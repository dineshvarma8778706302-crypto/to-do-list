import os
import streamlit as st
from datetime import datetime
from google import genai

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI To-Do List",
    page_icon="🤖",
    layout="centered"
)

# Sidebar for API Key Management
with st.sidebar:
    st.header("🔑 Configuration")
    user_api_key = st.text_input("Enter Gemini API Key", type="password")
    if user_api_key:
        os.environ["GEMINI_API_KEY"] = user_api_key

# Retrieve Key from Sidebar or Environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Create Gemini client
client = None
gemini_ready = False
gemini_error = None

if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        gemini_ready = True
    except Exception as e:
        client = None
        gemini_ready = False
        gemini_error = str(e)


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.title {
    text-align: center;
    font-size: 45px;
    font-weight: bold;
}

.subtitle {
    text-align: center;
    color: gray;
    margin-bottom: 30px;
}

.task-card {
    padding: 18px;
    border-radius: 12px;
    background-color: #f5f5f5;
    border: 1px solid #dddddd;
    margin-bottom: 10px;
}

.ai-card {
    padding: 18px;
    border-radius: 12px;
    background-color: #eef6ff;
    border-left: 5px solid #4a90e2;
    margin-bottom: 20px;
}

.completed {
    text-decoration: line-through;
    color: gray;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0


# ============================================================
# ADD TASK
# ============================================================

def add_task(title):

    st.session_state.task_counter += 1

    st.session_state.tasks.append({
        "id": st.session_state.task_counter,
        "title": title,
        "completed": False,
        "created": datetime.now().strftime(
            "%d %b %Y, %I:%M %p"
        ),
        "ai_benefits": None
    })


# ============================================================
# DELETE TASK
# ============================================================

def delete_task(task_id):

    st.session_state.tasks = [
        task
        for task in st.session_state.tasks
        if task["id"] != task_id
    ]


# ============================================================
# GEMINI FUNCTION
# ============================================================

def generate_benefits(task):

    if not GEMINI_API_KEY:
        return """
⚠️ **Gemini API key is missing.**

Please enter your Gemini API key in the sidebar configuration on the left.
"""

    if not gemini_ready:
        return f"""
❌ **Gemini client could not start.**

Error:
{gemini_error}
"""

    try:
        prompt = f"""
You are an AI productivity coach.

The user has just completed this task:
"{task}"

Explain the benefits of completing this task.

Give the answer in this format:

🎯 Benefits
- Give 2 or 3 practical benefits.

🧠 Skills / Habits Improved
- Explain what skills, habits, discipline, knowledge, or productivity abilities are improved.

🚀 Positive Impact
- Explain briefly how completing this task contributes to the user's personal, academic, career, or daily goals.

Keep the response concise.
Be positive and motivating.
Do not repeat the task unnecessarily.
"""

        # Model updated to gemini-3.5-flash
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:
        return f"""
❌ **Gemini Error**

{str(e)}

### Check these:
1. Is your API key correct?
2. Is the Gemini API enabled for the key?
3. Does your API key have access to Gemini models?
4. Is your internet connection working?
"""


# ============================================================
# COMPLETE TASK
# ============================================================

def complete_task(task_id):

    for task in st.session_state.tasks:

        if task["id"] == task_id:

            # First completion
            if not task["completed"]:

                task["completed"] = True

                # Generate Gemini response
                if not task["ai_benefits"]:

                    with st.spinner(
                        "🤖 Gemini is analyzing your achievement..."
                    ):

                        task["ai_benefits"] = generate_benefits(
                            task["title"]
                        )

            # If already completed, mark incomplete
            else:

                task["completed"] = False


# ============================================================
# CLEAR COMPLETED
# ============================================================

def clear_completed():

    st.session_state.tasks = [
        task
        for task in st.session_state.tasks
        if not task["completed"]
    ]


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="title">🤖 AI To-Do List</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
    Complete your tasks and Gemini explains why
    your achievement matters 🚀
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# ADD TASK FORM
# ============================================================

st.subheader("➕ Add a Task")

with st.form(
    "add_task",
    clear_on_submit=True
):

    task_input = st.text_input(
        "Task",
        placeholder="Example: Study Machine Learning for 2 hours"
    )

    add = st.form_submit_button(
        "➕ Add Task",
        use_container_width=True
    )

    if add:

        if task_input.strip():

            add_task(task_input.strip())

            st.success("Task added successfully!")

            st.rerun()

        else:

            st.warning("Please enter a task.")


# ============================================================
# STATISTICS
# ============================================================

st.divider()

st.subheader("📊 Progress")

total = len(st.session_state.tasks)

completed = sum(
    task["completed"]
    for task in st.session_state.tasks
)

pending = total - completed


col1, col2, col3 = st.columns(3)

with col1:
    st.metric("📋 Total", total)

with col2:
    st.metric("✅ Completed", completed)

with col3:
    st.metric("⏳ Pending", pending)


if total > 0:

    progress = completed / total

    st.progress(progress)

    st.caption(f"{int(progress * 100)}% completed")


# ============================================================
# FILTER
# ============================================================

st.divider()

st.subheader("📋 Your Tasks")

filter_option = st.selectbox(
    "Filter tasks",
    [
        "All",
        "Pending",
        "Completed"
    ]
)


if filter_option == "Pending":

    tasks = [
        task
        for task in st.session_state.tasks
        if not task["completed"]
    ]

elif filter_option == "Completed":

    tasks = [
        task
        for task in st.session_state.tasks
        if task["completed"]
    ]

else:

    tasks = st.session_state.tasks


# ============================================================
# DISPLAY TASKS
# ============================================================

if not tasks:

    if total == 0:

        st.info("🎯 No tasks yet. Add your first task!")

    elif filter_option == "Pending":

        st.success("🎉 Amazing! All tasks are completed!")

    else:

        st.info("No tasks found.")

else:

    for task in tasks:

        col1, col2, col3 = st.columns([0.6, 5, 0.8])


        # ----------------------------------------------------
        # CHECKBOX
        # ----------------------------------------------------

        with col1:

            checked = st.checkbox(
                "Done",
                value=task["completed"],
                key=f"checkbox_{task['id']}",
                label_visibility="collapsed"
            )

            if checked != task["completed"]:

                complete_task(task["id"])

                st.rerun()


        # ----------------------------------------------------
        # TASK DETAILS
        # ----------------------------------------------------

        with col2:

            if task["completed"]:

                st.markdown(
                    f"""
                    <div class="task-card">
                    <div class="completed">
                    <b>✅ {task["title"]}</b>
                    </div>
                    <small>Completed: {task["created"]}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div class="task-card">
                    <b>📌 {task["title"]}</b>
                    <br><br>
                    <small>Created: {task["created"]}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


        # ----------------------------------------------------
        # DELETE BUTTON
        # ----------------------------------------------------

        with col3:

            if st.button("🗑️", key=f"delete_{task['id']}"):

                delete_task(task["id"])

                st.rerun()


        # ----------------------------------------------------
        # GEMINI INSIGHT
        # ----------------------------------------------------

        if task["completed"]:

            st.markdown("### 🤖 Gemini Achievement Insight")

            st.markdown(
                f"""
                <div class="ai-card">
                {task["ai_benefits"]}
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# BOTTOM BUTTONS
# ============================================================

st.divider()

col1, col2 = st.columns(2)


with col1:

    if st.button("🧹 Clear Completed", use_container_width=True):

        clear_completed()

        st.rerun()


with col2:

    if st.button("❌ Clear All", use_container_width=True):

        st.session_state.tasks = []

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption("🚀 AI To-Do List • Streamlit + Gemini 3.5 Flash")