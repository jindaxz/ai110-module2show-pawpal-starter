"""CLI demo script for PawPal+ — verifies backend logic in the terminal."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule(title: str, tasks: list) -> None:
    """Print a formatted schedule section."""
    print(f"\n{'=' * 50}")
    print(f"  {title}")
    print("=" * 50)
    if not tasks:
        print("  (no tasks)")
    for task in tasks:
        print(f"  {task}")


def main() -> None:
    """Run the PawPal+ demo."""
    # --- Build the data model ---
    owner = Owner("Alex")

    buddy = Pet("Buddy", "Dog")
    buddy.add_task(Task("Morning walk", "07:30", frequency="daily", priority="High", due_date=date.today()))
    buddy.add_task(Task("Breakfast feeding", "08:00", frequency="daily", priority="High", due_date=date.today()))
    buddy.add_task(Task("Evening walk", "18:00", frequency="daily", priority="High", due_date=date.today()))
    buddy.add_task(Task("Flea medication", "09:00", frequency="weekly", priority="Medium", due_date=date.today()))

    whiskers = Pet("Whiskers", "Cat")
    whiskers.add_task(Task("Breakfast feeding", "08:00", frequency="daily", priority="High", due_date=date.today()))  # intentional conflict
    whiskers.add_task(Task("Playtime", "16:00", frequency="daily", priority="Low", due_date=date.today()))
    whiskers.add_task(Task("Vet appointment", "10:30", frequency="once", priority="High", due_date=date.today()))

    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    scheduler = Scheduler(owner)

    print(f"\nWelcome to PawPal+!  Owner: {owner.name}")
    print(f"Pets: {', '.join(p.name for p in owner.pets)}")

    # --- Today's schedule (sorted by time) ---
    print_schedule("TODAY'S SCHEDULE (by time)", scheduler.get_todays_schedule())

    # --- Priority-first schedule ---
    all_tasks = owner.get_all_tasks()
    print_schedule(
        "TODAY'S SCHEDULE (priority first)",
        scheduler.sort_by_priority_then_time(all_tasks),
    )

    # --- Filter by pet ---
    print_schedule("BUDDY'S TASKS", scheduler.filter_by_pet("Buddy"))
    print_schedule("WHISKERS'S TASKS", scheduler.filter_by_pet("Whiskers"))

    # --- Conflict detection ---
    print("\n" + "=" * 50)
    print("  CONFLICT CHECK")
    print("=" * 50)
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts detected.")

    # --- Mark a daily task complete and verify recurrence ---
    print("\n" + "=" * 50)
    print("  RECURRING TASK DEMO")
    print("=" * 50)
    morning_walk = buddy.tasks[0]
    print(f"  Before: {morning_walk}")
    next_task = scheduler.mark_task_complete(morning_walk, buddy)
    print(f"  After marking complete: {morning_walk}")
    if next_task:
        print(f"  Next occurrence created: {next_task}")

    # --- Completed vs incomplete ---
    incomplete = scheduler.filter_by_status(completed=False)
    completed = scheduler.filter_by_status(completed=True)
    print(f"\n  Incomplete tasks: {len(incomplete)}")
    print(f"  Completed tasks:  {len(completed)}")


if __name__ == "__main__":
    main()
