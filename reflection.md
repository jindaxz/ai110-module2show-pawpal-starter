# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I identified four classes from the start: `Task`, `Pet`, `Owner`, and `Scheduler`.

- **Task** holds a single care activity — its description, scheduled time (HH:MM), frequency (once/daily/weekly), completion status, priority level, and due date. I used a Python dataclass so attributes are declared clearly with default values.
- **Pet** groups tasks under a named animal. It owns `add_task()` and `remove_task()` so the pet itself manages its own care list.
- **Owner** aggregates pets and provides convenience methods (`get_all_tasks()`, `find_pet()`) so the Scheduler never has to iterate over pets directly.
- **Scheduler** is the algorithmic "brain" — it takes an `Owner` reference and exposes sorting, filtering, conflict detection, and recurrence logic without storing any mutable state of its own.

Three core actions I identified from the scenario:
1. Add a pet and schedule care tasks for it
2. View today's schedule sorted by time or priority
3. Receive a warning when two tasks overlap at the same time slot

**b. Design changes**

During implementation I made two meaningful changes:

1. **Added `due_date` to `Task`** — my initial sketch only had `time` (the HH:MM clock time). When implementing recurring tasks I realized I needed a calendar date too, so that `timedelta` could compute the next occurrence's calendar date independently of the clock time.

2. **Moved `mark_task_complete` into `Scheduler` rather than leaving it on `Task`** — originally `Task.mark_complete()` handled everything. But the recurrence logic requires adding a new task back to a `Pet`, which `Task` shouldn't know about. Splitting the work — `Task.mark_complete()` produces the next `Task` object, `Scheduler.mark_task_complete()` decides where to put it — kept responsibilities clean.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:
- **Clock time** — tasks are sorted chronologically using HH:MM string comparison (lexicographic order works correctly for zero-padded 24-hour times)
- **Priority level** — High / Medium / Low; used as a secondary sort key when the user wants priority-first ordering
- **Completion status** — completed tasks are excluded from "today's schedule" and from conflict checks, so finished work doesn't pollute the view
- **Frequency** — once / daily / weekly drives the recurrence engine

I decided time was the primary sort key for the default view because a pet owner's day is structured around the clock, not an abstract priority number. Priority-first sorting is offered as an alternative view for when the owner needs to triage.

**b. Tradeoffs**

**Exact-time conflict detection only.** The scheduler flags two tasks as a conflict only when their `time` strings are identical (e.g., both at "08:00"). It does not model task duration, so two tasks at 08:00 and 08:05 would not be flagged even if the first task takes 30 minutes.

This tradeoff is reasonable here because: (1) `Task` intentionally omits a duration field to keep the model simple, (2) pet care tasks like feedings and walks rarely have overlapping windows at the minute level in real life, and (3) adding duration-based overlap detection would require converting time strings to `datetime` objects and range-intersection logic — useful, but out of scope for the core scheduler.

---

## 3. AI Collaboration

**a. How I used AI**

I used AI (Claude Code via VS Code) across all phases:

- **Design brainstorming** — I described the four-class architecture and asked for a Mermaid.js class diagram. The AI generated a correct diagram that I used to verify my attribute choices before writing any code.
- **Skeleton generation** — I asked for Python dataclass stubs matching my UML; the AI produced clean stubs that I then filled in.
- **Recurrence logic** — I prompted: "If a daily task is marked complete, how do I calculate tomorrow's date using Python `timedelta`?" The AI suggested `date.today() + timedelta(days=1)`, which I adapted to use the task's own `due_date` rather than always `today()`, making it more accurate for tasks added in advance.
- **Test generation** — I asked: "What edge cases are most important for a pet scheduler with sorting and recurring tasks?" This produced a useful list: empty schedules, case-insensitive lookup, completed tasks excluded from conflict checks, weekly vs. daily recurrence differences. I used this list directly to write the 23 test functions.

The prompts that were most helpful were specific and referenced existing code: "Based on my `Task` class in `pawpal_system.py`, how should `mark_complete()` handle the weekly frequency?" Vague prompts produced generic advice; targeted prompts produced directly usable code.

**b. Judgment and verification**

When generating the conflict detection logic, the AI initially suggested using a list and comparing every pair of tasks (O(n²)). I recognized this as unnecessarily slow for a scheduler that could eventually handle hundreds of tasks, and asked for a dictionary-based approach instead. The AI provided the O(n) single-pass solution I used. I verified correctness by manually tracing through the logic with two tasks at "08:00" and confirming the warning string was generated, then confirmed that a completed task at "08:00" plus an incomplete task at "08:00" did *not* trigger a warning (since completed tasks are filtered first).

---

## 4. Testing and Verification

**a. What I tested**

23 tests across 7 test classes:

- **Task completion** — `mark_complete()` sets `completed = True`; once/daily/weekly frequencies return the correct next-occurrence task (or `None`)
- **Pet task management** — `add_task()` increases count; `remove_task()` decreases count; removing a nonexistent task returns `False`
- **Owner aggregation** — `get_all_tasks()` combines tasks from all pets; `find_pet()` is case-insensitive and returns `None` for unknown names
- **Sorting correctness** — tasks added out of order are returned chronologically; priority sort puts all High tasks before Low tasks
- **Filtering** — pet-name filter returns only that pet's tasks; status filter returns only complete or only incomplete tasks
- **Conflict detection** — flags duplicate times; ignores completed tasks; returns empty list when all times are unique
- **Recurrence integration** — `Scheduler.mark_task_complete()` adds the next occurrence to the pet's task list automatically

These tests matter because they cover the three core user actions and the two algorithmic features (conflict detection and recurrence) that have the highest potential for subtle bugs.

**b. Confidence**

**★★★★☆** — All 23 tests pass. I'm confident in correctness for the features implemented. The main gaps I would address next:

- **Duration-based conflict detection** — the current exact-time check misses overlapping windows
- **Multi-day schedule view** — filtering by `due_date` to show tomorrow's tasks
- **Persistence** — tasks reset when the Streamlit session ends; adding JSON save/load would make the app practical

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the separation of concerns between `Task`, `Pet`, `Owner`, and `Scheduler`. Each class has a single, clear job. `Task` knows nothing about `Pet`; `Pet` knows nothing about `Scheduler`. This meant I could write and test each class independently, and changing the recurrence logic in `Scheduler` didn't require touching `Task` or `Pet` at all.

**b. What I would improve**

I would add task duration as a field and upgrade conflict detection to use time-range intersection instead of exact-time matching. I would also add a `save_to_json` / `load_from_json` pair on `Owner` so data persists between Streamlit sessions — the current session-state approach is convenient but loses all data on refresh.

**c. Key takeaway**

The most important lesson from this project was the value of designing before coding. Spending time on the UML and identifying the four classes and their relationships upfront meant that when I wrote `Scheduler`, I already knew it should receive an `Owner` (not individual pets or tasks) — which made the API clean and testable from the start. AI tools accelerated every phase, but the architectural decisions — what each class is responsible for, what it should *not* know about — required human judgment that the AI could not substitute.
