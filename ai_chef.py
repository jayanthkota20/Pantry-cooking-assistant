import json
import re
import time
from datetime import date
from urllib.parse import quote_plus

import requests
import streamlit as st

from favorites import render_save_favorite
from shopping import add_shopping_items


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b"


SYSTEM_PROMPT = """
You are a practical cooking teacher for a first-time cook.
Write one complete recipe in clear English.

REQUEST:
- Make the requested dish even when its ingredients are not in the pantry.
- The pantry is optional inspiration, not a restriction.
- Missing meat is not a reason to create a vegetarian replacement.
- An empty pantry does not imply vegetarian.
- If no dish is named, suggest a meal using compatible pantry ingredients.
- Use reminder priorities only when compatible with the requested dish.
- Reminder dates do not establish expiration or food safety.
- Do not claim the user owns ingredients merely because they are requested.
- Chicken noodles, egg noodles and veg noodles mean stir-fried noodles
  unless the user explicitly asks for soup or another specific style.
- Do not silently turn noodles into soup or rice.

PREFERENCES:
- Respect explicit dietary restrictions.
- All recipes permits meat, seafood, eggs and vegetarian recipes.
- Vegetarian excludes meat, seafood, animal broth, fish sauce and gelatin.
- Exclude eggs when the preference prohibits eggs.
- Explain a conflict instead of silently changing the dish.
- Do not silently substitute allergens.
- Follow the selected cuisine when compatible; label adaptations honestly.

INGREDIENTS:
- Give one complete Recipe ingredients list.
- Do not create Available ingredients or Suggested additions sections.
- List every ingredient once using ingredient name: quantity and preparation.
- Include oil, water, sauces, salt and spices used in the steps.
- Combine repeated ingredients into one total quantity.
- Explain divided use in the cooking steps.
- Specify raw meat weight, cut, and bone-in or boneless consistently.
- Specify dried, fresh or already-cooked noodles and rice.
- Chicken noodles must contain measured quantities of chicken and noodles.
- Cilantro and fresh coriander leaves are the same herb; list them once.
- Coriander seeds, powder and leaves are different forms.
- Mark optional garnishes clearly.
- Ingredients required in the steps must not be optional.

BEGINNER INSTRUCTIONS:
- Explain preparation, chopping sizes and any marinating time.
- List equipment.
- Explain exactly when and how to add and cook the main ingredient.
- Give heat levels, approximate timings and signs of progress.
- Explain covered or uncovered cooking, stirring and adding liquid.
- Explain how to check doneness and tenderness.
- For curry, explain how to correct a thick or watery sauce.
- Include the meat-cooking stage.
- Prefer an ordinary stovetop pot unless equipment is specified.
- Never promise tender mutton after only a few minutes.
- Explain that mutton cooking time varies with cut, size and equipment.
- Do not invent pressure-cooker settings or rely on whistle counts.
- Prepare noodles according to their package instructions.
- Never instruct users to rinse raw chicken.
- For chicken, include an internal temperature of 165°F (74°C).
- Do not use meat color alone to establish safe cooking.
- Include preparation and cooking in total time.
- If the selected limit is unrealistic, explain the longer time needed.
- Give detailed instructions without repeating entire stages.

CLASSIFICATION:
- Classify the actual dish, including essential sauces and broth.
- Food type: Vegetarian, Contains eggs, Non-vegetarian or Not checked.
- Meat, seafood, animal broth, fish sauce or gelatin means Non-vegetarian.
- Eggs without non-vegetarian ingredients means Contains eggs.
- Vegetarian permits dairy but excludes eggs and non-vegetarian ingredients.
- Never describe a meat recipe as vegetarian-friendly.
- Do not claim gluten-free status is verified.
- Cuisine: Indian, Chinese, Italian, Korean, Japanese, Thai,
  American, Mexican, Other / mixed or Not specified.

NUTRITION:
- Choose and list reasonable ingredient quantities and numeric servings.
- Estimate nutrition from those quantities.
- Specify raw versus cooked weights.
- For bone-in meat, state the assumed edible portion.
- Include oils, sauces and required ingredients.
- Divide recipe totals by the number of servings.
- Exclude optional garnishes and unlisted accompaniments.
- Give rounded numeric estimates for calories, protein,
  carbohydrates and fat, with kcal or g.
- State important assumptions.
- Do not claim quantities are missing when you supplied them.
- If an estimate is not reasonably possible, explain why.
- Never invent verified nutrition data or output placeholders.
- Label values approximate AI estimates per serving.

OUTPUT:
Start with ## followed by only the dish name.
Write a short description on a separate line.
Then write each label with its value in a separate paragraph:
**Cuisine:**
**Food type:**
**Total time:**
**Servings:**

Use these sections once, in order:
### Recipe ingredients
### Equipment
### Cooking steps
### Estimated nutrition per serving
### Useful tip

Use ingredient bullets and numbered cooking steps.
Do not provide YouTube links; the app creates its own.
Do not repeat these instructions.
"""


class RecipeError(ValueError):
    pass


SECTION_NAMES = {
    "ingredients",
    "recipe ingredients",
    "equipment",
    "instructions",
    "cooking steps",
    "estimated nutrition per serving",
    "nutrition",
    "useful tip",
    "method",
    "directions",
    "description",
}


def clean_line(line):
    line = line.strip().replace("**", "").replace("__", "")
    line = re.sub(r"^#{1,6}\s*", "", line)
    return line.strip()


def get_recipe_name(answer, request=""):
    lines = [
        line.strip()
        for line in answer.splitlines()
        if line.strip()
    ]

    # Look for an explicit label or Markdown title first.
    for line in lines[:15]:
        text = clean_line(line)

        match = re.match(
            r"^(?:recipe name|recipe title|dish name)\s*:\s*(.+)$",
            text,
            re.I,
        )

        if match:
            return match.group(1).strip()

        if (
            re.match(r"^#{1,2}\s+", line)
            and text.casefold().rstrip(":") not in SECTION_NAMES
            and ":" not in text
        ):
            return text

    # Also accept a short plain or bold title near the beginning.
    for line in lines[:3]:
        text = clean_line(line)

        if text.casefold().startswith(
            ("sure", "here is", "here's", "certainly")
        ):
            continue

        if (
            len(text.split()) <= 10
            and len(text) <= 80
            and text.casefold().rstrip(":") not in SECTION_NAMES
            and not re.search(r"[:.!?]", text)
            and not re.match(r"^[-*•\d]", text)
        ):
            return text

        break

    if request.strip():
        return "Recipe: " + request.strip().splitlines()[0][:100]

    return "My cooking recipe"


def ensure_recipe_title(answer, request="", preferred_name=""):
    name = preferred_name or get_recipe_name(answer, request)
    lines = answer.strip().splitlines()

    first = next(
        (index for index, line in enumerate(lines) if line.strip()),
        None,
    )

    if first is not None:
        text = clean_line(lines[first])

        labeled = re.match(
            r"^(?:recipe name|recipe title|dish name)\s*:\s*(.+)$",
            text,
            re.I,
        )

        if (
            text == name
            or (
                labeled
                and labeled.group(1).strip() == name
            )
        ):
            lines.pop(first)

    body = "\n".join(lines).strip()
    return name, f"## {name}\n\n{body}"


def recipe_sections(answer):
    aliases = {
        "ingredients": "recipe ingredients",
        "instructions": "cooking steps",
        "method": "cooking steps",
        "directions": "cooking steps",
        "nutrition": "estimated nutrition per serving",
        "nutrition per serving": "estimated nutrition per serving",
        "tip": "useful tip",
    }

    known = {
        "recipe ingredients",
        "equipment",
        "cooking steps",
        "estimated nutrition per serving",
        "useful tip",
    }

    sections = {}
    current = None

    for line in answer.splitlines():
        title = clean_line(line).rstrip(":").casefold()
        title = aliases.get(title, title)

        if title in known:
            current = title
            sections.setdefault(current, [])
        elif re.match(r"^#{1,3}\s+", line.strip()):
            current = None
        elif current:
            sections[current].append(line)

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
    }


def normalize_labels(answer):
    aliases = {
        "cuisine": "Cuisine",
        "food type": "Food type",
        "diet type": "Food type",
        "total time": "Total time",
        "total cooking time": "Total time",
        "servings": "Servings",
        "serves": "Servings",
    }

    result = []

    for line in answer.splitlines():
        cleaned = clean_line(line)

        match = re.match(
            r"^([^:：]+)\s*[:：]\s*(.+)$",
            cleaned,
        )

        if match:
            name = aliases.get(
                match.group(1).strip().casefold()
            )

            if name:
                result.extend([
                    f"**{name}:** {match.group(2).strip()}",
                    "",
                ])
                continue

        result.append(line)

    return "\n".join(result).strip()


def shopping_draft(answer):
    ingredients = recipe_sections(answer).get(
        "recipe ingredients",
        "",
    )

    items = []

    for line in ingredients.splitlines():
        match = re.match(r"^\s*[-*+•]\s+(.+)", line)

        if match:
            item = match.group(1).replace("**", "").strip()

            if item:
                items.append(item)

    return "\n".join(dict.fromkeys(items))


def due_pantry_items(pantry):
    records = st.session_state.get("pantry_records", {})

    if not isinstance(records, dict):
        return []

    selected = {
        str(item).casefold()
        for item in pantry
    }

    due = []

    for name, record in records.items():
        if str(name).casefold() not in selected:
            continue

        if not isinstance(record, dict):
            continue

        try:
            reminder = date.fromisoformat(
                str(record.get("remind_on", ""))
            )
        except ValueError:
            continue

        if reminder <= date.today():
            due.append((reminder, str(name)))

    return [
        name
        for _, name in sorted(due)
    ]


def build_messages(
    question,
    pantry,
    cuisine,
    preference,
    minutes,
    priority,
):
    user_prompt = f"""
Request: {question}
Pantry reference: {", ".join(pantry) or "None confirmed"}
Cuisine preference: {cuisine}
Food preference: {preference}
Preferred preparation plus cooking time: {minutes} minutes
Compatible reminder priorities: {", ".join(priority) or "None"}

Give the requested dish even if ingredients need to be purchased.
Start with the recipe name as a Markdown heading.
Provide one ingredient list and detailed beginner instructions.
Explain if the requested time is unrealistic.
"""

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]


def stream_recipe(messages, on_update):
    parts = []
    completed = False
    last_update = 0.0

    with requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": True,
            "keep_alive": "30m",
            "options": {
                "temperature": 0.6,
                "repeat_last_n": 128,
                "repeat_penalty": 1.1,
                "num_predict": 2400,
            },
        },
        stream=True,
        timeout=(10, 300),
    ) as response:
        if not response.ok:
            try:
                payload = response.json()

                details = (
                    payload.get("error", response.text)
                    if isinstance(payload, dict)
                    else response.text
                )
            except ValueError:
                details = response.text

            raise RecipeError(
                f"Ollama HTTP {response.status_code}: {details}"
            )

        for raw in response.iter_lines(chunk_size=1):
            if not raw:
                continue

            event = json.loads(raw)

            if not isinstance(event, dict):
                raise RecipeError(
                    "Ollama returned an invalid stream event."
                )

            if event.get("error"):
                raise RecipeError(str(event["error"]))

            message = event.get("message", {})

            if not isinstance(message, dict):
                raise RecipeError(
                    "Ollama returned an invalid message."
                )

            chunk = message.get("content", "")

            if not isinstance(chunk, str):
                raise RecipeError(
                    "Ollama returned invalid recipe text."
                )

            if chunk:
                parts.append(chunk)
                now = time.monotonic()

                if now - last_update >= 0.15:
                    on_update("".join(parts))
                    last_update = now

            if event.get("done"):
                if event.get("done_reason") == "length":
                    raise RecipeError(
                        "The response reached its length limit. "
                        "The unfinished recipe was not saved."
                    )

                completed = True
                break

    if not completed:
        raise RecipeError(
            "The connection ended before the recipe finished. "
            "The unfinished recipe was not saved."
        )

    answer = "".join(parts).strip()

    if not answer:
        raise RecipeError("Ollama returned an empty recipe.")

    on_update(answer)
    return answer


def render_recipe_tools(answer, context):
    recipe_name = (
        context.get("recipe_name")
        or get_recipe_name(
            answer,
            context.get("request", ""),
        )
    )

    st.download_button(
        "Download recipe",
        data=answer,
        file_name="my_ai_recipe.md",
        mime="text/markdown",
        key="download_ai_recipe",
    )

    render_save_favorite(
        answer,
        recipe_name,
        context,
    )

    st.link_button(
        "Find cooking videos on YouTube",
        "https://www.youtube.com/results?search_query="
        + quote_plus(f"{recipe_name} recipe"),
        use_container_width=True,
    )

    st.caption(
        "YouTube results may use different ingredients or methods."
    )

    with st.expander(
        "Build a shopping list from this recipe"
    ):
        st.caption(
            "This draft includes all recipe ingredients. "
            "Remove items you already have and optional "
            "extras you do not want."
        )

        if "shopping_recipe_draft" not in st.session_state:
            st.session_state.shopping_recipe_draft = (
                shopping_draft(answer)
            )

        draft = st.text_area(
            "Shopping items, one per line",
            key="shopping_recipe_draft",
            height=160,
        )

        if st.button(
            "Add to shopping list",
            key="recipe_to_shopping",
        ):
            if draft.strip():
                added = add_shopping_items(
                    draft.splitlines()
                )

                st.success(
                    f"Added {added} new items. "
                    "Open Shopping List to view them."
                )
            else:
                st.info(
                    "Enter the ingredients you want to buy."
                )

    with st.expander("Details of this suggestion"):
        st.write("**Recipe name:** " + recipe_name)

        st.write(
            "**Selected pantry:** "
            + (
                ", ".join(context.get("pantry", []))
                or "No pantry ingredients selected."
            )
        )

        st.write(
            "**Request:** "
            + context.get("request", "Not recorded.")
        )

        st.write(
            "**Cuisine:** "
            + context.get("cuisine", "Any cuisine")
        )

        st.write(
            "**Food preference:** "
            + context.get("preference", "All recipes")
        )

        st.write(
            "**Requested time limit:** "
            + str(context.get("minutes", "Not recorded"))
            + " minutes"
        )

        if context.get("priority"):
            st.write(
                "**Reminder priorities:** "
                + ", ".join(context["priority"])
            )

        if context.get("generation_seconds") is not None:
            seconds = context["generation_seconds"]

            st.caption(
                f"Generated in {seconds:.0f} seconds "
                f"using {context.get('model', MODEL)}."
            )


def render_ai_chef():
    st.subheader("What would you like to cook?")
    st.caption(
        "Search any dish, or get inspiration from your pantry."
    )

    pantry = [
        str(item)
        for item in st.session_state.get("pantry", [])
    ]

    due_items = due_pantry_items(pantry)

    with st.container(border=True):
        if pantry:
            with st.expander(
                f"Your pantry · {len(pantry)} ingredients"
            ):
                st.write(
                    ", ".join(item.title() for item in pantry)
                )
        else:
            st.info(
                "Search any recipe with an empty pantry "
                "and buy its ingredients later."
            )

        with st.form("ai_chef_form"):
            question = st.text_area(
                "Describe your meal",
                placeholder=(
                    "Indian-style chicken stir-fried noodles "
                    "for 2 people. Explain each step for a beginner."
                ),
                height=130,
                key="ai_request",
            )

            use_pantry = st.checkbox(
                "Use my pantry as a reference",
                value=True,
                key="ai_use_pantry",
            )

            prioritize_due = st.checkbox(
                "Use these first — ingredients with due reminders",
                value=bool(due_items),
                disabled=not bool(due_items),
                key="ai_prioritize_due",
            )

            if due_items:
                st.caption(
                    "Reminder ingredients: "
                    + ", ".join(due_items)
                    + ". Used only when compatible with your dish."
                )

            left, right = st.columns(2)

            with left:
                cuisine = st.selectbox(
                    "Cuisine inspiration",
                    [
                        "Any cuisine",
                        "Indian",
                        "Korean",
                        "Japanese",
                        "Chinese",
                        "Thai",
                        "American",
                        "Italian",
                        "Mexican",
                    ],
                    key="ai_cuisine",
                )

            with right:
                preference = st.selectbox(
                    "Food preference",
                    [
                        "All recipes",
                        "Vegetarian (no meat, seafood, or eggs)",
                        "Vegetarian + eggs",
                    ],
                    key="ai_food_preference",
                )

            minutes = st.slider(
                "Preferred maximum total cooking time",
                min_value=10,
                max_value=120,
                value=30,
                step=5,
                format="%d minutes",
                key="ai_minutes",
            )

            st.caption(
                "The recipe appears as it is written. "
                "Initial model loading may take a moment."
            )

            submitted = st.form_submit_button(
                "Create my recipe",
                type="primary",
                use_container_width=True,
            )

    output = st.empty()

    if submitted:
        selected_pantry = pantry if use_pantry else []

        selected_priority = (
            due_items
            if use_pantry and prioritize_due
            else []
        )

        if not question.strip() and not selected_pantry:
            st.warning(
                "Enter a dish or select pantry ingredients."
            )
        else:
            request_text = (
                question.strip()
                or "Suggest a meal using my pantry ingredients."
            )

            for key in (
                "ai_recipe",
                "ai_recipe_context",
                "ai_debug_response",
                "ai_debug_problems",
            ):
                st.session_state.pop(key, None)

            try:
                with output.container():
                    status = st.empty()
                    preview = st.empty()

                    status.info(
                        "Starting AI Chef… "
                        "The recipe will appear below."
                    )

                    def show_update(text):
                        status.caption(
                            "Writing your recipe… "
                            "Please wait for completion."
                        )
                        preview.markdown(text + " ▌")

                    started = time.monotonic()

                    messages = build_messages(
                        request_text,
                        selected_pantry,
                        cuisine,
                        preference,
                        minutes,
                        selected_priority,
                    )

                    answer = stream_recipe(
                        messages,
                        show_update,
                    )

                    answer = normalize_labels(answer)

                    recipe_name, answer = ensure_recipe_title(
                        answer,
                        request_text,
                    )

                    st.session_state.ai_recipe = answer

                    st.session_state.ai_recipe_context = {
                        "recipe_name": recipe_name,
                        "pantry": selected_pantry,
                        "request": request_text,
                        "cuisine": cuisine,
                        "preference": preference,
                        "minutes": minutes,
                        "priority": selected_priority,
                        "model": MODEL,
                        "generation_seconds": (
                            time.monotonic() - started
                        ),
                    }

                    st.session_state.shopping_recipe_draft = (
                        shopping_draft(answer)
                    )

            except requests.exceptions.Timeout:
                output.empty()

                st.error(
                    "Ollama took too long to respond. "
                    "The unfinished recipe was not saved."
                )

            except requests.exceptions.ConnectionError:
                output.empty()

                st.error(
                    "The connection to Ollama failed or was interrupted. "
                    "Keep the Ollama server running and try again."
                )

            except RecipeError as error:
                output.empty()
                st.error(str(error))

            except (
                ValueError,
                requests.exceptions.RequestException,
            ):
                output.empty()

                st.error(
                    "Could not complete the streamed response. "
                    "The unfinished recipe was not saved. "
                    "Please try again."
                )

    answer = st.session_state.get("ai_recipe")

    if not answer:
        return

    context = st.session_state.get(
        "ai_recipe_context",
        {},
    )

    # Also add a heading to an answer already in this session.
    recipe_name, answer = ensure_recipe_title(
        answer,
        context.get("request", ""),
        context.get("recipe_name", ""),
    )

    context["recipe_name"] = recipe_name
    st.session_state.ai_recipe = answer
    st.session_state.ai_recipe_context = context

    with output.container():
        st.divider()

        with st.container(border=True):
            st.caption(
                "AI-generated recipe · Review before cooking. "
                "Nutrition values are approximate AI estimates."
            )

            st.markdown(answer)

            render_recipe_tools(
                answer,
                context,
            )