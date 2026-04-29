import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import (
    Task, Pet, Owner, AvailabilityBlock,
    Scheduler, ScheduledTask, TaskBatch, DayPlan,
    time_to_minutes,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_owner(busy_start=None, busy_end=None):
    owner = Owner(name="Jordan")
    if busy_start and busy_end:
        owner.add_availability(AvailabilityBlock(
            label="Work", start_time=busy_start, end_time=busy_end, frequency="weekdays"
        ))
    return owner


def make_task(name="Walk", priority="high", duration=30, frequency="daily",
              time_pref=None, task_type="exercise"):
    return Task(
        name=name, task_type=task_type, priority=priority,
        duration=duration, frequency=frequency, time_preference=time_pref,
    )


def make_pet(name="Mochi", species="dog"):
    return Pet(name=name, species=species, age=3)


# ─── Task ────────────────────────────────────────────────────────────────────

def test_mark_complete_changes_status():
    task = make_task()
    assert task.status == "incomplete"
    task.mark_complete()
    assert task.status == "complete"


def test_mark_incomplete_resets_status():
    task = make_task()
    task.mark_complete()
    task.mark_incomplete()
    assert task.status == "incomplete"


def test_next_occurrence_daily():
    """Daily task should generate next occurrence one day later."""
    task = make_task(frequency="daily")
    next_t = task.next_occurrence("2026-03-31")
    assert next_t is not None
    assert next_t.due_date == "2026-04-01"
    assert next_t.status == "incomplete"


def test_next_occurrence_weekly():
    """Weekly task should generate next occurrence seven days later."""
    task = make_task(frequency="weekly")
    next_t = task.next_occurrence("2026-03-31")
    assert next_t is not None
    assert next_t.due_date == "2026-04-07"


def test_next_occurrence_as_needed_returns_none():
    """Tasks with 'as needed' frequency should not generate a next occurrence."""
    task = make_task(frequency="as needed")
    assert task.next_occurrence("2026-03-31") is None


def test_next_occurrence_preserves_fields():
    """next_occurrence should copy name, task_type, priority, duration, and frequency."""
    task = Task(name="Feeding", task_type="nutrition", priority="high",
                duration=10, frequency="daily", time_preference="morning")
    next_t = task.next_occurrence("2026-03-31")
    assert next_t.name == "Feeding"
    assert next_t.task_type == "nutrition"
    assert next_t.priority == "high"
    assert next_t.duration == 10
    assert next_t.frequency == "daily"
    assert next_t.time_preference == "morning"


def test_task_serialization_roundtrip():
    """to_dict/from_dict should produce an identical Task."""
    original = Task(
        name="Morning Walk", task_type="exercise", priority="high",
        duration=30, frequency="daily", time_preference="morning",
        status="complete", due_date="2026-04-01",
    )
    restored = Task.from_dict(original.to_dict())
    assert restored.name == original.name
    assert restored.task_type == original.task_type
    assert restored.priority == original.priority
    assert restored.duration == original.duration
    assert restored.frequency == original.frequency
    assert restored.time_preference == original.time_preference
    assert restored.status == original.status
    assert restored.due_date == original.due_date


def test_task_from_dict_backwards_compat():
    """from_dict should accept the old 'type' key for task_type."""
    d = {"name": "Walk", "type": "exercise", "priority": "low",
         "duration": 20, "frequency": "daily"}
    task = Task.from_dict(d)
    assert task.task_type == "exercise"


# ─── Pet ─────────────────────────────────────────────────────────────────────

def test_add_care_task_increases_count():
    pet = make_pet()
    assert len(pet.care_tasks) == 0
    pet.add_care_task(make_task())
    assert len(pet.care_tasks) == 1


def test_remove_care_task_decreases_count():
    """remove_care_task should remove exactly the given task."""
    pet = make_pet()
    task = make_task(name="Grooming")
    pet.add_care_task(task)
    assert len(pet.care_tasks) == 1
    pet.remove_care_task(task)
    assert len(pet.care_tasks) == 0


def test_get_all_tasks_returns_all():
    """get_all_tasks should return every task added to the pet."""
    pet = make_pet()
    t1, t2 = make_task(name="Walk"), make_task(name="Feeding")
    pet.add_care_task(t1)
    pet.add_care_task(t2)
    all_tasks = pet.get_all_tasks()
    assert len(all_tasks) == 2
    assert t1 in all_tasks
    assert t2 in all_tasks


def test_pet_serialization_roundtrip():
    """Pet.to_dict/from_dict should restore the pet with all its tasks intact."""
    pet = make_pet(name="Luna", species="cat")
    pet.add_care_task(Task(name="Feeding", task_type="nutrition", priority="high",
                           duration=10, frequency="daily"))
    pet.add_care_task(Task(name="Playtime", task_type="enrichment", priority="low",
                           duration=15, frequency="daily"))

    restored = Pet.from_dict(pet.to_dict())
    assert restored.name == "Luna"
    assert restored.species == "cat"
    assert len(restored.care_tasks) == 2
    assert restored.care_tasks[0].name == "Feeding"
    assert restored.care_tasks[1].task_type == "enrichment"


# ─── AvailabilityBlock ───────────────────────────────────────────────────────

def test_availability_block_detects_overlap():
    """conflicts_with should return True when the slot overlaps the block."""
    block = AvailabilityBlock(label="Work", start_time="09:00", end_time="17:00", frequency="weekdays")
    assert block.conflicts_with("10:00", "10:30") is True   # fully inside
    assert block.conflicts_with("08:30", "09:15") is True   # straddles start
    assert block.conflicts_with("16:45", "17:15") is True   # straddles end


def test_availability_block_no_overlap():
    """conflicts_with should return False for slots entirely outside the block."""
    block = AvailabilityBlock(label="Work", start_time="09:00", end_time="17:00", frequency="weekdays")
    assert block.conflicts_with("08:00", "09:00") is False  # ends exactly at block start
    assert block.conflicts_with("17:00", "17:30") is False  # starts exactly at block end
    assert block.conflicts_with("07:00", "08:00") is False  # entirely before


# ─── Owner JSON persistence ───────────────────────────────────────────────────

def test_owner_json_save_and_load(tmp_path):
    """save_to_json/load_from_json should round-trip owner, availability, and pets."""
    filepath = str(tmp_path / "data.json")

    owner = Owner(name="Jordan")
    owner.add_availability(AvailabilityBlock(
        label="Work", start_time="09:00", end_time="17:00", frequency="weekdays"
    ))
    pet = Pet(name="Mochi", species="dog", age=3)
    pet.add_care_task(Task(name="Walk", task_type="exercise", priority="high",
                           duration=30, frequency="daily"))
    owner.save_to_json([pet], filepath=filepath)

    loaded_owner, loaded_pets = Owner.load_from_json(filepath=filepath)

    assert loaded_owner.name == "Jordan"
    assert len(loaded_owner.availability) == 1
    assert loaded_owner.availability[0].label == "Work"
    assert len(loaded_pets) == 1
    assert loaded_pets[0].name == "Mochi"
    assert loaded_pets[0].care_tasks[0].name == "Walk"


def test_owner_load_missing_file():
    """load_from_json should return (None, []) when the file does not exist."""
    owner, pets = Owner.load_from_json(filepath="/tmp/nonexistent_pawpal_test.json")
    assert owner is None
    assert pets == []


def test_owner_load_corrupt_json(tmp_path):
    """load_from_json should return (None, []) on malformed JSON."""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json")
    owner, pets = Owner.load_from_json(filepath=str(bad_file))
    assert owner is None
    assert pets == []


# ─── ScheduledTask ────────────────────────────────────────────────────────────

def test_scheduled_task_mark_complete_sets_next():
    """mark_complete on a recurring ScheduledTask should populate next_task."""
    task = make_task(frequency="daily")
    sched = ScheduledTask(task=task, start_time="08:00", end_time="08:30")
    sched.mark_complete(on_date="2026-03-31")
    assert sched.is_complete is True
    assert sched.next_task is not None
    assert sched.next_task.due_date == "2026-04-01"


def test_mark_complete_then_incomplete_resets():
    """Marking complete then incomplete should cleanly reset status and next_task."""
    task = make_task(frequency="daily")
    st = ScheduledTask(task=task, start_time="08:00", end_time="08:30")
    st.mark_complete(on_date="2026-03-31")
    assert st.is_complete is True
    assert st.next_task is not None

    task.mark_incomplete()
    st.is_complete = False
    st.next_task = None
    assert st.is_complete is False
    assert task.status == "incomplete"
    assert st.next_task is None


# ─── TaskBatch ───────────────────────────────────────────────────────────────

def test_task_batch_total_duration():
    """total_duration should sum durations of all tasks in the batch."""
    batch = TaskBatch(time_preference="morning")
    batch.tasks = [make_task(duration=20), make_task(duration=15)]
    assert batch.total_duration == 35


def test_task_batch_is_complete_all_done():
    """is_complete should be True only when every task is complete."""
    t1 = make_task(name="A")
    t2 = make_task(name="B")
    batch = TaskBatch(time_preference="morning", tasks=[t1, t2])
    assert batch.is_complete is False
    t1.mark_complete()
    assert batch.is_complete is False
    t2.mark_complete()
    assert batch.is_complete is True


def test_task_batch_label():
    """label property should return human-readable routine names."""
    assert TaskBatch(time_preference="morning").label == "Morning Routine"
    assert TaskBatch(time_preference="afternoon").label == "Afternoon Routine"
    assert TaskBatch(time_preference="evening").label == "Evening Routine"
    assert TaskBatch(time_preference="unknown").label == "Task Block"


# ─── DayPlan ─────────────────────────────────────────────────────────────────

def test_day_plan_completion_status():
    """get_completion_status should correctly count total, complete, remaining."""
    owner, pet = make_owner(), make_pet()
    plan = DayPlan(plan_date="2026-03-31", owner=owner, pet=pet)
    s1 = ScheduledTask(task=make_task(name="Walk"), start_time="08:00", end_time="08:30")
    s2 = ScheduledTask(task=make_task(name="Feed"), start_time="09:00", end_time="09:10")
    plan.add_task(s1)
    plan.add_task(s2)
    s1.mark_complete(on_date="2026-03-31")

    status = plan.get_completion_status()
    assert status["total"] == 2
    assert status["complete"] == 1
    assert status["remaining"] == 1


def test_day_plan_filter_tasks():
    """filter_tasks should return only tasks matching the requested status."""
    owner, pet = make_owner(), make_pet()
    plan = DayPlan(plan_date="2026-03-31", owner=owner, pet=pet)
    s1 = ScheduledTask(task=make_task(name="Walk"), start_time="08:00", end_time="08:30")
    s2 = ScheduledTask(task=make_task(name="Feed"), start_time="09:00", end_time="09:10")
    plan.add_task(s1)
    plan.add_task(s2)
    s1.mark_complete(on_date="2026-03-31")

    assert len(plan.filter_tasks("complete")) == 1
    assert len(plan.filter_tasks("incomplete")) == 1
    assert len(plan.filter_tasks("all")) == 2


# ─── Scheduler: scheduling algorithm ─────────────────────────────────────────

def test_high_priority_scheduled_before_low():
    """High priority tasks should appear earlier in the schedule than low priority."""
    owner = make_owner()
    pet = make_pet()
    pet.add_care_task(make_task(name="Grooming", priority="low",  duration=20))
    pet.add_care_task(make_task(name="Feeding",  priority="high", duration=10))

    plan = Scheduler(owner=owner, pet=pet, date="2026-03-31").build_schedule()
    names = [st.task.name for st in plan.scheduled_tasks]
    assert names.index("Feeding") < names.index("Grooming")


def test_scheduler_avoids_busy_block():
    """No task should be scheduled inside the owner's busy block."""
    owner = make_owner(busy_start="08:00", busy_end="20:00")
    pet = make_pet()
    pet.add_care_task(make_task(name="Walk", duration=30))

    plan = Scheduler(owner=owner, pet=pet, date="2026-03-31").build_schedule()
    for st in plan.scheduled_tasks:
        start_min = time_to_minutes(st.start_time)
        end_min   = time_to_minutes(st.end_time)
        assert end_min <= 8 * 60 or start_min >= 20 * 60, (
            f"Task '{st.task.name}' scheduled inside busy block: {st.start_time}–{st.end_time}"
        )


def test_task_scheduled_within_time_preference_window():
    """A task with time_pref='evening' should be scheduled between 17:00 and 22:00."""
    owner = make_owner()
    pet = make_pet()
    pet.add_care_task(make_task(name="Evening Walk", duration=30, time_pref="evening"))

    plan = Scheduler(owner=owner, pet=pet, date="2026-03-31").build_schedule()
    assert len(plan.scheduled_tasks) == 1
    start_min = time_to_minutes(plan.scheduled_tasks[0].start_time)
    assert start_min >= time_to_minutes("17:00"), "Task not scheduled in evening window"
    assert start_min < time_to_minutes("22:00")


def test_build_schedule_empty_tasks():
    """Scheduler should return an empty DayPlan when pet has no tasks."""
    owner = make_owner()
    plan = Scheduler(owner=owner, pet=make_pet(), date="2026-03-31").build_schedule()
    assert len(plan.scheduled_tasks) == 0


def test_no_slot_when_day_fully_blocked():
    """When the entire day is blocked, no tasks should be scheduled."""
    owner = make_owner(busy_start="00:00", busy_end="23:59")
    pet = make_pet()
    pet.add_care_task(make_task(name="Walk", duration=30))
    plan = Scheduler(owner=owner, pet=pet, date="2026-03-31").build_schedule()
    assert len(plan.scheduled_tasks) == 0


# ─── Scheduler: energy curve ─────────────────────────────────────────────────

def test_fill_time_preferences_dog_exercise_gets_morning():
    """Energy curve: dog exercise tasks with no preference should default to morning."""
    owner = make_owner()
    pet = Pet(name="Rex", species="dog", age=2)
    task = Task(name="Walk", task_type="exercise", priority="high",
                duration=30, frequency="daily", time_preference=None)
    pet.add_care_task(task)

    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")
    scheduler.fill_time_preferences()
    assert task.time_preference == "morning"


def test_fill_time_preferences_cat_exercise_gets_evening():
    """Energy curve: cat exercise tasks with no preference should default to evening."""
    owner = make_owner()
    pet = Pet(name="Whiskers", species="cat", age=4)
    task = Task(name="Play", task_type="exercise", priority="medium",
                duration=15, frequency="daily", time_preference=None)
    pet.add_care_task(task)

    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")
    scheduler.fill_time_preferences()
    assert task.time_preference == "evening"


def test_fill_time_preferences_does_not_override_explicit():
    """Energy curve should NOT overwrite a time_preference the user already set."""
    owner = make_owner()
    pet = Pet(name="Rex", species="dog", age=2)
    task = Task(name="Walk", task_type="exercise", priority="high",
                duration=30, frequency="daily", time_preference="afternoon")
    pet.add_care_task(task)

    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")
    scheduler.fill_time_preferences()
    assert task.time_preference == "afternoon"  # user preference preserved


# ─── Scheduler: batch_tasks ───────────────────────────────────────────────────

def test_batch_tasks_groups_by_time_preference():
    """Tasks sharing the same time preference should land in the same batch."""
    owner, pet = make_owner(), make_pet()
    t1 = make_task(name="Walk",    time_pref="morning", duration=20)
    t2 = make_task(name="Feeding", time_pref="morning", duration=10)
    t3 = make_task(name="Play",    time_pref="evening", duration=15)

    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")
    batches = scheduler.batch_tasks([t1, t2, t3])

    morning_batch = next(b for b in batches if b.time_preference == "morning")
    evening_batch = next(b for b in batches if b.time_preference == "evening")
    assert len(morning_batch.tasks) == 2
    assert len(evening_batch.tasks) == 1


def test_batch_tasks_splits_when_over_limit():
    """A batch should split when combined duration exceeds BATCH_MAX_MINUTES (60)."""
    from pawpal_system import BATCH_MAX_MINUTES
    owner, pet = make_owner(), make_pet()
    tasks = [make_task(name=f"T{i}", time_pref="morning", duration=25) for i in range(3)]
    # 3 × 25 min = 75 min > 60 min limit → must produce at least 2 batches

    batches = Scheduler(owner=owner, pet=pet, date="2026-03-31").batch_tasks(tasks)
    morning_batches = [b for b in batches if b.time_preference == "morning"]
    assert len(morning_batches) >= 2
    for b in morning_batches:
        assert b.total_duration <= BATCH_MAX_MINUTES


# ─── Scheduler: check_day_load ────────────────────────────────────────────────

def test_check_day_load_not_overloaded():
    """check_day_load should report not overloaded when tasks fit in available time."""
    owner = make_owner()   # no busy blocks
    pet = make_pet()
    tasks = [make_task(name="Walk", duration=30)]

    result = Scheduler(owner=owner, pet=pet, date="2026-03-31").check_day_load(tasks)
    assert result["overloaded"] is False
    assert result["deferred_suggestions"] == []


def test_check_day_load_overloaded_suggests_deferrals():
    """When total task minutes exceed available time, low-priority tasks should be deferred."""
    # Day is 08:00–22:00 (840 min); busy 08:00–21:30 leaves exactly 30 free minutes.
    # Feeding (30 min, high) fits; Grooming (60 min, low) should be deferred.
    owner = make_owner(busy_start="08:00", busy_end="21:30")
    pet = make_pet()
    tasks = [
        make_task(name="Feeding",  priority="high", duration=30),
        make_task(name="Grooming", priority="low",  duration=60),
    ]

    result = Scheduler(owner=owner, pet=pet, date="2026-03-31").check_day_load(tasks)
    assert result["overloaded"] is True
    deferred_names = [t.name for t in result["deferred_suggestions"]]
    assert "Grooming" in deferred_names    # low-priority task deferred
    assert "Feeding" not in deferred_names  # high-priority task kept


# ─── Scheduler: sort, conflicts, explain ─────────────────────────────────────

def test_sort_by_time_returns_chronological_order():
    """sort_by_time should return scheduled tasks ordered earliest to latest."""
    owner, pet = make_owner(), make_pet()
    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")

    plan = DayPlan(plan_date="2026-03-31", owner=owner, pet=pet)
    plan.add_task(ScheduledTask(task=make_task(name="Evening Walk"), start_time="18:00", end_time="18:30"))
    plan.add_task(ScheduledTask(task=make_task(name="Feeding"),      start_time="08:00", end_time="08:10"))
    plan.add_task(ScheduledTask(task=make_task(name="Grooming"),     start_time="13:00", end_time="13:20"))

    sorted_tasks = scheduler.sort_by_time(plan)
    times = [st.start_time for st in sorted_tasks]
    assert times == sorted(times), f"Expected chronological order, got: {times}"


def test_detect_conflicts_finds_overlap():
    """detect_conflicts should return a warning when two tasks overlap."""
    owner, pet = make_owner(), make_pet()
    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")

    plan = DayPlan(plan_date="2026-03-31", owner=owner, pet=pet)
    plan.add_task(ScheduledTask(task=make_task(name="Walk"),    start_time="08:00", end_time="08:30"))
    plan.add_task(ScheduledTask(task=make_task(name="Feeding"), start_time="08:15", end_time="08:25"))

    warnings = scheduler.detect_conflicts(plan)
    assert len(warnings) > 0
    assert "Walk" in warnings[0]["message"]
    assert "Feeding" in warnings[0]["message"]


def test_detect_conflicts_no_overlap():
    """detect_conflicts should return no warnings when tasks do not overlap."""
    owner, pet = make_owner(), make_pet()
    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")

    plan = DayPlan(plan_date="2026-03-31", owner=owner, pet=pet)
    plan.add_task(ScheduledTask(task=make_task(name="Walk"),    start_time="08:00", end_time="08:30"))
    plan.add_task(ScheduledTask(task=make_task(name="Feeding"), start_time="08:30", end_time="08:40"))

    assert scheduler.detect_conflicts(plan) == []


def test_detect_conflicts_across_two_pets():
    """detect_conflicts should catch overlaps between different pets' schedules."""
    owner = make_owner()
    pet_a = Pet(name="Mochi", species="dog", age=3)
    pet_b = Pet(name="Luna",  species="cat", age=2)

    plan_a = DayPlan(plan_date="2026-03-31", owner=owner, pet=pet_a)
    plan_b = DayPlan(plan_date="2026-03-31", owner=owner, pet=pet_b)
    plan_a.add_task(ScheduledTask(task=make_task(name="Walk"),   start_time="09:00", end_time="09:30"))
    plan_b.add_task(ScheduledTask(task=make_task(name="Feeding"), start_time="09:15", end_time="09:25"))

    scheduler = Scheduler(owner=owner, pet=pet_a, date="2026-03-31")
    warnings = scheduler.detect_conflicts(plan_a, plan_b)
    assert len(warnings) > 0
    assert "Walk" in warnings[0]["message"]


def test_detect_conflicts_suggests_resolution():
    """A conflict dict should include a non-None suggestion when a free slot exists."""
    owner = make_owner()   # no busy blocks
    pet = make_pet()
    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")

    plan = DayPlan(plan_date="2026-03-31", owner=owner, pet=pet)
    plan.add_task(ScheduledTask(task=make_task(name="Walk"),    start_time="08:00", end_time="08:30"))
    plan.add_task(ScheduledTask(task=make_task(name="Feeding"), start_time="08:15", end_time="08:25"))

    warnings = scheduler.detect_conflicts(plan)
    assert warnings[0]["suggestion"] is not None


def test_explain_plan_is_non_empty():
    """explain_plan should return a non-empty string for a non-empty schedule."""
    owner = make_owner()
    pet = make_pet()
    pet.add_care_task(make_task(name="Walk", duration=30, time_pref="morning"))
    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")
    plan = scheduler.build_schedule()
    explanation = scheduler.explain_plan(plan)
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    assert "Walk" in explanation


def test_explain_plan_empty_schedule():
    """explain_plan should return a helpful message when nothing could be scheduled."""
    owner = make_owner(busy_start="00:00", busy_end="23:59")
    pet = make_pet()
    pet.add_care_task(make_task())
    scheduler = Scheduler(owner=owner, pet=pet, date="2026-03-31")
    plan = scheduler.build_schedule()
    explanation = scheduler.explain_plan(plan)
    assert isinstance(explanation, str)
    assert len(explanation) > 0
