import streamlit as st

st.set_page_config(page_title="To-Do App", page_icon="✅", layout="centered")

st.title("Jesse rules")
st.caption("A simple Streamlit to-do list with add, complete, and delete features.")

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
