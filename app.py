import os
from datetime import datetime, timezone

import streamlit as st

st.set_page_config(page_title="To-Do + DB Monitor", page_icon="✅", layout="centered")

st.title("Jesse rules")
st.caption("A simple to-do list plus a Postgres database connection monitor.")

# ------------------------------
# To-do app
# ------------------------------
if "todos" not in st.session_state:
    st.session_state.todos = []

with st.form("add_todo", clear_on_submit=True):
    new_task = st.text_input("Add a task", placeholder="e.g., Finish report")
    submitted = st.form_submit_button("Add")

if submitted:
    task = new_task.strip()
    if task:
        st.session_state.todos.append({"text": task, "done": False})
    else:
        st.warning("Please enter a task before adding.")

if not st.session_state.todos:
    st.info("No tasks yet. Add your first task above.")
else:
    st.subheader("Your tasks")
    completed = 0

    for idx, todo in enumerate(st.session_state.todos):
        col1, col2 = st.columns([0.8, 0.2])

        with col1:
            checked = st.checkbox(todo["text"], value=todo["done"], key=f"todo_{idx}")
            st.session_state.todos[idx]["done"] = checked
            if checked:
                completed += 1

        with col2:
            if st.button("Delete", key=f"delete_{idx}"):
                st.session_state.todos.pop(idx)
                st.rerun()

    total = len(st.session_state.todos)
    st.progress(completed / total if total else 0)
    st.write(f"Completed **{completed}/{total}** tasks")

if st.button("Clear completed tasks"):
    st.session_state.todos = [t for t in st.session_state.todos if not t["done"]]
    st.rerun()

st.divider()

# ------------------------------
# Postgres monitor
# ------------------------------
st.header("Postgres connection monitor")
st.write(
    "Use this to verify your app is connected to the right database and that your table is receiving updates."
)

with st.expander("Connection settings", expanded=True):
    default_url = os.getenv("DATABASE_URL", "")
    db_url = st.text_input(
        "DATABASE_URL",
        value=default_url,
        type="password",
        help="Example: postgresql://user:password@host:5432/dbname",
    )
    schema_name = st.text_input("Schema", value="public")
    table_name = st.text_input("Table", value="filings")
    updated_at_col = st.text_input(
        "Updated timestamp column",
        value="updated_at",
        help="Column used to check the latest row update.",
    )

if st.button("Run DB health check"):
    if not db_url.strip():
        st.error("Please set DATABASE_URL first.")
    else:
        try:
            import psycopg

            with psycopg.connect(db_url.strip()) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT current_database(), current_user, NOW()")
                    current_db, current_user, db_now = cur.fetchone()

                    cur.execute(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_schema = %s
                              AND table_name = %s
                        )
                        """,
                        (schema_name.strip(), table_name.strip()),
                    )
                    table_exists = cur.fetchone()[0]

                    st.success("Database connection successful.")
                    st.write(f"Connected DB: `{current_db}`")
                    st.write(f"Connected user: `{current_user}`")
                    st.write(f"DB server time: `{db_now}`")

                    if not table_exists:
                        st.error(
                            f"Table `{schema_name.strip()}.{table_name.strip()}` does not exist. "
                            "This is why queries like `FROM filings` fail with relation does not exist."
                        )
                        st.info(
                            "Tip: verify the exact table name, schema, and whether you need quotes "
                            "for mixed-case names."
                        )
                    else:
                        safe_ident = psycopg.sql.Identifier(schema_name.strip(), table_name.strip())
                        safe_updated_col = psycopg.sql.Identifier(updated_at_col.strip())

                        cur.execute(
                            psycopg.sql.SQL("SELECT COUNT(*) FROM {}")
                            .format(safe_ident)
                        )
                        row_count = cur.fetchone()[0]
                        st.success(
                            f"Table `{schema_name.strip()}.{table_name.strip()}` exists with `{row_count}` rows."
                        )

                        # Check whether the updated_at column exists before querying it
                        cur.execute(
                            """
                            SELECT EXISTS (
                                SELECT 1
                                FROM information_schema.columns
                                WHERE table_schema = %s
                                  AND table_name = %s
                                  AND column_name = %s
                            )
                            """,
                            (schema_name.strip(), table_name.strip(), updated_at_col.strip()),
                        )
                        col_exists = cur.fetchone()[0]

                        if col_exists:
                            cur.execute(
                                psycopg.sql.SQL("SELECT MAX({}) FROM {}")
                                .format(safe_updated_col, safe_ident)
                            )
                            latest_update = cur.fetchone()[0]
                            st.write(f"Latest `{updated_at_col.strip()}` value: `{latest_update}`")

                            now_utc = datetime.now(timezone.utc)
                            st.caption(
                                "Last checked at "
                                f"{now_utc.isoformat(timespec='seconds')}"
                            )
                        else:
                            st.warning(
                                f"Column `{updated_at_col.strip()}` not found on "
                                f"`{schema_name.strip()}.{table_name.strip()}`."
                            )

        except ImportError:
            st.error("Missing dependency: psycopg. Install requirements and rerun.")
        except Exception as exc:
            st.error(f"DB health check failed: {exc}")
