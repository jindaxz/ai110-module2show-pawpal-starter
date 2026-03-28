"""Automated test suite for PawPal+ system."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def basic_owner() -> Owner:
    """Return an Owner with two pets and a handful of tasks."""
    owner = Owner("Alex")

    buddy = Pet("Buddy", "Dog")
    buddy.add_task(Task("Morning walk", "07:30", frequency="daily", priority="High", due_date=date.today()))
    buddy.add_task(Task("Breakfast", "08:00", frequency="daily", priority="High", due_date=date.today()))
    buddy.add_task(Task("Evening walk", "18:00", frequency="daily", priority="Low", due_date=date.today()))

    whiskers = Pet("Whiskers", "Cat")
    whiskers.add_task(Task("Playtime", "16:00", frequency="daily", priority="Low", due_date=date.today()))
    whiskers.add_task(Task("Vet appointment", "10:30", frequency="once", priority="High", due_date=date.today()))

    owner.add_pet(buddy)
    owner.add_pet(whiskers)
    return owner


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


class TestTaskCompletion:
    def test_mark_complete_changes_status(self):
        """Calling mark_complete() sets completed to True."""
        task = Task("Walk", "09:00")
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_mark_complete_once_returns_none(self):
        """One-time tasks produce no next occurrence."""
        task = Task("Vet visit", "10:00", frequency="once")
        result = task.mark_complete()
        assert result is None

    def test_mark_complete_daily_returns_next_day(self):
        """Daily tasks return a new task due tomorrow."""
        today = date.today()
        task = Task("Feed", "08:00", frequency="daily", due_date=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.completed is False
        assert next_task.description == "Feed"

    def test_mark_complete_weekly_returns_next_week(self):
        """Weekly tasks return a new task due seven days later."""
        today = date.today()
        task = Task("Flea med", "09:00", frequency="weekly", due_date=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------


class TestPet:
    def test_add_task_increases_count(self):
        """Adding a task increases the pet's task list length."""
        pet = Pet("Buddy", "Dog")
        assert len(pet.tasks) == 0
        pet.add_task(Task("Walk", "08:00"))
        assert len(pet.tasks) == 1
        pet.add_task(Task("Feed", "09:00"))
        assert len(pet.tasks) == 2

    def test_remove_task_by_description(self):
        """Removing a task by description reduces the list."""
        pet = Pet("Buddy", "Dog")
        pet.add_task(Task("Walk", "08:00"))
        pet.add_task(Task("Feed", "09:00"))
        removed = pet.remove_task("Walk")
        assert removed is True
        assert len(pet.tasks) == 1
        assert pet.tasks[0].description == "Feed"

    def test_remove_nonexistent_task_returns_false(self):
        """Removing a task that doesn't exist returns False."""
        pet = Pet("Buddy", "Dog")
        assert pet.remove_task("Nonexistent") is False


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------


class TestOwner:
    def test_add_pet_increases_count(self):
        """Adding a pet increases the owner's pet list."""
        owner = Owner("Alex")
        assert len(owner.pets) == 0
        owner.add_pet(Pet("Buddy", "Dog"))
        assert len(owner.pets) == 1

    def test_get_all_tasks_aggregates_across_pets(self, basic_owner):
        """get_all_tasks() returns tasks from all pets combined."""
        total = sum(len(p.tasks) for p in basic_owner.pets)
        assert len(basic_owner.get_all_tasks()) == total

    def test_find_pet_returns_correct_pet(self, basic_owner):
        """find_pet() returns the correct Pet object."""
        pet = basic_owner.find_pet("Buddy")
        assert pet is not None
        assert pet.name == "Buddy"

    def test_find_pet_case_insensitive(self, basic_owner):
        """find_pet() is case-insensitive."""
        assert basic_owner.find_pet("buddy") is not None
        assert basic_owner.find_pet("BUDDY") is not None

    def test_find_pet_missing_returns_none(self, basic_owner):
        """find_pet() returns None for unknown names."""
        assert basic_owner.find_pet("Nemo") is None


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------


class TestSchedulerSorting:
    def test_sort_by_time_chronological_order(self, basic_owner):
        """Tasks are returned in chronological order."""
        scheduler = Scheduler(basic_owner)
        schedule = scheduler.get_todays_schedule()
        times = [t.time for t in schedule]
        assert times == sorted(times)

    def test_sort_by_time_out_of_order_input(self):
        """sort_by_time() handles tasks added in reverse order."""
        owner = Owner("Alex")
        pet = Pet("Buddy", "Dog")
        pet.add_task(Task("C", "18:00"))
        pet.add_task(Task("A", "07:00"))
        pet.add_task(Task("B", "12:00"))
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        result = scheduler.sort_by_time(owner.get_all_tasks())
        assert [t.time for t in result] == ["07:00", "12:00", "18:00"]

    def test_sort_by_priority_then_time(self, basic_owner):
        """High-priority tasks come before Medium, then Low."""
        scheduler = Scheduler(basic_owner)
        result = scheduler.sort_by_priority_then_time(basic_owner.get_all_tasks())
        priorities = [t.priority for t in result]
        # All High entries should precede Low entries
        first_low = next((i for i, p in enumerate(priorities) if p == "Low"), len(priorities))
        last_high = max((i for i, p in enumerate(priorities) if p == "High"), default=-1)
        assert last_high < first_low


class TestSchedulerFiltering:
    def test_filter_by_pet_returns_only_that_pets_tasks(self, basic_owner):
        """filter_by_pet() returns tasks exclusively for the named pet."""
        scheduler = Scheduler(basic_owner)
        buddy_tasks = scheduler.filter_by_pet("Buddy")
        buddy = basic_owner.find_pet("Buddy")
        assert len(buddy_tasks) == len(buddy.tasks)

    def test_filter_by_status_incomplete(self, basic_owner):
        """filter_by_status(False) returns only incomplete tasks."""
        scheduler = Scheduler(basic_owner)
        incomplete = scheduler.filter_by_status(completed=False)
        assert all(not t.completed for t in incomplete)

    def test_filter_by_status_completed(self, basic_owner):
        """filter_by_status(True) returns only completed tasks."""
        scheduler = Scheduler(basic_owner)
        # Complete one task first
        task = basic_owner.pets[0].tasks[0]
        task.mark_complete()
        completed = scheduler.filter_by_status(completed=True)
        assert len(completed) == 1
        assert completed[0].completed is True


class TestConflictDetection:
    def test_no_conflict_unique_times(self, basic_owner):
        """No warnings when all task times are unique."""
        scheduler = Scheduler(basic_owner)
        assert scheduler.detect_conflicts() == []

    def test_detects_same_time_conflict(self):
        """detect_conflicts() flags two tasks at the same time."""
        owner = Owner("Alex")
        pet_a = Pet("Dog", "Dog")
        pet_a.add_task(Task("Walk", "08:00"))
        pet_b = Pet("Cat", "Cat")
        pet_b.add_task(Task("Feed", "08:00"))
        owner.add_pet(pet_a)
        owner.add_pet(pet_b)
        scheduler = Scheduler(owner)
        warnings = scheduler.detect_conflicts()
        assert len(warnings) == 1
        assert "08:00" in warnings[0]

    def test_no_conflict_for_completed_tasks(self):
        """Completed tasks are excluded from conflict checking."""
        owner = Owner("Alex")
        pet = Pet("Buddy", "Dog")
        t1 = Task("Walk", "08:00")
        t2 = Task("Feed", "08:00")
        t1.mark_complete()  # mark one done
        pet.add_task(t1)
        pet.add_task(t2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []


class TestRecurringTaskIntegration:
    def test_mark_task_complete_creates_next_occurrence(self):
        """Completing a daily task via Scheduler adds a new task to the pet."""
        owner = Owner("Alex")
        pet = Pet("Buddy", "Dog")
        today = date.today()
        task = Task("Walk", "08:00", frequency="daily", due_date=today)
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)

        initial_count = len(pet.tasks)
        next_task = scheduler.mark_task_complete(task, pet)

        assert next_task is not None
        assert len(pet.tasks) == initial_count + 1
        assert next_task.due_date == today + timedelta(days=1)

    def test_empty_pet_schedule(self):
        """Scheduler handles a pet with no tasks gracefully."""
        owner = Owner("Alex")
        owner.add_pet(Pet("EmptyPet", "Fish"))
        scheduler = Scheduler(owner)
        assert scheduler.get_todays_schedule() == []
        assert scheduler.detect_conflicts() == []
