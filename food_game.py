import random

import streamlit as st


FOODS = [
    "🥕", "🍅", "🥦", "🍆",
    "🍎", "🍌", "🍓", "🍉",
]

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


def start_food_game():
    cards = FOODS * 2
    random.shuffle(cards)

    st.session_state.food_game = {
        "cards": cards,
        "matched": [],
        "flipped": [],
        "moves": 0,
    }


def flip_food_card(index):
    game = st.session_state.food_game

    if index in game["matched"]:
        return

    # Hide the previous wrong pair when another card is clicked.
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

        if game["cards"][first] == game["cards"][second]:
            game["matched"].extend([first, second])
            game["flipped"] = []


def render_food_game():
    # Reset an older 6 × 6 game during this update.
    if (
        "food_game" not in st.session_state
        or len(st.session_state.food_game["cards"]) != 16
    ):
        start_food_game()

    st.markdown(
        """
<style>
.st-key-food_game_board .stButton > button {
    min-height: 78px;
    padding: 4px;
    border-radius: 14px;
    background: #ffffff;
    border: 2px solid #c7d7bc;
    opacity: 1 !important;
}

.st-key-food_game_board .stButton > button p {
    font-size: clamp(32px, 4vw, 48px) !important;
    line-height: 1.2 !important;
    color: #285943 !important;
    -webkit-text-fill-color: #285943 !important;
    opacity: 1 !important;
}

.st-key-food_game_board .stButton > button:hover {
    background: #edf5e6;
    border-color: #588447;
}

.st-key-food_game_board .stButton > button:disabled {
    background: #edf5e6 !important;
    border-color: #91b37e !important;
    opacity: 1 !important;
}

.st-key-food_game_board .stButton > button:disabled p {
    opacity: 1 !important;
}
.st-key-food_game_board button,
.st-key-food_game_board button * {
    opacity: 1 !important;
}

.st-key-food_game_board button {
    background: #ffffff !important;
}

.st-key-food_game_board button p {
    font-family: "Segoe UI Emoji", "Apple Color Emoji",
                 "Noto Color Emoji", sans-serif !important;
    font-size: 48px !important;
}
</style>
""",
        unsafe_allow_html=True,
    )

    with st.expander(
        "Food Match — Take a cooking break",
        expanded=True,
    ):
        st.caption(
            "Find all 8 matching pairs. If two cards do not "
            "match, click another hidden card to keep playing."
        )

        game = st.session_state.food_game
        pairs_found = len(game["matched"]) // 2

        left, right = st.columns(2)
        left.metric("Pairs found", f"{pairs_found} / 8")
        right.metric("Moves", game["moves"])

        st.progress(pairs_found / 8)

        with st.container(key="food_game_board"):
            for row in range(4):
                columns = st.columns(4, gap="small")

                for column, container in enumerate(columns):
                    index = row * 4 + column

                    revealed = (
                        index in game["matched"]
                        or index in game["flipped"]
                    )

                    label = (
                        game["cards"][index]
                        if revealed
                        else "?"
                    )

                    with container:
                        st.button(
                            label,
                            key=f"food_card_{index}",
                            help=(
                                f"Matched: {game['cards'][index]}"
                                if index in game["matched"]
                                else f"Card {index + 1}"
                            ),
                            disabled=False,
                            on_click=flip_food_card,
                            args=(index,),
                            use_container_width=True,
                        )

        # Celebration belongs outside the card-building loops.
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