import hashlib
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote_plus

import streamlit as st


DB = Path(__file__).parent / "pantry.db"

FOOD_TYPES = [
    "Not checked",
    "Vegetarian",
    "Contains eggs",
    "Non-vegetarian",
]

CUISINES = [
    "Not specified",
    "Indian",
    "Chinese",
    "Italian",
    "Korean",
    "Japanese",
    "Thai",
    "American",
    "Mexican",
    "Other / mixed",
]

GLUTEN_STATUSES = [
    "Not checked",
    "Gluten-free",
    "Contains gluten",
]


# ---------- Database ----------

@contextmanager
def favorite_connection():
    connection = sqlite3.connect(DB, timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS favorite_recipes (
                    id INTEGER PRIMARY KEY,
                    recipe_hash TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    recipe_text TEXT NOT NULL,
                    food_type TEXT NOT NULL,
                    cuisine TEXT NOT NULL,
                    gluten_status TEXT NOT NULL
                        DEFAULT 'Not checked',
                    saved_on TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            yield connection
    finally:
        connection.close()


def recipe_hash(answer):
    return hashlib.sha256(
        answer.strip().encode("utf-8")
    ).hexdigest()


def read_favorites():
    with favorite_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM favorite_recipes
            ORDER BY saved_on DESC, id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def save_favorite(
    name,
    answer,
    food_type,
    cuisine,
    gluten_status,
):
    name = name.strip()
    answer = answer.strip()

    if not name or not answer:
        raise ValueError("Recipe name and text are required.")

    if food_type not in FOOD_TYPES:
        raise ValueError("Choose a listed food type.")

    if cuisine not in CUISINES:
        raise ValueError("Choose a listed cuisine.")

    if gluten_status not in GLUTEN_STATUSES:
        raise ValueError("Choose a listed gluten status.")

    with favorite_connection() as connection:
        # Saving again does not overwrite manually corrected labels.
        connection.execute(
            """
            INSERT INTO favorite_recipes (
                recipe_hash,
                name,
                recipe_text,
                food_type,
                cuisine,
                gluten_status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(recipe_hash) DO NOTHING
            """,
            (
                recipe_hash(answer),
                name,
                answer,
                food_type,
                cuisine,
                gluten_status,
            ),
        )


def update_favorite(
    recipe_id,
    name,
    food_type,
    cuisine,
    gluten_status,
):
    name = name.strip()

    if not name:
        raise ValueError("Enter a recipe name.")

    if (
        food_type not in FOOD_TYPES
        or cuisine not in CUISINES
        or gluten_status not in GLUTEN_STATUSES
    ):
        raise ValueError("Choose one of the listed labels.")

    with favorite_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE favorite_recipes
            SET name = ?,
                food_type = ?,
                cuisine = ?,
                gluten_status = ?
            WHERE id = ?
            """,
            (
                name,
                food_type,
                cuisine,
                gluten_status,
                recipe_id,
            ),
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "This favorite no longer exists. Refresh the page."
            )


def remove_favorite(recipe_id):
    with favorite_connection() as connection:
        connection.execute(
            "DELETE FROM favorite_recipes WHERE id = ?",
            (recipe_id,),
        )


# ---------- Automatic labels ----------

def automatic_labels(answer):
    labels = {
        "food_type": "Not checked",
        "cuisine": "Not specified",
    }

    for line in answer.splitlines():
        clean = line.replace("**", "").strip()
        key, separator, value = clean.partition(":")

        if not separator:
            continue

        key = key.strip().casefold()
        value = value.strip().casefold()

        if key == "food type":
            choices = {
                item.casefold(): item
                for item in FOOD_TYPES
            }
            labels["food_type"] = choices.get(
                value,
                "Not checked",
            )

        elif key == "cuisine":
            choices = {
                item.casefold(): item
                for item in CUISINES
            }
            labels["cuisine"] = choices.get(
                value,
                "Not specified",
            )

    return labels


def filter_favorites(
    recipes,
    search="",
    food_type="All",
    cuisine="All",
    gluten="All",
):
    search = search.strip().casefold()

    return [
        recipe
        for recipe in recipes
        if (
            not search
            or search in recipe["name"].casefold()
        )
        and (
            food_type == "All"
            or recipe["food_type"] == food_type
        )
        and (
            cuisine == "All"
            or recipe["cuisine"] == cuisine
        )
        and (
            gluten == "All"
            or recipe["gluten_status"] == gluten
        )
    ]


# ---------- One click save ----------

def render_save_favorite(
    answer,
    recipe_name="",
    context=None,
):
    token = recipe_hash(answer)

    try:
        existing = next(
            (
                recipe
                for recipe in read_favorites()
                if recipe["recipe_hash"] == token
            ),
            None,
        )
    except sqlite3.Error:
        st.error("Could not load favorites. Please try again.")
        return

    if existing:
        st.success(
            "Saved to favorites. "
            "Open Favorites to view or edit it."
        )
        return

    labels = automatic_labels(answer)

    st.caption(
        f"AI labels: {labels['food_type']} · "
        f"{labels['cuisine']} · Gluten: Not checked. "
        "You can correct labels in Favorites."
    )

    if st.button(
        "Add to favorites",
        key=f"save_favorite_{token}",
        type="primary",
    ):
        try:
            save_favorite(
                recipe_name or "Untitled recipe",
                answer,
                labels["food_type"],
                labels["cuisine"],
                "Not checked",
            )
        except (sqlite3.Error, ValueError):
            st.error(
                "Could not save the recipe. Please try again."
            )
        else:
            st.rerun()


# ---------- Favorites tab ----------

def render_favorites():
    st.subheader("Your favorite recipes")

    st.caption(
        "Reopen your saved meals without generating them again. "
        "AI food and cuisine labels can be corrected below."
    )

    notice = st.session_state.pop("favorite_notice", None)

    if notice:
        st.success(notice)

    try:
        recipes = read_favorites()
    except sqlite3.Error:
        st.error("Could not load favorites. Please try again.")
        return

    if not recipes:
        st.info(
            "No favorites yet. Generate a recipe in AI Chef "
            "and click Add to favorites."
        )
        return

    search = st.text_input(
        "Search recipe names",
        placeholder="Try paneer or noodles...",
        key="favorites_search",
    )

    first, second, third = st.columns(3)

    with first:
        food = st.selectbox(
            "Food type",
            ["All", *FOOD_TYPES],
            key="favorites_food_filter",
        )

    with second:
        cuisine = st.selectbox(
            "Cuisine",
            ["All", *CUISINES],
            key="favorites_cuisine_filter",
        )

    with third:
        gluten = st.selectbox(
            "Gluten status",
            ["All", *GLUTEN_STATUSES],
            key="favorites_gluten_filter",
        )

    matches = filter_favorites(
        recipes,
        search,
        food,
        cuisine,
        gluten,
    )

    st.caption(
        f"Showing {len(matches)} of {len(recipes)} recipes. "
        "Gluten status is user-reviewed, not AI verification."
    )

    if not matches:
        st.info(
            "No recipes match these filters. "
            "Try All or a different search."
        )

    for recipe in matches:
        recipe_id = recipe["id"]

        with st.container(border=True):
            st.subheader(recipe["name"])

            st.caption(
                f"{recipe['food_type']} · "
                f"{recipe['cuisine']} · "
                f"{recipe['gluten_status']}"
            )

            with st.expander("View recipe"):
                st.caption(
                    "Saved AI suggestion. "
                    "Nutrition values are approximate."
                )
                st.markdown(recipe["recipe_text"])

            left, right = st.columns(2)

            with left:
                filename = re.sub(
                    r"[^a-zA-Z0-9_-]+",
                    "_",
                    recipe["name"],
                ).strip("_") or "recipe"

                st.download_button(
                    "Download recipe",
                    data=recipe["recipe_text"],
                    file_name=f"{filename}.md",
                    mime="text/markdown",
                    key=f"favorite_download_{recipe_id}",
                )

            with right:
                st.link_button(
                    "Find on YouTube",
                    "https://www.youtube.com/results?search_query="
                    + quote_plus(recipe["name"] + " recipe"),
                )

            with st.expander("Correct labels or remove"):
                st.caption(
                    "Vegetarian excludes meat, seafood, and eggs. "
                    "Contains eggs is for meat-free egg dishes."
                )

                with st.form(f"favorite_edit_{recipe_id}"):
                    name = st.text_input(
                        "Recipe name",
                        value=recipe["name"],
                        key=f"favorite_name_{recipe_id}",
                    )

                    new_food = st.selectbox(
                        "Food type",
                        FOOD_TYPES,
                        index=FOOD_TYPES.index(
                            recipe["food_type"]
                        ),
                        key=f"favorite_food_{recipe_id}",
                    )

                    new_cuisine = st.selectbox(
                        "Cuisine",
                        CUISINES,
                        index=CUISINES.index(
                            recipe["cuisine"]
                        ),
                        key=f"favorite_cuisine_{recipe_id}",
                    )

                    new_gluten = st.selectbox(
                        "Gluten status",
                        GLUTEN_STATUSES,
                        index=GLUTEN_STATUSES.index(
                            recipe["gluten_status"]
                        ),
                        key=f"favorite_gluten_{recipe_id}",
                    )

                    update = st.form_submit_button(
                        "Update favorite"
                    )

                if update:
                    try:
                        update_favorite(
                            recipe_id,
                            name,
                            new_food,
                            new_cuisine,
                            new_gluten,
                        )
                    except ValueError as error:
                        st.warning(str(error))
                    except sqlite3.Error:
                        st.error(
                            "Could not update this favorite."
                        )
                    else:
                        st.session_state.favorite_notice = (
                            "Favorite updated. If it no longer "
                            "appears, check your active filters."
                        )
                        st.rerun()

                if st.button(
                    "Remove from favorites",
                    key=f"favorite_remove_{recipe_id}",
                ):
                    try:
                        remove_favorite(recipe_id)
                    except sqlite3.Error:
                        st.error(
                            "Could not remove this favorite."
                        )
                    else:
                        st.session_state.favorite_notice = (
                            "Recipe removed from favorites."
                        )
                        st.rerun()