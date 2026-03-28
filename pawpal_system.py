"""PawPal+ backend logic: Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    time: str  # "HH:MM" 24-hour format
    frequency: str = "once"  # "once", "daily", "weekly"
    completed: bool = False
    priority: str = "Medium"  # "Low", "Medium", "High"
    due_date: Optional[date] = None

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete and return next occurrence for recurring tasks.

        Returns a new Task for the next occurrence if frequency is daily/weekly,
        otherwise returns None.
        """
        self.completed = True
        if self.frequency == "daily":
            next_date = (self.due_date or date.today()) + timedelta(days=1)
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                priority=self.priority,
                due_date=next_date,
            )
        if self.frequency == "weekly":
            next_date = (self.due_date or date.today()) + timedelta(weeks=1)
            return Task(
                description=self.description,
                time=self.time,
                frequency=self.frequency,
                priority=self.priority,
                due_date=next_date,
            )
        return None

    def __str__(self) -> str:
        """Return human-readable task summary."""
        status = "✓" if self.completed else "○"
        priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(
            self.priority, "○"
        )
        return (
            f"[{status}] {priority_icon} {self.time} - {self.description} "
            f"({self.frequency})"
        )


@dataclass
class Pet:
    """Represents a pet with its care tasks."""

    name: str
    species: str
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove a task by description. Returns True if found and removed."""
        for i, task in enumerate(self.tasks):
            if task.description == description:
                self.tasks.pop(i)
                return True
        return False

    def __str__(self) -> str:
        """Return human-readable pet summary."""
        return f"{self.name} ({self.species}) — {len(self.tasks)} task(s)"


class Owner:
    """Represents a pet owner who manages multiple pets."""

    def __init__(self, name: str) -> None:
        """Initialize an owner with a name and empty pet list."""
        self.name = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's care roster."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Retrieve every task across all pets."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Retrieve all tasks for a specific pet by name."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return list(pet.tasks)
        return []

    def find_pet(self, pet_name: str) -> Optional[Pet]:
        """Find and return a Pet by name, or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def __str__(self) -> str:
        """Return human-readable owner summary."""
        return f"Owner: {self.name} — {len(self.pets)} pet(s)"


class Scheduler:
    """Organizes and manages pet care tasks across all pets for an owner."""

    PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

    def __init__(self, owner: Owner) -> None:
        """Initialize the scheduler with an owner."""
        self.owner = owner

    def get_todays_schedule(self) -> list[Task]:
        """Return all incomplete tasks sorted by time for today."""
        tasks = self.owner.get_all_tasks()
        return self.sort_by_time([t for t in tasks if not t.completed])

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks chronologically by their HH:MM time string."""
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority_then_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority (High first), then by time within each priority."""
        return sorted(
            tasks,
            key=lambda t: (self.PRIORITY_ORDER.get(t.priority, 1), t.time),
        )

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks belonging to a specific pet."""
        return self.owner.get_tasks_for_pet(pet_name)

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks matching the given completion status."""
        return [t for t in self.owner.get_all_tasks() if t.completed == completed]

    def detect_conflicts(self) -> list[str]:
        """Detect tasks scheduled at exactly the same time across all pets.

        Returns a list of warning strings describing each conflict found.
        """
        all_tasks = [t for t in self.owner.get_all_tasks() if not t.completed]
        seen: dict[str, Task] = {}
        warnings = []
        for task in all_tasks:
            if task.time in seen:
                other = seen[task.time]
                warnings.append(
                    f"⚠️ Conflict at {task.time}: "
                    f'"{task.description}" and "{other.description}"'
                )
            else:
                seen[task.time] = task
        return warnings

    def mark_task_complete(self, task: Task, pet: Pet) -> Optional[Task]:
        """Mark a task complete and schedule its next occurrence if recurring.

        Adds the next occurrence back to the pet's task list automatically.
        Returns the new Task if one was created, else None.
        """
        next_task = task.mark_complete()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task
