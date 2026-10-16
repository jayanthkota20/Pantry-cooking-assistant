import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from favorites import read_favorites


DB = Path(__file__).parent / "pantry.db"
MEALS = ("Breakfast", "Lunch", "Dinner")


@contextmanager
def planner_connection():
    connection = sqlite3.connect(DB, timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS weekly_meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meal_date TEXT NOT NULL,
                    meal_slot TEXT NOT NULL,
                    name TEXT NOT NULL,
                    recipe_text TEXT NOT NULL DEFAULT '',
                    source TEXT NOT NULL,
                    UNIQUE(meal_date, meal_slot)
                )
                """
            )
            yield connection
    finally:
        connection.close()


def monday_of(day):
    return day - timedelta(days=day.weekday())


def save_meal(day, slot, name, recipe_text, source):
    if not isinstance(day, date) or slot not in MEALS:
        raise ValueError("Choose a valid date and meal slot.")

    if not name.strip():
        raise ValueError("Enter a meal name.")

    if source not in {
        "Custom meal",
        "Latest AI recipe",
        "Favorite",
    }:
        raise ValueError("Choose a valid recipe source.")

    with planner_connection() as connection:
        connection.execute(
            """
            INSERT INTO weekly_meals (
                meal_date,
                meal_slot,
                name,
                recipe_text,
                source
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(meal_date, meal_slot) DO UPDATE SET
                name = excluded.name,
                recipe_text = excluded.recipe_text,
                source = excluded.source
            """,
            (
                day.isoformat(),
                slot,
                name.strip(),
                recipe_text.strip(),
                source,
            ),
        )


def read_week(day):
    start = monday_of(day)
    end = start + timedelta(days=7)

    with planner_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM weekly_meals
            WHERE meal_date >= ? AND meal_date < ?
            ORDER BY meal_date,
                CASE meal_slot
                    WHEN 'Breakfast' THEN 0
                    WHEN 'Lunch' THEN 1
                    ELSE 2
                END
            """,
            (start.isoformat(), end.isoformat()),
        ).fetchall()

    return [dict(row) for row in rows]


def remove_meal(meal_id):
    with planner_connection() as connection:
        connection.execute(
            "DELETE FROM weekly_meals WHERE id = ?",
            (meal_id,),
        )


def weekly_download(start, records):
    start = monday_of(start)

    lookup = {
        (row["meal_date"], row["meal_slot"]): row
        for row in records
    }

    lines = [
        f"# Weekly meal plan — {start:%d %B %Y}",
        "",
    ]

    for offset in range(7):
        day = start + timedelta(days=offset)
        lines.extend([f"## {day:%A, %d %B}", ""])

        for slot in MEALS:
            row = lookup.get((day.isoformat(), slot))
            name = row["name"] if row else "Not planned"

            lines.append(f"### {slot}: {name}")

            if row:
                lines.append(
                    row["recipe_text"]
                    or "Recipe details not added yet."
                )

            lines.append("")

    return "\n".join(lines)


def ai_recipe_name(answer):
    for line in answer.splitlines():
        if line.strip().startswith("#"):
            return (
                line.strip()
                .lstrip("#")
                .strip()
                .replace("**", "")
            )

    return "My AI recipe"


def render_meal_planner():
    st.subheader("Your meal planner")
    st.caption(
        "Choose any date and plan your own meal, "
        "your latest AI recipe, or a favorite."
    )

    # Apply navigation before creating the date widget.
    pending_date = st.session_state.pop(
        "planner_pending_date",
        None,
    )

    if pending_date is not None:
        st.session_state["planner_week"] = pending_date

    notice = st.session_state.pop("planner_notice", None)

    if notice:
        st.success(notice)

    selected = st.date_input(
        "View the week containing this date",
        value=date.today(),
        key="planner_week",
    )

    start = monday_of(selected)
    days = [
        start + timedelta(days=offset)
        for offset in range(7)
    ]

    st.caption(
        f"Monday {start:%d %b %Y} — "
        f"Sunday {days[-1]:%d %b %Y}"
    )

    try:
        records = read_week(start)
    except sqlite3.Error as error:
        st.error(f"Could not open the meal planner: {error}")
        return

    source = st.radio(
        "Add a meal from",
        [
            "Custom meal",
            "Latest AI recipe",
            "Favorite",
        ],
        horizontal=True,
        key="planner_source",
    )

    favorites = []
    ai_answer = st.session_state.get("ai_recipe", "")
    ready = True

    if source == "Latest AI recipe" and not ai_answer:
        st.info(
            "Generate a recipe in AI Chef first, "
            "or choose Custom meal."
        )
        ready = False

    elif source == "Favorite":
        try:
            favorites = read_favorites()
        except sqlite3.Error:
            st.error(
                "Could not load favorites. "
                "You can still add a custom meal."
            )

        if not favorites:
            st.info(
                "No favorites available. Choose Custom meal "
                "or Latest AI recipe."
            )
            ready = False

    if ready:
        form_key = (
            f"planner_form_{source}_{selected.isoformat()}"
        )

        with st.form(form_key):
            left, right = st.columns(2)

            with left:
                meal_day = st.date_input(
                    "Meal date",
                    value=selected,
                )

            with right:
                slot = st.selectbox("Meal", MEALS)

            if source == "Custom meal":
                name = st.text_input(
                    "Meal name",
                    placeholder="My vegetable pulao",
                )

                ingredients = st.text_area(
                    "Ingredients (optional)",
                    placeholder="One ingredient per line",
                )

                instructions = st.text_area(
                    "Cooking instructions or notes (optional)",
                    height=140,
                )

                text_parts = []

                if ingredients.strip():
                    bullets = "\n".join(
                        "- " + line.strip().lstrip("- ")
                        for line in ingredients.splitlines()
                        if line.strip()
                    )
                    text_parts.append(
                        "### Ingredients\n" + bullets
                    )

                if instructions.strip():
                    text_parts.append(
                        "### Instructions or notes\n"
                        + instructions.strip()
                    )

                recipe_text = "\n\n".join(text_parts)

                st.caption(
                    "Save just a meal name if you prefer. "
                    "You can add recipe details later."
                )

            elif source == "Latest AI recipe":
                name = ai_recipe_name(ai_answer)
                recipe_text = ai_answer

                st.write("**Selected recipe:** " + name)
                st.caption(
                    "A copy is saved in the planner. "
                    "Saving to Favorites first is not required."
                )

            else:
                choices = {
                    row["id"]: row
                    for row in favorites
                }

                chosen = st.selectbox(
                    "Recipe",
                    list(choices),
                    format_func=lambda ident: (
                        f"{choices[ident]['name']} · #{ident}"
                    ),
                )

                name = choices[chosen]["name"]
                recipe_text = choices[chosen]["recipe_text"]

            replace = st.checkbox(
                "Replace an existing meal in this date and slot",
                value=False,
            )

            submitted = st.form_submit_button(
                "Save to meal plan",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            try:
                # Keep this separate from the week currently displayed.
                target_records = read_week(meal_day)
            except sqlite3.Error as error:
                st.error(
                    f"Could not check the selected date: {error}"
                )
                target_records = None

            if target_records is not None:
                occupied = any(
                    row["meal_date"] == meal_day.isoformat()
                    and row["meal_slot"] == slot
                    for row in target_records
                )

                if occupied and not replace:
                    st.warning(
                        "That date and meal slot already have a meal. "
                        "Tick Replace to change it."
                    )
                else:
                    try:
                        save_meal(
                            meal_day,
                            slot,
                            name,
                            recipe_text,
                            source,
                        )
                    except (ValueError, sqlite3.Error) as error:
                        st.error(str(error))
                    else:
                        st.session_state.planner_notice = (
                            f"Saved {name.strip()} for "
                            f"{meal_day:%A, %d %B} "
                            f"{slot.lower()}."
                        )

                        # Navigate on the next run, before the widget exists.
                        st.session_state["planner_pending_date"] = (
                            meal_day
                        )
                        st.rerun()

    st.divider()

    planned_days = len({
        row["meal_date"]
        for row in records
    })

    st.caption(
        f"{len(records)} / 21 meal slots planned · "
        f"{planned_days} / 7 days"
    )

    st.download_button(
        "Download weekly plan",
        data=weekly_download(start, records),
        file_name=f"meal_plan_{start.isoformat()}.md",
        mime="text/markdown",
        key="planner_download",
    )

    for day in days:
        day_rows = {
            row["meal_slot"]: row
            for row in records
            if row["meal_date"] == day.isoformat()
        }

        with st.expander(
            day.strftime("%A, %d %B"),
            expanded=bool(day_rows),
        ):
            for slot in MEALS:
                row = day_rows.get(slot)

                if not row:
                    st.caption(f"{slot} · Not planned")
                    continue

                st.markdown(
                    f"**{slot} · {row['name']}**"
                )
                st.caption(
                    "Added from: " + row["source"]
                )

                show_recipe = st.checkbox(
                    "Show recipe or notes",
                    key=f"planner_show_{row['id']}",
                )

                if show_recipe:
                    st.markdown(
                        row["recipe_text"]
                        or "No recipe details yet. "
                        "Use Edit to add them."
                    )

                    if row["source"] != "Custom meal":
                        st.caption(
                            "AI recipe details and nutrition "
                            "estimates may need review."
                        )

                with st.expander("Edit meal"):
                    with st.form(
                        f"planner_edit_{row['id']}"
                    ):
                        edited_name = st.text_input(
                            "Meal name",
                            value=row["name"],
                        )

                        edited_text = st.text_area(
                            "Recipe or notes (Markdown supported)",
                            value=row["recipe_text"],
                            height=180,
                        )

                        edit = st.form_submit_button(
                            "Save changes"
                        )

                    if edit:
                        try:
                            save_meal(
                                day,
                                slot,
                                edited_name,
                                edited_text,
                                "Custom meal",
                            )
                        except (ValueError, sqlite3.Error) as error:
                            st.error(str(error))
                        else:
                            st.session_state.planner_notice = (
                                "Meal updated."
                            )
                            st.rerun()

                if st.button(
                    "Remove meal",
                    key=f"planner_remove_{row['id']}",
                ):
                    try:
                        remove_meal(row["id"])
                    except sqlite3.Error as error:
                        st.error(str(error))
                    else:
                        st.session_state.planner_notice = (
                            "Meal removed."
                        )
                        st.rerun()

                st.divider()

    st.caption(
        "Plans are saved locally. Editing or deleting a "
        "favorite does not change its saved meal-plan copy."
    )