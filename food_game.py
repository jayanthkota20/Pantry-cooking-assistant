import random

import streamlit as st


# Each entry has its own name.
# Some foods share an emoji, so pairs are matched by ID.
FOOD_CATALOG = {
    "vegetables": [
        ("carrot", "🥕", "Carrot"),
        ("tomato", "🍅", "Tomato"),
        ("broccoli", "🥦", "Broccoli"),
        ("eggplant", "🍆", "Eggplant"),
        ("potato", "🥔", "Potato"),
        ("onion", "🧅", "Onion"),
        ("cucumber", "🥒", "Cucumber"),
        ("bell_pepper", "🫑", "Bell pepper"),
    ],
    "fruits": [
        ("apple", "🍎", "Apple"),
        ("banana", "🍌", "Banana"),
        ("strawberry", "🍓", "Strawberry"),
        ("watermelon", "🍉", "Watermelon"),
        ("grapes", "🍇", "Grapes"),
        ("pineapple", "🍍", "Pineapple"),
        ("orange", "🍊", "Orange"),
        ("kiwi", "🥝", "Kiwi"),
    ],
    "pantry_and_dairy": [
        ("bread", "🍞", "Bread"),
        ("rice", "🍚", "Rice"),
        ("noodles", "🍜", "Noodles"),
        ("eggs", "🥚", "Eggs"),
        ("milk", "🥛", "Milk"),
        ("cheese", "🧀", "Cheese"),
        ("butter", "🧈", "Butter"),
        ("beans", "🫘", "Beans"),
    ],
    "meat_and_seafood": [
        ("chicken", "🍗", "Chicken"),
        ("meat", "🥩", "Meat"),
        ("fish", "🐟", "Fish"),
        ("prawns", "🦐", "Prawns"),
        ("crab", "🦀", "Crab"),
    ],
    "spices_and_herbs": [
        ("salt", "🧂", "Salt"),
        ("garlic", "🧄", "Garlic"),
        ("ginger", "🫚", "Ginger"),
        ("chili", "🌶️", "Chili"),
        ("herbs", "🌿", "Herbs"),
    ],
}

WIN_MESSAGES = [
    "You matched everything! Now go match "
    "those ingredients with a frying pan.",

    "The vegetables are impressed. "
    "The onion is crying happy tears.",

    "Master of matching, champion of snacks. "
    "Dinner is still your responsibility.",

    "Even the broccoli is cheering for you. "
    "That's a tough crowd!",

    "You found every pair. "
    "Your missing socks could use your help next.",

    "Your memory is fully cooked. "
    "Time to check on dinner!",
]

GAME_VERSION = 3


def start_food_game():
    # Include one random food from every category.
    selected = [
        random.choice(items)
        for items in FOOD_CATALOG.values()
    ]

    selected_ids = {
        food_id
        for food_id, _, _ in selected
    }

    remaining = [
        food
        for items in FOOD_CATALOG.values()
        for food in items
        if food[0] not in selected_ids
    ]

    # Add three more random foods, making eight pairs.
    selected.extend(
        random.sample(remaining, 8 - len(selected))
    )

    food_details = {
        food_id: {
            "emoji": emoji,
            "name": name,
        }
        for food_id, emoji, name in selected
    }

    cards = list(food_details) * 2
    random.shuffle(cards)

    st.session_state.food_game = {
        "version": GAME_VERSION,
        "cards": cards,
        "foods": food_details,
        "matched": [],
        "flipped": [],
        "moves": 0,
    }


def flip_food_card(index):
    game = st.session_state.food_game

    if index in game["matched"]:
        return

    # Hide a previous wrong pair on the next hidden-card click.
    if len(game["flipped"]) == 2:
        if index in game["flipped"]:
            return

        game["flipped"] = []

    if index in game["flipped"]:
        return

    game["flipped"].append(index)

    if len(game["flipped"]) == 2:
        game["moves"] += 1
        first, second = game["flipped"]

        # Match food IDs, not just their emoji.
        if game["cards"][first] == game["cards"][second]:
            game["matched"].extend([first, second])
            game["flipped"] = []


def render_food_game():
    existing_game = st.session_state.get("food_game", {})

    if existing_game.get("version") != GAME_VERSION:
        start_food_game()

    st.markdown(
        """
<style>
.st-key-food_game_board .stButton > button {
    min-height: 78px;
    padding: 4px;
    border-radius: 14px;
    background: #ffffff !important;
    border: 2px solid #c7d7bc;
    opacity: 1 !important;
}

.st-key-food_game_board button,
.st-key-food_game_board button * {
    opacity: 1 !important;
}

.st-key-food_game_board .stButton > button p {
    font-family:
        "Segoe UI Emoji",
        "Apple Color Emoji",
        "Noto Color Emoji",
        sans-serif !important;
    font-size: clamp(32px, 4vw, 48px) !important;
    line-height: 1.2 !important;
    color: #285943 !important;
    -webkit-text-fill-color: #285943 !important;
}

.st-key-food_game_board .stButton > button:hover {
    background: #edf5e6 !important;
    border-color: #588447;
}

.st-key-food_game_board [data-testid="stCaptionContainer"] {
    min-height: 38px;
    text-align: center;
}

.st-key-food_game_board [data-testid="stCaptionContainer"] p {
    color: #263b29 !important;
    font-size: 14px !important;
    font-weight: 600;
}
</style>
""",
        unsafe_allow_html=True,
    )

    with st.expander(
        "Food Match — Play and learn",
        expanded=True,
    ):
        st.caption(
            "Find 8 matching pairs and learn their names. "
            "Every new game mixes foods from different categories."
        )

        game = st.session_state.food_game
        pairs_found = len(game["matched"]) // 2

        best_moves = st.session_state.get("food_game_best")

        if pairs_found == 8:
            if (
                best_moves is None
                or game["moves"] < best_moves
            ):
                st.session_state.food_game_best = game["moves"]
                best_moves = game["moves"]

        first, second, third = st.columns(3)

        first.metric("Pairs found", f"{pairs_found} / 8")
        second.metric("Moves", game["moves"])
        third.metric(
            "Best moves",
            best_moves if best_moves is not None else "—",
        )

        st.progress(pairs_found / 8)

        with st.container(key="food_game_board"):
            for row in range(4):
                columns = st.columns(4, gap="small")

                for column, container in enumerate(columns):
                    index = row * 4 + column
                    food_id = game["cards"][index]
                    food = game["foods"][food_id]

                    revealed = (
                        index in game["matched"]
                        or index in game["flipped"]
                    )

                    label = food["emoji"] if revealed else "?"

                    with container:
                        st.button(
                            label,
                            key=f"food_card_{index}",
                            help=(
                                food["name"]
                                if revealed
                                else "Click to reveal this food"
                            ),
                            disabled=False,
                            on_click=flip_food_card,
                            args=(index,),
                            use_container_width=True,
                        )

                        st.caption(
                            food["name"] if revealed else "Hidden"
                        )

        if pairs_found == 8:
            if "win_message" not in game:
                game["win_message"] = random.choice(
                    WIN_MESSAGES
                )
                st.balloons()

            st.success(
                f"You found all 8 pairs "
                f"in {game['moves']} moves!"
            )
            st.info(game["win_message"])

        elif len(game["flipped"]) == 2:
            st.caption(
                "No match this time. Click another hidden card."
            )

        elif len(game["flipped"]) == 1:
            st.caption("Choose a second card.")

        st.button(
            "Start a new game",
            key="food_game_restart",
            on_click=start_food_game,
            use_container_width=True,
        )