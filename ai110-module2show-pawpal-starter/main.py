from pawpal_system import Task, Pet, Owner, AvailabilityBlock, Scheduler, ScheduledTask, DayPlan

# --- Owner ---
jordan = Owner(name="Jordan")
jordan.add_availability(AvailabilityBlock(label="Work", start_time="09:00", end_time="17:00", frequency="weekdays"))

# --- Pet 1: Mochi (tasks added OUT OF ORDER intentionally) ---
mochi = Pet(name="Mochi", species="dog", age=3)
mochi.add_care_task(Task(name="Grooming",     task_type="hygiene",   priority="low",    duration=20, frequency="weekly", time_preference="afternoon"))
mochi.add_care_task(Task(name="Evening Walk", task_type="exercise",  priority="medium", duration=30, frequency="daily",  time_preference="evening"))
mochi.add_care_task(Task(name="Feeding",      task_type="nutrition", priority="high",   duration=10, frequency="daily",  time_preference="morning"))
mochi.add_care_task(Task(name="Morning Walk", task_type="exercise",  priority="high",   duration=30, frequency="daily",  time_preference="morning"))

# --- Pet 2: Luna ---
luna = Pet(name="Luna", species="cat", age=5)
luna.add_care_task(Task(name="Playtime",   task_type="enrichment", priority="low",    duration=15, frequency="daily",  time_preference="evening"))
luna.add_care_task(Task(name="Litter Box", task_type="hygiene",    priority="medium", duration=10, frequency="daily",  time_preference="afternoon"))
luna.add_care_task(Task(name="Feeding",    task_type="nutrition",  priority="high",   duration=10, frequency="daily",  time_preference="morning"))

today = "2026-03-30"

# ─────────────────────────────────────────────
# MOCHI
# ─────────────────────────────────────────────
print("=" * 50)
scheduler_mochi = Scheduler(owner=jordan, pet=mochi, date=today)
plan_mochi = scheduler_mochi.build_schedule()

print("\n[RAW ORDER — as scheduled]")
plan_mochi.display()

print("\n[SORTED BY TIME]")
for st in scheduler_mochi.sort_by_time(plan_mochi):
    print(f"  {st.start_time}–{st.end_time}  {st.task.name}")

# Mark one task complete to test filtering
plan_mochi.scheduled_tasks[0].mark_complete()

print("\n[FILTER: incomplete only]")
for st in plan_mochi.filter_tasks("incomplete"):
    print(f"  ○ {st.task.name}")

print("\n[FILTER: complete only]")
for st in plan_mochi.filter_tasks("complete"):
    print(f"  ✓ {st.task.name}")

print()
print(scheduler_mochi.explain_plan(plan_mochi))

# ─────────────────────────────────────────────
# LUNA
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
scheduler_luna = Scheduler(owner=jordan, pet=luna, date=today)
plan_luna = scheduler_luna.build_schedule()

print("\n[RAW ORDER — as scheduled]")
plan_luna.display()

print("\n[SORTED BY TIME]")
for st in scheduler_luna.sort_by_time(plan_luna):
    print(f"  {st.start_time}–{st.end_time}  {st.task.name}")

print()
print(scheduler_luna.explain_plan(plan_luna))

# ─────────────────────────────────────────────
# TEST: next_occurrence() / recurring tasks
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("[RECURRING TASK TEST]")

for st in plan_mochi.scheduled_tasks:
    st.mark_complete(on_date=today)
    if st.next_task:
        print(f"  ✓ '{st.task.name}' complete → next due: {st.next_task.due_date} ({st.task.frequency})")
    else:
        print(f"  ✓ '{st.task.name}' complete → no recurrence ({st.task.frequency})")

# ─────────────────────────────────────────────
# TEST: detect_conflicts()
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("[CONFLICT DETECTION TEST]")

# Build a fake plan with two tasks manually forced to overlap
fake_owner = Owner(name="Test")
fake_pet = Pet(name="TestPet", species="dog", age=1)
fake_scheduler = Scheduler(owner=fake_owner, pet=fake_pet, date=today)

conflict_plan = DayPlan(date=today, owner=fake_owner, pet=fake_pet)
task_a = Task(name="Morning Walk", task_type="exercise", priority="high", duration=30, frequency="daily")
task_b = Task(name="Feeding",      task_type="nutrition", priority="high", duration=10, frequency="daily")

# Force both to start at 08:00 — intentional conflict
conflict_plan.add_task(ScheduledTask(task=task_a, start_time="08:00", end_time="08:30"))
conflict_plan.add_task(ScheduledTask(task=task_b, start_time="08:15", end_time="08:25"))

print("\nForced overlap: Morning Walk 08:00–08:30 and Feeding 08:15–08:25")
warnings = fake_scheduler.detect_conflicts(conflict_plan)
if warnings:
    for w in warnings:
        print(f"  {w}")
else:
    print("  No conflicts detected.")

# Also check real plans against each other (cross-pet)
print("\nCross-pet conflict check (Mochi vs Luna):")
real_warnings = scheduler_mochi.detect_conflicts(plan_mochi, plan_luna)
if real_warnings:
    for w in real_warnings:
        print(f"  {w}")
else:
    print("  No conflicts between Mochi and Luna's schedules.")
