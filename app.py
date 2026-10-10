import json
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="Pantry Cooking Assistant",
    page_icon="🥕",
    layout="wide",
)

# Remember selected ingredients when Streamlit refreshes.
if "pantry" not in st.session_state:
    st.session_state.pantry = []

groceries = {
    "Vegetables": {
        "Tomato": "🍅",
        "Carrot": "🥕",
        "Broccoli": "🥦",
        "Onion": "🧅",
        "Potato": "🥔",
        "Spinach": "🥬",
    },
    "Fruits": {
        "Apple": "🍎",
        "Banana": "🍌",
        "Lemon": "🍋",
        "Avocado": "🥑",
    },
    "Pantry & dairy": {
        "Rice": "🍚",
        "Bread": "🍞",
        "Eggs": "🥚",
        "Milk": "🥛",
        "Cheese": "🧀",
        "Beans": "🫘",
    },
}
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
    }

    return aliases.get(name, name)

def add_ingredient(name):
    name = normalize_ingredient(name)

    if name and name not in st.session_state.pantry:
        st.session_state.pantry.append(name)

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
        color: #284b32;
        font-size: clamp(32px, 5vw, 54px);
    }

    .hero p {
        color: #65735c;
        font-size: 19px;
    }

    .stButton > button {
        border-radius: 16px;
        border: 1px solid #d9e2cc;
        background: #ffffff;
        color: #284b32;
        min-height: 55px;
    }

    .stButton > button:hover {
        border-color: #6d945b;
        background: #edf5e6;
        color: #284b32;
    }

    .stButton > button[kind="primary"] {
        background: #315c3b;
        color: white;
        border: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="grocery-border">🥕 🍅 🥦 🍋 🧅 🥑 🍚 🥬</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>What’s in your kitchen today?</h1>
        <p>A little pantry inspiration for your next delicious meal.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# A form clears the search field after an ingredient is added.
with st.form("ingredient_search", clear_on_submit=True):
    search_col, add_col = st.columns([4, 1])

    with search_col:
        ingredient = st.text_input(
            "Search or enter an ingredient",
            placeholder="Try tomato, rice, or something in your pantry...",
        )

    with add_col:
        st.write("")
        st.write("")
        submitted = st.form_submit_button(
            "Add ingredient",
            use_container_width=True,
        )

    if submitted:
        if ingredient.strip():
            add_ingredient(ingredient)
            st.rerun()
        else:
            st.warning("Enter an ingredient first.")

st.subheader("Browse your grocery shelf")
st.caption("Click an ingredient to add it to your pantry.")

tabs = st.tabs(list(groceries.keys()))

for tab, items in zip(tabs, groceries.values()):
    with tab:
        columns = st.columns(3)

        for index, (name, emoji) in enumerate(items.items()):
            with columns[index % 3]:
                selected = name.lower() in st.session_state.pantry

                if st.button(
                    f"{emoji}  {name}" + ("  ✓" if selected else ""),
                    key=f"grocery_{name}",
                    use_container_width=True,
                ):
                    add_ingredient(name)
                    st.rerun()

st.divider()
st.subheader("Your pantry")

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
else:
    st.info("Your basket is waiting! Search above or pick a grocery.")

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

st.caption(
    "Explore any cuisine, or choose a favorite for your next meal."
)

if st.button(
    "What can I cook?",
    type="primary",
    use_container_width=True,
):
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

        pantry = {
    normalize_ingredient(item)
    for item in st.session_state.pantry
        }
        matches = []

        for recipe in recipes:
            if (
                selected_cuisine != "Any cuisine"
                and recipe["cuisine"] != selected_cuisine
            ):
                continue

            required = {
    normalize_ingredient(ingredient)
    for ingredient in recipe["ingredients"]
        }

            available = required & pantry
            missing = required - pantry

            if not missing:
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

        if not matches:
            st.info(
            "No recipes can be made with only these ingredients yet. "
            "Add other ingredients you have, or try another cuisine."
        )
        else:
            st.subheader("Here's what you could cook")

            for match in matches[:6]:
                recipe = match["recipe"]
                percentage = round(match["score"] * 100)

                with st.container(border=True):
                    st.subheader(recipe["name"])

                    st.caption(
                        f'{recipe["cuisine"]} • '
                        f'{recipe["minutes"]} minutes • '
                        f'Serves {recipe["servings"]}'
                    )

                    st.progress(
                        match["score"],
                        text=f"{percentage}% ingredient match",
                    )

                    st.write(
                        "**You have:** "
                        + ", ".join(match["available"])
                    )

                    if match["missing"]:
                        st.write(
                            "**Still needed:** "
                            + ", ".join(match["missing"])
                        )
                    else:
                        st.success("You have all the listed ingredients!")

                    with st.expander("View cooking instructions"):
                        for number, step in enumerate(
                            recipe["instructions"], start=1
                        ):
                            st.write(f"{number}. {step}")