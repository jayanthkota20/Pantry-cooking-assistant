import sqlite3
from favorites import render_favorites
from food_game import render_food_game
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from ai_chef import render_ai_chef
from shopping import render_shopping_list


st.set_page_config(
    page_title="Pantry Cooking Assistant",
    page_icon="🥕",
    layout="wide",
)

PANTRY_DB = Path(__file__).parent / "pantry.db"


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


# ---------- Saved pantry ----------

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
    st.session_state.pantry = list(
        st.session_state.pantry_records
    )


def add_ingredient(name, kind, added_on):
    name = normalize_ingredient(name)

    # Keep an existing item's saved dates.
    if not name or name in st.session_state.pantry_records:
        return

    reminder_days = 10 if kind == "Dry goods" else 7

    save_pantry_item(
        name,
        kind,
        added_on,
        added_on + timedelta(days=reminder_days),
    )

    refresh_pantry()


# Preserve pantry ingredients from the previous interface.
previous_pantry = list(st.session_state.get("pantry", []))
refresh_pantry()

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
            f"Added: {record['added_on']} · "
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


# ---------- Interface styling ----------

st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 0% 0%, #eaf1df, transparent 45%
        ),
        radial-gradient(
            circle at 100% 100%, #ffe9d5, transparent 45%
        ),
        #fffaf0;
    color: #263b29;
}

.block-container {
    max-width: 1120px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    padding: 20px 0 28px;
}

.hero .eyebrow {
    color: #a64b20;
    font-weight: 700;
    letter-spacing: 2px;
    font-size: 13px;
}

.hero h1 {
    color: #285943;
    font-size: clamp(32px, 5vw, 48px);
    margin: 0;
}

.hero p {
    color: #626b5b;
    font-size: 18px;
}

.stApp h2,
.stApp h3 {
    color: #285943;
}

.stButton button,
.stFormSubmitButton button,
.stLinkButton a {
    border-radius: 12px;
    min-height: 44px;
}

.stApp button[kind="primary"] {
    background: #315c3b;
    color: white;
}

.stApp button[kind="primary"] p {
    color: white;
}

[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #ffffff !important;
    color: #263b29 !important;
    -webkit-text-fill-color: #263b29 !important;
    caret-color: #263b29 !important;
}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #737a70 !important;
    -webkit-text-fill-color: #737a70 !important;
}

[data-testid="stDateInputCalendar"],
[data-baseweb="calendar"] {
    background: #fffaf0 !important;
}

[data-testid="stDateInputCalendar"],
[data-testid="stDateInputCalendar"] *,
[data-baseweb="calendar"],
[data-baseweb="calendar"] * {
    color: #263b29 !important;
    -webkit-text-fill-color: #263b29 !important;
}

[data-testid="stDateInputCalendar"] [data-selected="true"],
[data-testid="stDateInputCalendar"] [data-selected="true"] *,
[data-testid="stDateInputCalendar"] [aria-selected="true"],
[data-testid="stDateInputCalendar"] [aria-selected="true"] *,
[data-baseweb="calendar"] [aria-selected="true"],
[data-baseweb="calendar"] [aria-selected="true"] * {
    background: #315c3b !important;
    color: white !important;
    -webkit-text-fill-color: white !important;
}

[role="listbox"] [role="option"],
[role="listbox"] [role="option"] *,
[data-baseweb="menu"] li,
[data-baseweb="menu"] li * {
    color: #263b29 !important;
    -webkit-text-fill-color: #263b29 !important;
}

[data-testid="stTabs"] [role="tab"] {
    font-size: 17px;
    padding: 12px 18px;
}

@media (max-width: 640px) {
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero {
        padding-top: 8px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="grocery-border" aria-hidden="true">🥕 🍅 🥦 🍋 🧅 🥑 🍚 🥬</div>
<div class="hero">
    <div class="eyebrow">PANTRY COOKING ASSISTANT</div>
    <h1>Good meals start with what you have.</h1>
    <p>
        Keep track of your ingredients.
        Let your AI Chef help with dinner.
    </p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown(
    """
<style>
.block-container {
    position: relative;
    z-index: 1;
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
    left: 5%;
    animation-delay: -2s;
}

.floating-groceries span:nth-child(2) {
    left: 18%;
    animation-delay: -13s;
}

.floating-groceries span:nth-child(3) {
    left: 31%;
    animation-delay: -7s;
}

.floating-groceries span:nth-child(4) {
    left: 44%;
    animation-delay: -18s;
}

.floating-groceries span:nth-child(5) {
    left: 57%;
    animation-delay: -4s;
}

.floating-groceries span:nth-child(6) {
    left: 70%;
    animation-delay: -16s;
}

.floating-groceries span:nth-child(7) {
    left: 82%;
    animation-delay: -10s;
}

.floating-groceries span:nth-child(8) {
    left: 93%;
    animation-delay: -21s;
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

.grocery-border {
    text-align: center;
    font-size: clamp(24px, 4vw, 44px);
    letter-spacing: 10px;
    opacity: 0.65;
    margin-bottom: 16px;
}

@media (prefers-reduced-motion: reduce) {
    .floating-groceries {
        display: none;
    }
}
</style>

<div class="floating-groceries" aria-hidden="true">
<span>🥕</span>
<span>🍎</span>
<span>🥦</span>
<span>🍗</span>
<span>🍅</span>
<span>🐟</span>
<span>🍋</span>
<span>🦐</span>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Due reminders ----------

today = date.today()

due_items = {
    name: record
    for name, record in st.session_state.pantry_records.items()
    if date.fromisoformat(record["remind_on"]) <= today
}

if due_items:
    notice, action = st.columns([4, 1])

    with notice:
        st.warning(
            "Reminders due: "
            + ", ".join(name.title() for name in due_items)
        )

    with action:
        open_reminders = st.button(
            "View reminders",
            use_container_width=True,
        )

    if (
        open_reminders
        or st.session_state.get("reminders_shown_on")
        != today.isoformat()
    ):
        st.session_state.reminders_shown_on = today.isoformat()
        pantry_reminder_popup()


# ---------- Main navigation ----------

pantry_tab, chef_tab, shopping_tab, favorites_tab = st.tabs(
    [
        "My Pantry",
        "AI Chef",
        "Shopping List",
        "Favorites",
    ]
)


# ---------- My Pantry ----------

with pantry_tab:
    st.subheader("Your kitchen, at a glance")

    first, second, third = st.columns(3)

    first.metric(
        "Pantry ingredients",
        len(st.session_state.pantry),
    )
    second.metric("Reminders due", len(due_items))
    third.metric(
        "Dry goods",
        sum(
            record["kind"] == "Dry goods"
            for record in st.session_state.pantry_records.values()
        ),
    )

    st.caption(
        "Reminders help you remember ingredients; "
        "they are not expiry dates. "
        "Fresh: 7 days · Dry goods: 10 days."
    )

    add_col, saved_col = st.columns(
        [1.15, 1],
        gap="large",
    )

    with add_col:
        st.subheader("Add ingredients")

        kind_col, date_col = st.columns(2)

        with kind_col:
            new_kind = st.selectbox(
                "Reminder category",
                ["Fresh", "Dry goods"],
                key="new_item_kind",
            )

        with date_col:
            added_date = st.date_input(
                "Date added",
                value=today,
                max_value=today,
                key="new_item_added",
            )

        st.caption(
            "New items use these settings. "
            "Adding an existing item keeps its saved dates."
        )

        with st.form(
            "ingredient_search",
            clear_on_submit=True,
        ):
            ingredient_text = st.text_input(
                "Type ingredients",
                placeholder="Eggs, spinach, chicken…",
            )

            submitted = st.form_submit_button(
                "Add to pantry",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            entered_items = [
                item
                for item in ingredient_text.split(",")
                if item.strip()
            ]

            if not entered_items:
                st.warning("Enter at least one ingredient.")
            else:
                for item in entered_items:
                    add_ingredient(
                        item,
                        new_kind,
                        added_date,
                    )

                st.rerun()

        st.divider()
        st.markdown("### Browse groceries")

        shelf_search = st.text_input(
            "Search ingredients",
            placeholder="Search chicken, paneer, tomato…",
            key="shelf_search",
        )

        search_term = normalize_ingredient(shelf_search)

        def display_groceries(items):
            columns = st.columns(3)

            for index, (group, name, emoji) in enumerate(items):
                selected = (
                    normalize_ingredient(name)
                    in st.session_state.pantry
                )

                with columns[index % 3]:
                    if st.button(
                        f"{emoji} {name}"
                        + (" ✓" if selected else ""),
                        key=f"grocery_{group}_{name}",
                        disabled=selected,
                        use_container_width=True,
                    ):
                        add_ingredient(
                            name,
                            new_kind,
                            added_date,
                        )
                        st.rerun()

        if search_term:
            # Search across every grocery category.
            results = [
                (group, name, emoji)
                for group, items in groceries.items()
                for name, emoji in items.items()
                if search_term in normalize_ingredient(name)
            ]

            if results:
                display_groceries(results)
            else:
                st.info(
                    "No shelf match. Add your ingredient "
                    "using the box above."
                )
        else:
            category_tabs = st.tabs(list(groceries.keys()))

            for tab, (group, items) in zip(
                category_tabs,
                groceries.items(),
            ):
                with tab:
                    display_groceries([
                        (group, name, emoji)
                        for name, emoji in items.items()
                    ])
    with saved_col:
        st.subheader("My saved pantry")

        if st.session_state.pantry:
            for name, record in (
                st.session_state.pantry_records.items()
            ):
                with st.expander(
                    f"{name.title()} · "
                    f"Reminder: {record['remind_on']}"
                ):
                    st.caption(
                        f"{record['kind']} · "
                        f"Added: {record['added_on']}"
                    )

                    with st.form(f"edit_item_{name}"):
                        edited_kind = st.selectbox(
                            "Category",
                            ["Fresh", "Dry goods"],
                            index=(
                                0
                                if record["kind"] == "Fresh"
                                else 1
                            ),
                            key=f"kind_{name}",
                        )

                        edited_added = st.date_input(
                            "Date added",
                            value=date.fromisoformat(
                                record["added_on"]
                            ),
                            max_value=today,
                            key=f"added_{name}",
                        )

                        edited_date = st.date_input(
                            "Reminder date",
                            value=date.fromisoformat(
                                record["remind_on"]
                            ),
                            key=f"reminder_{name}",
                        )

                        if st.form_submit_button(
                            "Save reminder"
                        ):
                            if edited_date < edited_added:
                                st.error(
                                    "Reminder date must be on "
                                    "or after the added date."
                                )
                            else:
                                save_pantry_item(
                                    name,
                                    edited_kind,
                                    edited_added,
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
                if st.button(
                    "Clear pantry",
                    key="clear_pantry",
                ):
                    with sqlite3.connect(
                        PANTRY_DB
                    ) as connection:
                        connection.execute(
                            "DELETE FROM pantry"
                        )

                    refresh_pantry()
                    st.rerun()
        else:
            st.info(
                "Your pantry is empty. "
                "Type ingredients or choose from the grocery shelf."
            )
            st.divider()
        render_food_game()

# ---------- AI Chef ----------

with chef_tab:
    render_ai_chef()


# ---------- Shopping List ----------

with shopping_tab:
    render_shopping_list()

    
# ---------- Favorites ----------

with favorites_tab:
    render_favorites()