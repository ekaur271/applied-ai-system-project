# PawPal+

**PawPal+** is a smart pet care scheduling app built with Python and Streamlit. It helps busy pet owners stay consistent with their pets' daily care by automatically building an optimized daily schedule around the owner's availability, the pet's needs, and task priorities.

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

## Features

### Core Scheduling

- **Priority-based scheduling** — Tasks are sorted high → medium → low before placement. Critical tasks like feeding and medication always get a slot before lower-priority ones like grooming or enrichment.
- **Availability-aware slot finding** — The scheduler scans the day in 15-minute increments and skips any window that overlaps with the owner's busy blocks (e.g. a 9–5 work schedule). No task will ever land inside a blocked period.
- **Time preference windows** — Each task can target a morning (8–12), afternoon (12–17), or evening (17–22) window. The scheduler searches within that window first, and falls back to the full day if no slot is found.
- **Conflict detection with resolution** — After building schedules for multiple pets, PawPal+ automatically scans for overlapping tasks across all plans. Each conflict is surfaced with a suggested fix (move the lower-priority task to the next open slot), and the owner can Apply Fix or Ignore with one click.
- **Schedule explanation** — Every generated schedule includes a plain-English breakdown of why each task was placed when it was — priority, duration, and time preference all explained.

### Advanced Algorithms

- **Pet energy curve** — Automatically assigns default time preferences based on species and task type before scheduling. Dogs get exercise in the morning; cats get it in the evening. Medication always defaults to morning. If the owner manually set a preference, it is never overwritten.
- **Task batching** — Tasks are grouped into batches by time window (Morning Routine, Afternoon Routine, Evening Routine) with a combined cap of 60 minutes per batch. Batches that exceed the cap are automatically split. The batched view in the schedule tab lets owners check off an entire routine at once.
- **Day load balancing** — Before building the schedule, PawPal+ calculates total available minutes (day window minus busy blocks) and compares it to total task time. If the day is overloaded, it suggests which low-priority tasks to defer, and the owner decides Keep or Defer for each one.
- **Recurring task generation** — When a scheduled task is marked complete, a new instance is automatically created with the next due date (`daily` → +1 day, `weekly` → +7 days, `as needed` → no recurrence). The next due date is shown inline beneath the completed task.

### Task Management

- **Multi-pet support** — Register any number of pets and generate independent schedules for each. Conflict detection works across all pets simultaneously.
- **Sorting** — The schedule view can be sorted by time (chronological), priority (high first), or grouped into time-window batches.
- **Task list filtering** — In the Tasks panel, filter tasks by type (exercise, nutrition, hygiene, enrichment, medication) and sort by priority, duration, or name.
- **Inline completion tracking** — Check off individual tasks or entire batches. Completed tasks fade and show a strikethrough. Progress bar and completion count update live.

### Persistence

- **JSON persistence** — Owner profile, busy blocks, pets, and all tasks are automatically saved to `data.json` on every change and restored on app startup. No data is lost between sessions.

### UI

- **Single-page dashboard** — All configuration (owner, pets, tasks) lives in the sidebar. The main area is the live schedule dashboard — no tab-switching required.
- **Dark mode** — Full dark theme via `.streamlit/config.toml`.
- **Animations** — Animated gradient topbar, task rows slide in on render, hover effects with purple glow, conflict banners pulse, buttons lift on hover.

---

## Project Structure

```
pawpal_system.py   # All backend logic — classes, scheduling, algorithms
app.py             # Streamlit dashboard UI
tests/
  test_pawpal.py   # 43 pytest tests covering all major behaviors
.streamlit/
  config.toml      # Dark mode theme config
data.json          # Auto-generated persistence file (created on first save)
mermaid.md         # UML class diagram source
reflection.md      # Project reflection
```

---

## Data Model

| Class | Responsibility |
|---|---|
| `Task` | A single care task with type, priority, duration, frequency, and time preference |
| `Pet` | Owns a list of care tasks; tracks species and age |
| `AvailabilityBlock` | A busy time window the scheduler must avoid |
| `Owner` | Holds the owner's name and availability blocks; handles JSON persistence |
| `ScheduledTask` | A placed task with a start/end time and completion state |
| `TaskBatch` | A group of tasks sharing a time window, with a combined duration cap |
| `DayPlan` | The full schedule for one pet on one day |
| `Scheduler` | Orchestrates all scheduling logic — slot finding, prioritization, batching, conflict detection |

---

## Running the App

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Running Tests

```bash
python -m pytest tests/test_pawpal.py -v
```

The test suite covers 43 behaviors across all classes and algorithms:

- Task lifecycle: complete, incomplete, recurrence (daily/weekly/as-needed), field preservation
- Pet CRUD: add, remove, get all tasks, serialization roundtrip
- Owner: JSON save/load roundtrip, missing file, corrupt JSON
- AvailabilityBlock: overlap detection, boundary conditions
- ScheduledTask: mark complete, next task generation, reset
- TaskBatch: total duration, completion state, label generation, batch splitting
- DayPlan: completion status, filter by status
- Scheduler: priority ordering, busy block avoidance, time preference windows, energy curve (dog/cat/explicit override), batching, day load (normal + overloaded), conflict detection (same pet, cross-pet, no overlap, with suggestion), sort by time, explain plan

**Test confidence: ⭐⭐⭐⭐ (4/5)** — Core logic is solid. Would push to 5 with tests covering time preference fallback when a preferred window is fully blocked, and tasks longer than any available gap.

---

## How I Used Agent Mode

I used Claude as a collaborator throughout the whole project, not just to generate code but to actually think through the design with me.

**Brainstorming and design** — I started by listing out my rough ideas for objects and attributes and asked Claude what it thought. We went back and forth until I had a solid set of classes with the right responsibilities. Then I had it generate a Mermaid.js UML diagram so I could visualize everything before writing any code.

**Generating the skeleton** — Once I was happy with the UML, I asked Claude to turn it into Python class stubs using dataclasses. No logic yet, just the structure. That made it easy to review and catch anything missing before getting into the actual implementation.

**Implementing the scheduling logic** — I had Claude implement the core algorithm step by step — priority ordering, the 15-minute slot scanner, busy block avoidance, and time preference windows. I reviewed each piece before moving on so I understood what was happening and could push back if something felt off.

**Advanced features** — For the four advanced algorithmic features (task batching, pet energy curve, day load balancing, conflict detection with resolution), I always discussed the approach with Claude before any code was written. I wanted to agree on the tradeoffs before committing.

**Code review and refactoring** — I asked Claude to put on the hat of a senior software engineer and a senior UX designer and do a full review. That caught a bug where `type` was shadowing a Python builtin, cleaned up unused variables, and led to a full UI rewrite from a tab layout to a single dashboard.

**Tests** — Claude helped write the test suite but I made sure each test was covering something real. We went from 13 tests to 43, covering every major class and behavior including edge cases like fully blocked days, corrupt JSON, and cross-pet conflict detection.

The workflow that worked best was always discussing before implementing, and using prompts like "think like a senior engineer" or "explain what you're about to do" to stay in control of what was being built.

---
