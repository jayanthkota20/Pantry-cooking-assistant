import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from ai_chef import render_ai_chef


st.set_page_config(
    page_title="Pantry Cooking Assistant",
    page_icon="🥕",
    layout="wide",
)


# ---------- Ingredient names ----------

def normalize_ingredient(name):
    name = " ".join(name.strip().lower().split())

    aliases = {
        "egg": "eggs",
        "tomatoes": "tomato",
        "onions": "onion",
        "carrots": "carrot",
        "potatoes": "potato",
        "pea": "peas",
        "lemons": "lemon",
        "spring onions": "spring onion",
        "green onion": "spring onion",
        "green onions": "spring onion",
        "scallion": "spring onion",
        "scallions": "spring onion",
        "capsicum": "bell pepper",
        "bell peppers": "bell pepper",
        "curd": "yogurt",
        "yoghurt": "yogurt",
        "coriander leaves": "coriander",
        "cilantro": "coriander",
        "corn starch": "cornstarch",
        "egg plant": "eggplant",
        "brinjal": "eggplant",
        "american egg plant": "american eggplant",
        "chinese egg plant": "chinese eggplant",
        "muli": "radish",
        "mooli": "radish",
        "fenugreek leaves": "methi leaves",
        "blue berry": "blueberry",
        "blueberries": "blueberry",
        "strawberries": "strawberry",
        "sour bread": "sourdough bread",
        "wheat bread": "whole wheat bread",
        "shrimp": "prawns",
        "prawn": "prawns",
        "iol": "oil",
    }

    return aliases.get(name, name)


# ---------- Saved local pantry ----------

PANTRY_DB = Path(__file__).parent / "pantry.db"


def read_saved_pantry():
    with sqlite3.connect(PANTRY_DB) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pantry (
                name TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                added_on TEXT NOT NULL,
                remind_on TEXT NOT NULL
            )
            """
        )

        rows = connection.execute(
            """
            SELECT name, kind, added_on, remind_on
            FROM pantry
            ORDER BY name
            """
        ).fetchall()

    return {
        name: {
            "kind": kind,
            "added_on": added,
            "remind_on": reminder,
        }
        for name, kind, added, reminder in rows
    }


def save_pantry_item(name, kind, added_on, remind_on):
    with sqlite3.connect(PANTRY_DB) as connection:
        connection.execute(
            """
            INSERT INTO pantry (name, kind, added_on, remind_on)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                kind = excluded.kind,
                added_on = excluded.added_on,
                remind_on = excluded.remind_on
            """,
            (
                name,
                kind,
                added_on.isoformat(),
                remind_on.isoformat(),
            ),
        )


def remove_pantry_item(name):
    with sqlite3.connect(PANTRY_DB) as connection:
        connection.execute(
            "DELETE FROM pantry WHERE name = ?",
            (name,),
        )


def refresh_pantry():
    st.session_state.pantry_records = read_saved_pantry()

    # AI Chef and recipe matching still receive a list of names.
    st.session_state.pantry = list(
        st.session_state.pantry_records
    )


previous_pantry = list(st.session_state.get("pantry", []))
refresh_pantry()

# Preserve ingredients from an existing session during this upgrade.
if "pantry_migrated" not in st.session_state:
    for old_name in previous_pantry:
        name = normalize_ingredient(old_name)

        if name and name not in st.session_state.pantry_records:
            save_pantry_item(
                name,
                "Fresh",
                date.today(),
                date.today() + timedelta(days=7),
            )

    st.session_state.pantry_migrated = True
    refresh_pantry()

if "show_recipes" not in st.session_state:
    st.session_state.show_recipes = False


def add_ingredient(name, kind=None, added_on=None, remind_on=None):
    name = normalize_ingredient(name)

    # Clicking an existing ingredient does not reset its reminder.
    if not name or name in st.session_state.pantry_records:
        return

    kind = kind or st.session_state.get(
        "new_item_kind", "Fresh"
    )

    added_on = added_on or st.session_state.get(
        "new_item_added", date.today()
    )

    reminder_days = 10 if kind == "Dry goods" else 7

    remind_on = remind_on or (
        added_on + timedelta(days=reminder_days)
    )

    save_pantry_item(name, kind, added_on, remind_on)
    refresh_pantry()


# ---------- Reminder popup ----------

@st.dialog("Your pantry reminders")
def pantry_reminder_popup():
    st.caption(
        "These are reminder dates, not expiry dates "
        "or a food-safety assessment."
    )

    today = date.today()

    due = {
        name: record
        for name, record in st.session_state.pantry_records.items()
        if date.fromisoformat(record["remind_on"]) <= today
    }

    for name, record in due.items():
        st.write(
            f"**{name.title()}** — check this ingredient "
            "and consider using it."
        )

        st.caption(
            f"Added: {record['added_on']} • "
            f"Reminder: {record['remind_on']}"
        )

    if not due:
        st.success("No reminders are due.")

    if due and st.button(
        "Remind me tomorrow",
        key="snooze_reminders",
    ):
        for name, record in due.items():
            save_pantry_item(
                name,
                record["kind"],
                date.fromisoformat(record["added_on"]),
                today + timedelta(days=1),
            )

        refresh_pantry()
        st.rerun()

    if st.button("Close reminders", key="close_reminders"):
        st.rerun()


# ---------- Grocery shelf ----------

groceries = {
    "Vegetables": {
        "Tomato": "🍅",
        "Carrot": "🥕",
        "Baby carrots": "🥕",
        "Broccoli": "🥦",
        "Onion": "🧅",
        "White onion": "🧅",
        "Potato": "🥔",
        "Red potato": "🥔",
        "Spinach": "🥬",
        "Tindora": "🥒",
        "Okra": "🌿",
        "Chinese okra": "🌿",
        "Cucumber": "🥒",
        "Radish": "🥬",
        "Taro": "🥔",
        "Plantain": "🍌",
        "Methi leaves": "🌿",
        "Eggplant": "🍆",
        "American eggplant": "🍆",
        "Chinese eggplant": "🍆",
        "Cabbage": "🥬",
        "Red cabbage": "🥬",
        "Peas": "🫛",
        "Bell pepper": "🫑",
        "Spring onion": "🌱",
    },
    "Fruits": {
        "Apple": "🍎",
        "Banana": "🍌",
        "Lemon": "🍋",
        "Avocado": "🥑",
        "Pineapple": "🍍",
        "Watermelon": "🍉",
        "Muskmelon": "🍈",
        "Grapes": "🍇",
        "Strawberry": "🍓",
        "Blueberry": "🫐",
        "Pomegranate": "🍎",
        "Dragon fruit": "🌵",
        "Orange": "🍊",
        "Kiwi": "🥝",
    },
    "Pantry & dairy": {
        "Rice": "🍚",
        "Toor dal": "🫘",
        "Noodles": "🍜",
        "Bread": "🍞",
        "Whole wheat bread": "🍞",
        "Sourdough bread": "🍞",
        "Gluten-free bread": "🍞",
        "Eggs": "🥚",
        "Milk": "🥛",
        "Almond milk": "🥛",
        "Coconut milk": "🥥",
        "Low-fat milk": "🥛",
        "Cheese": "🧀",
        "Cream cheese": "🧀",
        "Beans": "🫘",
        "Red beans": "🫘",
        "Yogurt": "🥣",
        "Paneer": "🧀",
        "Butter": "🧈",
        "Cream": "🥛",
    },
    "Meat & seafood": {
        "Chicken": "🍗",
        "Lamb": "🥩",
        "Goat meat": "🥩",
        "Beef": "🥩",
        "Pork": "🥩",
        "Prawns": "🦐",
        "Crab": "🦀",
        "Fish": "🐟",
        "Salmon": "🐟",
        "Tuna": "🐟",
    },
    "Spices, herbs & sauces": {
        "Oil": "🫙",
        "Salt": "🧂",
        "Pepper": "🥄",
        "Ginger": "🫚",
        "Garlic": "🧄",
        "Cumin": "🌿",
        "Turmeric": "🥄",
        "Chili powder": "🌶️",
        "Garam masala": "🥄",
        "Biryani masala": "🥄",
        "Mint": "🌿",
        "Coriander": "🌿",
        "Curry leaves": "🌿",
        "Cornstarch": "🥣",
        "Rice flour": "🥣",
        "Soy sauce": "🫙",
        "Ketchup": "🍅",
        "Vinegar": "🫙",
        "Kimchi": "🥬",
        "Nori": "🌿",
    },
}


# ---------- Design and animation ----------

st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(circle at 5% 15%, #e1edcf 0%, transparent 35%),
        radial-gradient(circle at 95% 70%, #ffe2bf 0%, transparent 35%),
        #fffaf0;
    color: #263b29;
}

.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    position: relative;
    z-index: 1;
}

.grocery-border {
    text-align: center;
    font-size: clamp(24px, 4vw, 44px);
    letter-spacing: 12px;
    opacity: 0.65;
    margin-bottom: 24px;
}

.hero {
    text-align: center;
    padding: 20px 10px 30px;
}

.hero h1 {
    color: #285943;
    font-size: clamp(32px, 5vw, 54px);
}

.stApp .hero p {
    color: #826044;
    font-size: 19px;
}

.stApp h2,
.stApp h3 {
    color: #356b46;
}

.stApp [data-testid="stMarkdownContainer"] p {
    color: #344637;
}

.stApp [data-testid="stWidgetLabel"] p {
    color: #a64b20;
    font-weight: 600;
}

.stApp [data-testid="stCaptionContainer"] p {
    color: #76634f;
}

.stButton > button {
    border-radius: 16px;
    border: 1px solid #d9e2cc;
    background: #ffffff;
    color: #285943;
    min-height: 55px;
}

.stButton > button:hover {
    border-color: #6d945b;
    background: #edf5e6;
}

.stApp .stButton > button p {
    color: #285943;
}

.stButton > button[kind="primary"] {
    background: #315c3b;
    border: none;
}

.stApp .stButton > button[kind="primary"] p {
    color: #ffffff;
}

.floating-groceries {
    position: fixed;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
}

.floating-groceries span {
    position: absolute;
    bottom: -100px;
    font-size: clamp(30px, 4vw, 55px);
    opacity: 0;
    animation: grocery-float 22s linear infinite;
}

.floating-groceries span:nth-child(1) {
    left: 5%; animation-delay: -2s;
}
.floating-groceries span:nth-child(2) {
    left: 18%; animation-delay: -13s;
}
.floating-groceries span:nth-child(3) {
    left: 31%; animation-delay: -7s;
}
.floating-groceries span:nth-child(4) {
    left: 44%; animation-delay: -18s;
}
.floating-groceries span:nth-child(5) {
    left: 57%; animation-delay: -4s;
}
.floating-groceries span:nth-child(6) {
    left: 70%; animation-delay: -16s;
}
.floating-groceries span:nth-child(7) {
    left: 82%; animation-delay: -10s;
}
.floating-groceries span:nth-child(8) {
    left: 93%; animation-delay: -21s;
}

@keyframes grocery-float {
    0% {
        transform: translate(0, 0) rotate(-15deg);
        opacity: 0;
    }
    15% {
        opacity: 0.12;
    }
    50% {
        transform: translate(20px, -55vh) rotate(15deg);
        opacity: 0.12;
    }
    85% {
        opacity: 0.12;
    }
    100% {
        transform: translate(-10px, -120vh) rotate(-10deg);
        opacity: 0;
    }
}

@media (prefers-reduced-motion: reduce) {
    .floating-groceries {
        display: none;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="floating-groceries" aria-hidden="true">'
    '<span>🥕</span>'
    '<span>🍎</span>'
    '<span>🥦</span>'
    '<span>🍗</span>'
    '<span>🍅</span>'
    '<span>🐟</span>'
    '<span>🍋</span>'
    '<span>🦐</span>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="grocery-border">🥕 🍅 🥦 🍋 🧅 🥑 🍚 🥬</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero">'
    '<h1>What’s in your kitchen today?</h1>'
    '<p>A little pantry inspiration for your next delicious meal.</p>'
    '</div>',
    unsafe_allow_html=True,
)


# ---------- Show due reminders ----------

today = date.today()

due_items = {
    name: record
    for name, record in st.session_state.pantry_records.items()
    if date.fromisoformat(record["remind_on"]) <= today
}

if due_items:
    st.warning(
        "Pantry reminders due: "
        + ", ".join(name.title() for name in due_items)
    )

    open_reminders = st.button(
        "View pantry reminders",
        key="open_reminders",
    )

    if (
        open_reminders
        or st.session_state.get("reminders_shown_on")
        != today.isoformat()
    ):
        st.session_state.reminders_shown_on = today.isoformat()
        pantry_reminder_popup()


# ---------- AI Chef ----------

with st.expander(
    "AI Chef — Create a recipe with your ingredients",
    expanded=True,
):
    render_ai_chef()

st.divider()


# ---------- Add ingredients ----------

st.subheader("Add to your saved pantry")

st.caption(
    "Fresh: 7-day reminder • Dry goods: 10-day reminder. "
    "These are reminders, not expiry estimates."
)

kind_col, date_col = st.columns(2)

with kind_col:
    new_kind = st.selectbox(
        "Reminder category for new items",
        ["Fresh", "Dry goods"],
        key="new_item_kind",
    )

with date_col:
    added_date = st.date_input(
        "Date added",
        value=date.today(),
        max_value=date.today(),
        key="new_item_added",
    )

st.caption(
    "Grocery shelf clicks use the category and date selected above. "
    "Add fresh and dry ingredients separately."
)

with st.form("ingredient_search", clear_on_submit=True):
    ingredient_text = st.text_input(
        "Enter ingredients",
        placeholder="Try eggs, cheese, butter, salt...",
    )

    custom_reminder = st.date_input(
        "Reminder date for these ingredients",
        value=added_date + timedelta(
            days=10 if new_kind == "Dry goods" else 7
        ),
    )

    submitted = st.form_submit_button(
        "Add ingredients",
        use_container_width=True,
    )

    if submitted:
        entered_items = [
            item
            for item in ingredient_text.split(",")
            if item.strip()
        ]

        if entered_items:
            for item in entered_items:
                add_ingredient(
                    item,
                    new_kind,
                    added_date,
                    custom_reminder,
                )

            st.rerun()
        else:
            st.warning("Enter at least one ingredient.")


# ---------- Browse groceries ----------

st.subheader("Browse your grocery shelf")
st.caption("Click an ingredient to add it to your pantry.")

shelf_search = st.text_input(
    "Search the grocery shelf",
    placeholder="Try paneer, chicken, or tomato...",
    key="shelf_search",
)

search_term = normalize_ingredient(shelf_search)

if search_term:
    search_results = [
        (category, name, emoji)
        for category, items in groceries.items()
        for name, emoji in items.items()
        if (
            search_term in normalize_ingredient(name)
            or shelf_search.strip().lower() in name.lower()
        )
    ]

    if search_results:
        columns = st.columns(3)

        for index, (category, name, emoji) in enumerate(search_results):
            with columns[index % 3]:
                selected = (
                    normalize_ingredient(name)
                    in st.session_state.pantry
                )

                if st.button(
                    f"{emoji}  {name}" + ("  ✓" if selected else ""),
                    key=f"search_{category}_{name}",
                    use_container_width=True,
                ):
                    add_ingredient(name)
                    st.rerun()
    else:
        st.info(
            "No shelf items match. You can still enter "
            "the ingredient using the box above."
        )
else:
    tabs = st.tabs(list(groceries.keys()))

    for tab, (category, items) in zip(tabs, groceries.items()):
        with tab:
            columns = st.columns(3)

            for index, (name, emoji) in enumerate(items.items()):
                with columns[index % 3]:
                    selected = (
                        normalize_ingredient(name)
                        in st.session_state.pantry
                    )

                    if st.button(
                        f"{emoji}  {name}" + ("  ✓" if selected else ""),
                        key=f"grocery_{category}_{name}",
                        use_container_width=True,
                    ):
                        add_ingredient(name)
                        st.rerun()


# ---------- Manage saved pantry ----------

st.divider()
st.subheader("My saved pantry")

if st.session_state.pantry:
    for name, record in st.session_state.pantry_records.items():
        with st.expander(
            f"{name.title()} • Reminder: {record['remind_on']}"
        ):
            st.caption(
                f"{record['kind']} • Added: {record['added_on']}"
            )

            with st.form(f"edit_item_{name}"):
                edited_kind = st.selectbox(
                    "Category",
                    ["Fresh", "Dry goods"],
                    index=0 if record["kind"] == "Fresh" else 1,
                    key=f"kind_{name}",
                )

                edited_date = st.date_input(
                    "Reminder date",
                    value=date.fromisoformat(record["remind_on"]),
                    key=f"reminder_{name}",
                )

                if st.form_submit_button("Save reminder"):
                    save_pantry_item(
                        name,
                        edited_kind,
                        date.fromisoformat(record["added_on"]),
                        edited_date,
                    )

                    refresh_pantry()
                    st.rerun()

            if st.button(
                "Used up / remove",
                key=f"remove_{name}",
            ):
                remove_pantry_item(name)
                refresh_pantry()
                st.rerun()

    if st.checkbox(
        "I want to clear my saved pantry",
        key="confirm_clear_pantry",
    ):
        if st.button("Clear pantry", key="clear_pantry"):
            with sqlite3.connect(PANTRY_DB) as connection:
                connection.execute("DELETE FROM pantry")

            refresh_pantry()
            st.rerun()
else:
    st.info("Your basket is waiting! Search above or pick a grocery.")


# ---------- Recipe filters ----------

st.subheader("What cuisine are you craving?")

selected_cuisine = st.selectbox(
    "Choose a cuisine",
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
)

diet_preference = st.selectbox(
    "Food preference",
    [
        "All recipes",
        "Vegetarian (no meat, seafood, or eggs)",
        "Vegetarian + eggs",
    ],
)

max_minutes = st.slider(
    "How much time do you have?",
    min_value=10,
    max_value=120,
    value=120,
    step=5,
    format="%d minutes",
)

st.caption(
    "Find recipes using your main ingredients, "
    "with suggested additions to complete each dish."
)

if st.button(
    "What can I cook today?",
    type="primary",
    use_container_width=True,
):
    st.session_state.show_recipes = True


# ---------- Load saved recipes ----------

if st.session_state.show_recipes:
    if not st.session_state.pantry:
        st.warning("Add at least one ingredient to get started.")
    else:
        recipe_path = Path(__file__).parent / "recipes.json"

        try:
            with recipe_path.open(encoding="utf-8") as file:
                recipes = json.load(file)
        except FileNotFoundError:
            st.error("Place recipes.json in the same folder as app.py.")
            st.stop()
        except json.JSONDecodeError as error:
            st.error(
                f"Check recipes.json near line {error.lineno}. "
                "There may be a missing comma or bracket."
            )
            st.stop()

        required_fields = {
            "id",
            "name",
            "cuisine",
            "minutes",
            "servings",
            "ingredients",
            "instructions",
        }

        if not isinstance(recipes, list):
            st.error("recipes.json must contain a list of recipes.")
            st.stop()

        for position, recipe in enumerate(recipes, start=1):
            if (
                not isinstance(recipe, dict)
                or not required_fields.issubset(recipe)
            ):
                st.error(
                    f"Recipe {position} is missing required fields."
                )
                st.stop()

            if (
                not isinstance(recipe["ingredients"], list)
                or not recipe["ingredients"]
                or not all(
                    isinstance(item, str) and item.strip()
                    for item in recipe["ingredients"]
                )
                or not isinstance(recipe["instructions"], list)
                or not all(
                    isinstance(step, str)
                    for step in recipe["instructions"]
                )
                or not isinstance(recipe["minutes"], (int, float))
            ):
                st.error(
                    f"Check the ingredients, instructions, "
                    f"and minutes in recipe {position}."
                )
                st.stop()


        # ---------- Match recipes ----------

        pantry = {
            normalize_ingredient(item)
            for item in st.session_state.pantry
        }

        meat_and_seafood = {
            "chicken",
            "lamb",
            "goat meat",
            "beef",
            "pork",
            "prawns",
            "crab",
            "fish",
            "salmon",
            "tuna",
            "fish sauce",
            "shrimp paste",
            "chicken stock",
        }

        matches = []

        for recipe in recipes:
            if recipe["minutes"] > max_minutes:
                continue

            if (
                selected_cuisine != "Any cuisine"
                and recipe["cuisine"] != selected_cuisine
            ):
                continue

            required = {
                normalize_ingredient(item)
                for item in recipe["ingredients"]
            }

            if diet_preference != "All recipes":
                if required & meat_and_seafood:
                    continue

                if "kimchi" in required:
                    continue

                if (
                    diet_preference
                    == "Vegetarian (no meat, seafood, or eggs)"
                    and "eggs" in required
                ):
                    continue

            available = required & pantry
            missing = required - pantry

            main_ingredients = {
                normalize_ingredient(item)
                for item in recipe.get(
                    "main_ingredients",
                    recipe["ingredients"][:1],
                )
            }

            if main_ingredients.issubset(pantry):
                matches.append({
                    "recipe": recipe,
                    "available": sorted(available),
                    "missing": sorted(missing),
                    "score": len(available) / len(required),
                })

        matches.sort(
            key=lambda match: (
                -match["score"],
                len(match["missing"]),
                match["recipe"]["minutes"],
            )
        )


        # ---------- Recipe cards ----------

        if not matches:
            st.info(
                "No matching saved recipes found yet. "
                "Check your pantry, cuisine, food preference, "
                "and time limit."
            )
        else:
            st.subheader("Here's what you could cook")

            st.caption(
                f"{len(matches)} matching recipes. "
                "Best ingredient matches appear first, "
                "then cooking time."
            )

            for match in matches:
                recipe = match["recipe"]

                with st.container(border=True):
                    st.subheader(recipe["name"])

                    st.caption(
                        f'{recipe["cuisine"]} • '
                        f'{recipe["minutes"]} minutes • '
                        f'Serves {recipe["servings"]}'
                    )

                    percentage = round(match["score"] * 100)

                    st.write(
                        f"**{percentage}% ingredient match**"
                    )

                    st.write(
                        "**Ingredients from your pantry:** "
                        + ", ".join(match["available"])
                    )

                    if match["missing"]:
                        st.write(
                            "**Suggested additions:** "
                            + ", ".join(match["missing"])
                        )
                    else:
                        st.success(
                            "You have all the listed ingredients!"
                        )

                    with st.expander("View cooking instructions"):
                        for number, step in enumerate(
                            recipe["instructions"],
                            start=1,
                        ):
                            st.write(f"{number}. {step}")
        st.markdown(
    """
        <style>
/* Dropdown options */
[role="listbox"] [role="option"],
[role="listbox"] [role="option"] *,
[data-baseweb="menu"] li,
[data-baseweb="menu"] li * {
    color: #a64b20 !important;
    -webkit-text-fill-color: #a64b20 !important;
}

/* Calendar — current and older Streamlit versions */
[data-testid="stDateInputCalendar"],
[data-baseweb="calendar"] {
    background-color: #fffaf0 !important;
}

[data-testid="stDateInputCalendar"],
[data-testid="stDateInputCalendar"] *,
[data-baseweb="calendar"],
[data-baseweb="calendar"] * {
    color: #263b29 !important;
    -webkit-text-fill-color: #263b29 !important;
}

/* Selected date */
[data-testid="stDateInputCalendar"] [data-selected="true"],
[data-testid="stDateInputCalendar"] [data-selected="true"] *,
[data-testid="stDateInputCalendar"] [aria-selected="true"],
[data-testid="stDateInputCalendar"] [aria-selected="true"] *,
[data-baseweb="calendar"] [aria-selected="true"],
[data-baseweb="calendar"] [aria-selected="true"] * {
    background-color: #315c3b !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
</style>
""",
    unsafe_allow_html=True,
)