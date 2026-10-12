from urllib.parse import quote_plus

import requests
import streamlit as st


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"


def generate_recipe(question, pantry, cuisine, preference, minutes):
    system_prompt = """
You are a practical cooking assistant.
Create one recipe that answers the user's actual request.

RECIPE RULES:
- If the user requests noodles, include noodles in the ingredients and steps.
  Do not replace the requested dish with rice or another dish.
- Only classify ingredients as available when explicitly listed in the
  selected pantry or explicitly described by the user as ingredients they have.
- A dish name such as "chicken noodles" does not confirm pantry ownership.
- Put every other ingredient under suggested additions, including oil,
  salt, sauces, and spices.
- Clearly separate essential additions from optional additions.
- Respect the cuisine and food preference.
- Do not include meat or seafood for vegetarian preferences.
- Exclude eggs for the vegetarian option that prohibits eggs.
- Keep preparation plus cooking within the user's time limit.
- If this is not realistically possible, explain the limitation.
- State assumptions such as thawed chicken or already-cooked rice.
- Give concrete quantities and a clear number of servings.
- Never instruct the user to rinse raw chicken.
- For chicken, use an internal temperature of 165°F (74°C).
- Do not determine food safety from pantry reminder dates.
- Explain important steps with heat levels, timings, and visual cues.
- Use clear, natural English suitable for a beginner.
- Do not repeat these instructions or placeholder wording in the answer.

FORMATTING:
Start with a Markdown heading containing only the real dish name.
For example: ## Chicken Noodles
Write your own brief description below it.
Leave blank lines between headings, paragraphs, and sections.
Use bold labels for Cuisine, Total time, and Servings.
Use these sections, each only once:
### Available ingredients
### Suggested additions
### Cooking steps
### Estimated nutrition per serving
### Useful tip

Use numbered cooking steps.
For nutrition, estimate calories (kcal), protein (g),
carbohydrates (g), and fat (g) per serving.
Include essential suggested additions in the estimate.
Clearly label nutrition as approximate AI estimates,
not verified calculations.
If you cannot reasonably estimate nutrition, say it is unavailable.
Do not provide YouTube links; the app creates those separately.
"""

    user_prompt = f"""
Selected pantry: {", ".join(pantry) if pantry else "No ingredients confirmed"}
Cuisine preference: {cuisine}
Food preference: {preference}
Maximum preparation plus cooking time: {minutes} minutes
User request: {question}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 1800,
            },
        },
        timeout=(10, 240),
    )

    response.raise_for_status()
    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("Unexpected response format.")

    message = data.get("message")

    if not isinstance(message, dict):
        raise ValueError("The response did not contain a message.")

    answer = message.get("content", "")

    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("The model returned an empty recipe.")

    return answer.strip()


def get_recipe_name(answer):
    for line in answer.splitlines():
        heading = line.strip()

        if heading.startswith("#"):
            name = heading.lstrip("#").strip().replace("**", "")
            if name:
                return name

    return ""


def render_ai_chef():
    st.subheader("Your personal AI Chef")
    st.caption("Turn what's in your kitchen into your next meal.")

    # Only change the typed text and cursor in the AI request box.
    st.markdown(
        """
<style>
.st-key-ai_request textarea,
.st-key-ai_request textarea:focus {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: #ffffff !important;
}
</style>
""",
        unsafe_allow_html=True,
    )

    pantry = list(st.session_state.get("pantry", []))

    with st.container(border=True):
        if pantry:
            st.write("**Your current pantry**")
            st.write(", ".join(item.title() for item in pantry))
        else:
            st.info(
                "Add ingredients to your pantry, "
                "or describe what you have in your request."
            )

        with st.form("ai_chef_form"):
            question = st.text_area(
                "What would you like to cook?",
                placeholder=(
                    "I have chicken, noodles, and spinach. "
                    "Suggest something spicy with minimal additions."
                ),
                height=130,
                key="ai_request",
            )

            use_pantry = st.checkbox(
                "Use my selected pantry ingredients",
                value=True,
                key="ai_use_pantry",
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
                "Maximum total cooking time",
                min_value=10,
                max_value=120,
                value=30,
                step=5,
                format="%d minutes",
                key="ai_minutes",
            )

            submitted = st.form_submit_button(
                "Create my recipe",
                type="primary",
                use_container_width=True,
            )

    if submitted:
        selected_pantry = pantry if use_pantry else []

        if not question.strip() and not selected_pantry:
            st.warning(
                "Enter a request or add ingredients to your pantry."
            )
        else:
            request_text = (
                question.strip()
                or "Suggest a meal using my pantry ingredients."
            )

            try:
                with st.spinner("Your AI Chef is preparing a recipe..."):
                    answer = generate_recipe(
                        request_text,
                        selected_pantry,
                        cuisine,
                        preference,
                        minutes,
                    )

                st.session_state.ai_recipe = answer
                st.session_state.ai_recipe_context = {
                    "pantry": selected_pantry,
                    "request": request_text,
                    "cuisine": cuisine,
                    "preference": preference,
                    "minutes": minutes,
                }

            except requests.exceptions.Timeout:
                st.error(
                    "The model took too long. Please try again."
                )

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to Ollama. Open the Ollama app "
                    "or run 'ollama serve' in a separate terminal."
                )

            except requests.exceptions.HTTPError as error:
                st.error(
                    f"Ollama returned an error: {error}. "
                    "Check that qwen2.5:3b is installed."
                )

            except (ValueError, requests.exceptions.RequestException):
                st.error(
                    "Could not read the model's response. Please try again."
                )

    if st.session_state.get("ai_recipe"):
        st.divider()

        with st.container(border=True):
            st.caption(
                "AI-generated suggestion • Based on your last submitted "
                "request. Nutrition values are approximate AI estimates."
            )

            answer = st.session_state.ai_recipe

            # Render headings, bold labels, and lists properly.
            st.markdown(answer)

            # Exactly one YouTube button.
            recipe_name = get_recipe_name(answer)

            if recipe_name:
                youtube_query = quote_plus(f"{recipe_name} recipe")

                st.link_button(
                    "Watch on YouTube",
                    "https://www.youtube.com/results?search_query="
                    + youtube_query,
                    use_container_width=True,
                )

                st.caption(
                    "YouTube results may use different ingredients or methods."
                )

            with st.expander("Details of this suggestion"):
                context = st.session_state.get(
                    "ai_recipe_context", {}
                )

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

            st.download_button(
                "Download recipe",
                data=answer,
                file_name="my_ai_recipe.md",
                mime="text/markdown",
                key="download_ai_recipe",
            )