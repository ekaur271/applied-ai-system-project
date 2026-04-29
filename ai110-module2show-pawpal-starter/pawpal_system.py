from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
import json
import os

DATA_FILE = "data.json"

# ─── Constants ────────────────────────────────────────────────────────────────

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

TIME_PREF_WINDOWS = {
    "morning":   ("08:00", "12:00"),
    "afternoon": ("12:00", "17:00"),
    "evening":   ("17:00", "22:00"),
}

ENERGY_CURVE = {
    "dog":   {"exercise": "morning",   "nutrition": "morning", "hygiene": "afternoon",
              "enrichment": "evening", "medication": "morning"},
    "cat":   {"exercise": "evening",   "nutrition": "morning", "hygiene": "afternoon",
              "enrichment": "evening", "medication": "morning"},
    "other": {"exercise": "morning",   "nutrition": "morning", "hygiene": "afternoon",
              "enrichment": "afternoon","medication": "morning"},
}

BATCH_MAX_MINUTES = 60

FREQUENCY_DELTAS = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


# ─── Utilities ────────────────────────────────────────────────────────────────

def minutes_to_time(minutes: int) -> str:
    """Convert total minutes since midnight to a HH:MM string."""
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


def time_to_minutes(t: str) -> int:
    """Convert a HH:MM string to total minutes since midnight."""
    h, m = map(int, t.split(":"))
    return h * 60 + m


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Task:
    name: str
    task_type: str
    priority: str           # "high", "medium", "low"
    duration: int           # minutes
    frequency: str          # "daily", "weekly", "as needed"
    time_preference: Optional[str] = None   # "morning", "afternoon", "evening"
    status: str = "incomplete"
    due_date: Optional[str] = None          # "YYYY-MM-DD"

    def assign_priority(self, priority: str):
        """Set the priority level of this task."""
        self.priority = priority

    def assign_duration(self, duration: int):
        """Set how long this task takes in minutes."""
        self.duration = duration

    def assign_frequency(self, frequency: str):
        """Set how often this task recurs."""
        self.frequency = frequency

    def assign_time_preference(self, time_preference: str):
        """Set the preferred time of day for this task."""
        self.time_preference = time_preference

    def mark_complete(self):
        """Mark this task as complete."""
        self.status = "complete"

    def mark_incomplete(self):
        """Mark this task as incomplete."""
        self.status = "incomplete"

    def next_occurrence(self, from_date: str) -> Optional["Task"]:
        """Return a new incomplete Task due on the next occurrence based on frequency."""
        delta = FREQUENCY_DELTAS.get(self.frequency)
        if delta is None:
            return None
        next_date = datetime.strptime(from_date, "%Y-%m-%d").date() + delta
        return Task(
            name=self.name, task_type=self.task_type, priority=self.priority,
            duration=self.duration, frequency=self.frequency,
            time_preference=self.time_preference, status="incomplete",
            due_date=str(next_date),
        )

    def to_dict(self) -> dict:
        """Serialize this Task to a JSON-compatible dictionary."""
        return {
            "name": self.name, "task_type": self.task_type, "priority": self.priority,
            "duration": self.duration, "frequency": self.frequency,
            "time_preference": self.time_preference, "status": self.status,
            "due_date": self.due_date,
        }

    @staticmethod
    def from_dict(d: dict) -> "Task":
        """Deserialize a Task from a dictionary."""
        return Task(
            name=d["name"],
            task_type=d.get("task_type", d.get("type", "exercise")),  # backwards compat
            priority=d["priority"], duration=d["duration"], frequency=d["frequency"],
            time_preference=d.get("time_preference"), status=d.get("status", "incomplete"),
            due_date=d.get("due_date"),
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    care_tasks: List[Task] = field(default_factory=list)

    def add_care_task(self, task: Task):
        """Add a care task to this pet's task list."""
        self.care_tasks.append(task)

    def remove_care_task(self, task: Task):
        """Remove a care task from this pet's task list."""
        self.care_tasks.remove(task)

    def get_all_tasks(self) -> List[Task]:
        """Return all care tasks for this pet."""
        return self.care_tasks

    def update_age(self, age: int):
        """Update the pet's age."""
        self.age = age

    def to_dict(self) -> dict:
        """Serialize this Pet to a JSON-compatible dictionary."""
        return {
            "name": self.name, "species": self.species, "age": self.age,
            "care_tasks": [t.to_dict() for t in self.care_tasks],
        }

    @staticmethod
    def from_dict(d: dict) -> "Pet":
        """Deserialize a Pet from a dictionary."""
        pet = Pet(name=d["name"], species=d["species"], age=d["age"])
        pet.care_tasks = [Task.from_dict(t) for t in d.get("care_tasks", [])]
        return pet


@dataclass
class AvailabilityBlock:
    label: str
    start_time: str     # "HH:MM"
    end_time: str       # "HH:MM"
    frequency: str      # "daily", "weekdays", "weekends"

    def update_start(self, start_time: str):
        """Update the start time of this block."""
        self.start_time = start_time

    def update_end(self, end_time: str):
        """Update the end time of this block."""
        self.end_time = end_time

    def add_frequency(self, frequency: str):
        """Set how often this block recurs."""
        self.frequency = frequency

    def conflicts_with(self, start_time: str, end_time: str) -> bool:
        """Return True if the given time slot overlaps with this busy block."""
        block_start = time_to_minutes(self.start_time)
        block_end   = time_to_minutes(self.end_time)
        slot_start  = time_to_minutes(start_time)
        slot_end    = time_to_minutes(end_time)
        return not (slot_end <= block_start or slot_start >= block_end)


@dataclass
class Owner:
    name: str
    availability: List[AvailabilityBlock] = field(default_factory=list)

    def add_availability(self, block: AvailabilityBlock):
        """Add a busy time block to the owner's schedule."""
        self.availability.append(block)

    def get_free_slots(self) -> List[AvailabilityBlock]:
        """Return all availability blocks for this owner."""
        return self.availability

    def to_dict(self) -> dict:
        """Serialize this Owner to a JSON-compatible dictionary."""
        return {
            "name": self.name,
            "availability": [
                {"label": b.label, "start_time": b.start_time,
                 "end_time": b.end_time, "frequency": b.frequency}
                for b in self.availability
            ],
        }

    def save_to_json(self, pets: List[Pet], filepath: str = DATA_FILE) -> None:
        """Save owner and pets to a JSON file."""
        data = {"owner": self.to_dict(), "pets": [p.to_dict() for p in pets]}
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_from_json(filepath: str = DATA_FILE):
        """Load owner and pets from JSON. Returns (Owner, List[Pet]) or (None, []) on failure."""
        if not os.path.exists(filepath):
            return None, []
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            owner_data = data.get("owner", {})
            owner = Owner(name=owner_data["name"])
            for b in owner_data.get("availability", []):
                owner.add_availability(AvailabilityBlock(
                    label=b["label"], start_time=b["start_time"],
                    end_time=b["end_time"], frequency=b["frequency"],
                ))
            pets = [Pet.from_dict(p) for p in data.get("pets", [])]
            return owner, pets
        except (json.JSONDecodeError, KeyError):
            return None, []


@dataclass
class ScheduledTask:
    task: Task
    start_time: str     # "HH:MM"
    end_time: str       # "HH:MM"
    is_complete: bool = False
    next_task: Optional[Task] = field(default=None, repr=False)

    def mark_complete(self, on_date: Optional[str] = None):
        """Mark complete and generate the next occurrence if recurring."""
        self.is_complete = True
        self.task.mark_complete()
        if on_date:
            self.next_task = self.task.next_occurrence(on_date)

    def update_start(self, start_time: str):
        """Update the scheduled start time."""
        self.start_time = start_time

    def update_finish(self, end_time: str):
        """Update the scheduled end time."""
        self.end_time = end_time


@dataclass
class TaskBatch:
    """A group of tasks sharing a time window that can be scheduled together."""
    time_preference: str
    tasks: List[Task] = field(default_factory=list)

    @property
    def total_duration(self) -> int:
        return sum(t.duration for t in self.tasks)

    @property
    def is_complete(self) -> bool:
        return all(t.status == "complete" for t in self.tasks)

    @property
    def label(self) -> str:
        labels = {
            "morning": "Morning Routine",
            "afternoon": "Afternoon Routine",
            "evening": "Evening Routine",
        }
        return labels.get(self.time_preference, "Task Block")


# ─── DayPlan ──────────────────────────────────────────────────────────────────

class DayPlan:
    def __init__(self, plan_date: str, owner: Owner, pet: Pet):
        self.plan_date = plan_date
        self.owner = owner
        self.pet = pet
        self.scheduled_tasks: List[ScheduledTask] = []

    def add_task(self, scheduled_task: ScheduledTask):
        """Append a scheduled task to today's plan."""
        self.scheduled_tasks.append(scheduled_task)

    def get_completion_status(self) -> dict:
        """Return total, complete, and remaining task counts."""
        total = len(self.scheduled_tasks)
        complete = sum(1 for t in self.scheduled_tasks if t.is_complete)
        return {"total": total, "complete": complete, "remaining": total - complete}

    def filter_tasks(self, status: str = "all") -> List[ScheduledTask]:
        """Filter scheduled tasks by completion status: 'complete', 'incomplete', or 'all'."""
        if status == "complete":
            return [t for t in self.scheduled_tasks if t.is_complete]
        if status == "incomplete":
            return [t for t in self.scheduled_tasks if not t.is_complete]
        return self.scheduled_tasks

    def display(self):
        """Print the day's schedule as a formatted table."""
        from tabulate import tabulate

        TYPE_EMOJI = {
            "exercise": "🏃", "nutrition": "🍖", "hygiene": "🛁",
            "enrichment": "🧸", "medication": "💊",
        }
        PRIORITY_SYMBOL = {"high": "🔴", "medium": "🟡", "low": "🟢"}

        print(f"\n{'='*56}")
        print(f"  🐾 {self.pet.name}'s Schedule — {self.plan_date}")
        print(f"  👤 Owner: {self.owner.name}")
        print(f"{'='*56}")

        rows = [
            [
                "✅" if t.is_complete else "○",
                f"{t.start_time}–{t.end_time}",
                f"{TYPE_EMOJI.get(t.task.task_type, '📌')} {t.task.name}",
                f"{PRIORITY_SYMBOL.get(t.task.priority, '')} {t.task.priority}",
                f"{t.task.duration} min",
                t.task.frequency,
            ]
            for t in self.scheduled_tasks
        ]

        print(tabulate(
            rows,
            headers=["", "Time", "Task", "Priority", "Duration", "Frequency"],
            tablefmt="rounded_outline",
        ))

        s = self.get_completion_status()
        bar = ("█" * s["complete"]) + ("░" * s["remaining"])
        print(f"\n  Progress: [{bar}] {s['complete']}/{s['total']} complete\n")


# ─── Scheduler ────────────────────────────────────────────────────────────────

class Scheduler:
    def __init__(
        self,
        owner: Owner,
        pet: Pet,
        date: str,
        day_start: str = "08:00",
        day_end: str = "22:00",
    ):
        self.owner = owner
        self.pet = pet
        self.date = date
        self.day_start = day_start
        self.day_end = day_end
        self._scheduled_slots: List[tuple] = []

    def build_schedule(self) -> DayPlan:
        """Build and return a DayPlan by prioritizing and slotting all pet tasks."""
        self.fill_time_preferences()
        plan = DayPlan(self.date, self.owner, self.pet)
        for task in self.prioritize_tasks(self.pet.get_all_tasks()):
            slot = self.find_available_slot(task.duration, task.time_preference)
            if slot:
                end_min = time_to_minutes(slot) + task.duration
                scheduled = ScheduledTask(task=task, start_time=slot, end_time=minutes_to_time(end_min))
                plan.add_task(scheduled)
                self._scheduled_slots.append((time_to_minutes(slot), end_min))
        return plan

    def prioritize_tasks(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks from highest to lowest priority."""
        return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    def find_available_slot(self, duration: int, time_preference: Optional[str] = None) -> Optional[str]:
        """Find the earliest open slot of the given duration, respecting availability and time preference."""
        day_start_min = time_to_minutes(self.day_start)
        day_end_min   = time_to_minutes(self.day_end)

        if time_preference and time_preference in TIME_PREF_WINDOWS:
            pref_start, pref_end = TIME_PREF_WINDOWS[time_preference]
            search_start = max(day_start_min, time_to_minutes(pref_start))
            search_end   = min(day_end_min,   time_to_minutes(pref_end))
        else:
            search_start = day_start_min
            search_end   = day_end_min

        current = search_start
        while current + duration <= search_end:
            candidate_end = current + duration
            c_start_str   = minutes_to_time(current)
            c_end_str     = minutes_to_time(candidate_end)

            blocked_by_owner = any(
                b.conflicts_with(c_start_str, c_end_str) for b in self.owner.availability
            )
            blocked_by_scheduled = any(
                not (candidate_end <= s or current >= e) for s, e in self._scheduled_slots
            )

            if not blocked_by_owner and not blocked_by_scheduled:
                return c_start_str

            current += 15

        return None

    def fill_time_preferences(self) -> None:
        """Pet Energy Curve: assign default time preferences based on species and task type."""
        curve = ENERGY_CURVE.get(self.pet.species, ENERGY_CURVE["other"])
        for task in self.pet.get_all_tasks():
            if task.time_preference is None:
                task.time_preference = curve.get(task.task_type, "morning")

    def batch_tasks(self, tasks: List[Task]) -> List[TaskBatch]:
        """Group tasks by time preference into batches where combined duration ≤ BATCH_MAX_MINUTES."""
        groups: dict = {}
        for task in tasks:
            pref = task.time_preference or "morning"
            groups.setdefault(pref, []).append(task)

        batches: List[TaskBatch] = []
        for pref, group in groups.items():
            current_batch = TaskBatch(time_preference=pref)
            for task in group:
                if current_batch.total_duration + task.duration <= BATCH_MAX_MINUTES:
                    current_batch.tasks.append(task)
                else:
                    if current_batch.tasks:
                        batches.append(current_batch)
                    current_batch = TaskBatch(time_preference=pref, tasks=[task])
            if current_batch.tasks:
                batches.append(current_batch)
        return batches

    def check_day_load(self, tasks: List[Task]) -> dict:
        """Calculate available minutes and suggest deferrals if the day is overloaded."""
        total_day_minutes = time_to_minutes(self.day_end) - time_to_minutes(self.day_start)
        busy_minutes = sum(
            time_to_minutes(b.end_time) - time_to_minutes(b.start_time)
            for b in self.owner.availability
        )
        available_minutes  = max(0, total_day_minutes - busy_minutes)
        total_task_minutes = sum(t.duration for t in tasks)
        overloaded         = total_task_minutes > available_minutes

        deferred: List[Task] = []
        if overloaded:
            running = 0
            for task in sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99)):
                if running + task.duration <= available_minutes:
                    running += task.duration
                else:
                    deferred.append(task)

        return {
            "available_minutes": available_minutes,
            "total_task_minutes": total_task_minutes,
            "overloaded": overloaded,
            "deferred_suggestions": deferred,
        }

    def detect_conflicts(self, *plans: DayPlan) -> List[dict]:
        """Check DayPlans for overlapping tasks. Returns conflict dicts with resolution suggestions."""
        all_scheduled = [
            (plan.pet.name, sched_task)
            for plan in plans
            for sched_task in plan.scheduled_tasks
        ]

        conflicts: List[dict] = []
        for i, (pet_a, task_a) in enumerate(all_scheduled):
            for pet_b, task_b in all_scheduled[i + 1:]:
                a_start = time_to_minutes(task_a.start_time)
                a_end   = time_to_minutes(task_a.end_time)
                b_start = time_to_minutes(task_b.start_time)
                b_end   = time_to_minutes(task_b.end_time)

                if a_end <= b_start or b_end <= a_start:
                    continue

                # Lower-priority task is the one to move
                a_rank = PRIORITY_ORDER.get(task_a.task.priority, 99)
                b_rank = PRIORITY_ORDER.get(task_b.task.priority, 99)
                loser, loser_pet = (task_b, pet_b) if a_rank <= b_rank else (task_a, pet_a)

                # Find the first open slot after the conflict ends
                conflict_end = max(a_end, b_end)
                taken_slots = [
                    (time_to_minutes(s.start_time), time_to_minutes(s.end_time))
                    for p in plans for s in p.scheduled_tasks if s is not loser
                ]
                suggestion = self._find_slot_after(conflict_end, loser.task.duration, taken_slots)

                conflicts.append({
                    "message": (
                        f"'{task_a.task.name}' ({pet_a}, {task_a.start_time}–{task_a.end_time}) "
                        f"overlaps with '{task_b.task.name}' ({pet_b}, {task_b.start_time}–{task_b.end_time})"
                    ),
                    "loser_task": loser,
                    "loser_pet": loser_pet,
                    "suggestion": suggestion,
                })

        return conflicts

    def _find_slot_after(self, start_min: int, duration: int, taken_slots: list) -> Optional[str]:
        """Find the first available slot starting at or after start_min."""
        current = start_min
        day_end_min = time_to_minutes(self.day_end)
        while current + duration <= day_end_min:
            c_end = current + duration
            blocked = any(not (c_end <= s or current >= e) for s, e in taken_slots)
            blocked_owner = any(
                b.conflicts_with(minutes_to_time(current), minutes_to_time(c_end))
                for b in self.owner.availability
            )
            if not blocked and not blocked_owner:
                return minutes_to_time(current)
            current += 15
        return None

    def sort_by_time(self, plan: DayPlan) -> List[ScheduledTask]:
        """Return the plan's scheduled tasks sorted by start time (earliest first)."""
        return sorted(plan.scheduled_tasks, key=lambda t: time_to_minutes(t.start_time))

    def explain_plan(self, plan: DayPlan) -> str:
        """Return a human-readable explanation of why each task was placed when it was."""
        if not plan.scheduled_tasks:
            return "No tasks could be scheduled — check availability blocks or task durations."
        lines = [f"Schedule for {plan.pet.name} on {plan.plan_date}:\n"]
        for t in plan.scheduled_tasks:
            pref = f" (prefers {t.task.time_preference})" if t.task.time_preference else ""
            lines.append(
                f"• {t.task.name} at {t.start_time}–{t.end_time}"
                f" — {t.task.priority} priority, {t.task.duration} min{pref}"
            )
        return "\n".join(lines)
