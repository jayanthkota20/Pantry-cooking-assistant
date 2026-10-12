import sqlite3
from contextlib import contextmanager
from pathlib import Path

import streamlit as st


DB = Path(__file__).parent / "pantry.db"


@contextmanager
def shopping_connection():
    connection = sqlite3.connect(DB)

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS shopping (
                id INTEGER PRIMARY KEY,
                item TEXT NOT NULL,
                checked INTEGER NOT NULL DEFAULT 0,
                UNIQUE(item COLLATE NOCASE)
            )
            """
        )

        connection.commit()

        with connection:
            yield connection
    finally:
        connection.close()


def add_shopping_items(items):
    count = 0

    with shopping_connection() as connection:
        for item in items:
            item = " ".join(
                str(item).strip().split()
            )

            if item:
                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO shopping (item)
                    VALUES (?)
                    """,
                    (item,),
                )

                count += cursor.rowcount

    return count


def read_shopping_items():
    with shopping_connection() as connection:
        return connection.execute(
            """
            SELECT id, item, checked
            FROM shopping
            ORDER BY checked, id
            """
        ).fetchall()


def render_shopping_list():
    st.subheader("Your shopping list")

    st.caption(
        "Keep missing ingredients in one place. "
        "Tick them off as you shop."
    )

    with st.form(
        "shopping_add",
        clear_on_submit=True,
    ):
        items = st.text_area(
            "Add items, one per line",
            placeholder=(
                "Carrots — 2\n"
                "Noodles — 200 g"
            ),
            height=100,
        )

        submitted = st.form_submit_button(
            "Add items",
            type="primary",
        )

    if submitted:
        if not items.strip():
            st.warning("Enter at least one item.")
        else:
            add_shopping_items(items.splitlines())
            st.rerun()

    rows = read_shopping_items()

    if not rows:
        st.info(
            "Your list is empty. Add an item here "
            "or use suggested additions from AI Chef."
        )
        return

    remaining = sum(
        not checked
        for _, _, checked in rows
    )

    st.caption(f"{remaining} items left to buy")

    for item_id, item, checked in rows:
        check_col, remove_col = st.columns([5, 1])

        with check_col:
            value = st.checkbox(
                item,
                value=bool(checked),
                key=f"shop_check_{item_id}",
            )

            if value != bool(checked):
                with shopping_connection() as connection:
                    connection.execute(
                        """
                        UPDATE shopping
                        SET checked = ?
                        WHERE id = ?
                        """,
                        (int(value), item_id),
                    )

                st.rerun()

        with remove_col:
            if st.button(
                "Remove",
                key=f"shop_remove_{item_id}",
            ):
                with shopping_connection() as connection:
                    connection.execute(
                        "DELETE FROM shopping WHERE id = ?",
                        (item_id,),
                    )

                st.rerun()

    left, right = st.columns(2)

    with left:
        if st.button("Clear purchased items"):
            with shopping_connection() as connection:
                connection.execute(
                    "DELETE FROM shopping WHERE checked = 1"
                )

            st.rerun()

    with right:
        content = "\n".join(
            f"[{'x' if checked else ' '}] {item}"
            for _, item, checked in rows
        )

        st.download_button(
            "Download shopping list",
            data=content,
            file_name="shopping_list.txt",
            mime="text/plain",
        )

    st.caption(
        "Checking an item does not add it to your pantry. "
        "Add purchased ingredients in My Pantry "
        "to set their reminder dates."
    )