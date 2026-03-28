"""PawPal+ Streamlit UI — integrates with pawpal_system.py backend."""

from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — never miss a walk, feeding, or vet visit.")

# ---------------------------------------------------------------------------
# Session-state initialization (runs once per browser session)
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None  # set up after owner form
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ---------------------------------------------------------------------------
# Sidebar — Owner & Pet Setup
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("👤 Owner Setup")
    owner_name = st.text_input("Your name", value="Alex")

    if st.button("Create / Reset Owner"):
        st.session_state.owner = Owner(owner_name)
        st.session_state.scheduler = Scheduler(st.session_state.owner)
        st.success(f"Owner '{owner_name}' ready!")

    if st.session_state.owner:
        st.divider()
        st.header("🐶 Add a Pet")
        pet_name = st.text_input("Pet name", value="Buddy")
        species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Rabbit", "Other"])
        if st.button("Add Pet"):
            existing = st.session_state.owner.find_pet(pet_name)
            if existing:
                st.warning(f"'{pet_name}' already exists.")
            else:
                st.session_state.owner.add_pet(Pet(pet_name, species))
                st.success(f"{pet_name} the {species} added!")

        # List current pets
        if st.session_state.owner.pets:
            st.divider()
            st.subheader("Your Pets")
            for pet in st.session_state.owner.pets:
                st.write(f"• **{pet.name}** ({pet.species}) — {len(pet.tasks)} task(s)")

# ---------------------------------------------------------------------------
# Main area — only active once an owner exists
# ---------------------------------------------------------------------------

if st.session_state.owner is None:
    st.info("👈 Enter your name in the sidebar and click **Create / Reset Owner** to get started.")
    st.stop()

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

st.divider()

# ---------------------------------------------------------------------------
# Add Tasks
# ---------------------------------------------------------------------------

st.subheader("➕ Add a Task")

if not owner.pets:
    st.warning("Add at least one pet in the sidebar before scheduling tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            target_pet = st.selectbox("For pet", [p.name for p in owner.pets])
            description = st.text_input("Task description", value="Morning walk")
        with col2:
            task_time = st.time_input("Time", value=None)
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

        priority = st.select_slider(
            "Priority", options=["Low", "Medium", "High"], value="Medium"
        )

        submitted = st.form_submit_button("Add Task")
        if submitted:
            if not description.strip():
                st.error("Please enter a task description.")
            elif task_time is None:
                st.error("Please select a time.")
            else:
                pet = owner.find_pet(target_pet)
                time_str = task_time.strftime("%H:%M")
                new_task = Task(
                    description=description.strip(),
                    time=time_str,
                    frequency=frequency,
                    priority=priority,
                    due_date=date.today(),
                )
                pet.add_task(new_task)
                st.success(f"Task '{description}' added to {target_pet} at {time_str}.")

st.divider()

# ---------------------------------------------------------------------------
# Schedule Display
# ---------------------------------------------------------------------------

st.subheader("📅 Today's Schedule")

sort_mode = st.radio(
    "Sort by", ["Time", "Priority → Time"], horizontal=True, label_visibility="collapsed"
)

all_tasks = owner.get_all_tasks()

if not all_tasks:
    st.info("No tasks yet. Add some above!")
else:
    if sort_mode == "Time":
        sorted_tasks = scheduler.sort_by_time(all_tasks)
    else:
        sorted_tasks = scheduler.sort_by_priority_then_time(all_tasks)

    # Conflict warnings
    conflicts = scheduler.detect_conflicts()
    for warning in conflicts:
        st.warning(warning)

    # Build display table
    priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
    rows = []
    for task in sorted_tasks:
        # Find which pet owns this task
        owner_pet = "Unknown"
        for pet in owner.pets:
            if task in pet.tasks:
                owner_pet = pet.name
                break
        rows.append(
            {
                "Status": "✓" if task.completed else "○",
                "Priority": priority_icon.get(task.priority, "") + " " + task.priority,
                "Time": task.time,
                "Task": task.description,
                "Pet": owner_pet,
                "Frequency": task.frequency,
            }
        )

    st.table(rows)

    # Mark complete
    st.divider()
    st.subheader("✅ Mark a Task Complete")
    incomplete = [t for t in all_tasks if not t.completed]
    if incomplete:
        task_labels = [
            f"{t.time} — {t.description}"
            for t in incomplete
        ]
        selected_label = st.selectbox("Select task to complete", task_labels)
        selected_task = incomplete[task_labels.index(selected_label)]

        if st.button("Mark Complete"):
            # Find owning pet
            owning_pet = None
            for pet in owner.pets:
                if selected_task in pet.tasks:
                    owning_pet = pet
                    break
            if owning_pet:
                next_task = scheduler.mark_task_complete(selected_task, owning_pet)
                if next_task:
                    st.success(
                        f"'{selected_task.description}' done! "
                        f"Next occurrence scheduled for {next_task.due_date}."
                    )
                else:
                    st.success(f"'{selected_task.description}' marked complete!")
                st.rerun()
    else:
        st.success("All tasks for today are complete! 🎉")

# ---------------------------------------------------------------------------
# Filter Panel
# ---------------------------------------------------------------------------

st.divider()
st.subheader("🔍 Filter Tasks")

if owner.pets:
    filter_pet = st.selectbox("Show tasks for pet", ["All"] + [p.name for p in owner.pets])
    if filter_pet != "All":
        filtered = scheduler.filter_by_pet(filter_pet)
        if filtered:
            rows = [
                {
                    "Status": "✓" if t.completed else "○",
                    "Time": t.time,
                    "Task": t.description,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                }
                for t in scheduler.sort_by_time(filtered)
            ]
            st.table(rows)
        else:
            st.info(f"No tasks for {filter_pet}.")
