from ai_chef import render_ai_chef
import json
from pathlib import Path
from urllib.parse import quote_plus
import streamlit as st


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
    }

    return aliases.get(name, name)


# ---------- Session state ----------

if "pantry" not in st.session_state:
    st.session_state.pantry = []

if "show_recipes" not in st.session_state:
    st.session_state.show_recipes = False

st.session_state.pantry = list(
    dict.fromkeys(
        normalize_ingredient(item)
        for item in st.session_state.pantry
        if item.strip()
    )
)


def add_ingredient(name):
    name = normalize_ingredient(name)

    if name and name not in st.session_state.pantry:
        st.session_state.pantry.append(name)


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


# ---------- Design and background animation ----------

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
    """
    <div class="hero">
        <h1>Whats in your kitchen today?</h1>
        <p>A little pantry inspiration for your next delicious meal.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
with st.expander("AI Chef — Create a recipe with your ingredients", expanded=True):
    render_ai_chef()

st.divider()


# ---------- Enter ingredients ----------

with st.form("ingredient_search", clear_on_submit=True):
    search_col, add_col = st.columns([4, 1])

    with search_col:
        ingredient_text = st.text_input(
            "Enter ingredients",
            placeholder="Try eggs, cheese, butter, salt...",
        )

    with add_col:
        st.write("")
        st.write("")
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
                add_ingredient(item)
            st.rerun()
        else:
            st.warning("Enter at least one ingredient.")


# ---------- Browse and search groceries ----------

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


# ---------- Selected pantry ----------

st.divider()
st.subheader("My pantry")

if st.session_state.pantry:
    st.caption("Click a selected ingredient to remove it.")
    columns = st.columns(3)

    for index, name in enumerate(st.session_state.pantry):
        with columns[index % 3]:
            if st.button(
                f"{name.title()}  ×",
                key=f"remove_{name}",
                use_container_width=True,
            ):
                st.session_state.pantry.remove(name)
                st.rerun()

    if st.button("Clear pantry", key="clear_pantry"):
        st.session_state.pantry = []
        st.rerun()
else:
    st.info("Your basket is waiting! Search above or pick a grocery.")


# ---------- Recipe filters ----------

st.subheader("What cuisine are you craving?")

selected_cuisine = st.selectbox(
    "Choose a cuisine",
    options=[
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
    options=[
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


# ---------- Load and validate recipes ----------

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
                    f"Check the ingredients, instructions, and minutes "
                    f"in recipe {position}."
                )
                st.stop()

        # ---------- Strict recipe matching ----------

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
                normalize_ingredient(ingredient)
                for ingredient in recipe["ingredients"]
            }

            if diet_preference != "All recipes":
                if required & meat_and_seafood:
                    continue

                # Generic kimchi may contain seafood.
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

        # ---------- Display recipe cards ----------

        if not matches:
            st.info(
                "No recipes can be made with only these ingredients yet. "
                "Check your pantry, cuisine, food preference, and time limit."
            )
        else:
            st.subheader("Here's what you could cook")

            st.caption(
                f"{len(matches)} matching recipes. "
                "Quickest recipes appear first."
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
                    st.write(f"**{percentage}% ingredient match**")

                    if match["missing"]:
                        st.write(
                            "**Suggested additions:** "
                            + ", ".join(match["missing"])
                        )
                       
                    
                    else:
                        st.success("You have all the listed ingredients!")
                    video_query = quote_plus(
                        f'{recipe["name"]} {recipe["cuisine"]} recipe'
                    )

                    
                    st.write(
                        "**Ingredients from your pantry:** "
                        + ", ".join(match["available"])
                    )

                    with st.expander("View cooking instructions"):
                        for number, step in enumerate(
                            recipe["instructions"],
                            start=1,
                        ):
                            st.write(f"{number}. {step}")
                           