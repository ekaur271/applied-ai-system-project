import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, AvailabilityBlock, Scheduler, TaskBatch

# ─── Page config (must be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="PawPal+",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ────────────────────────────────────────────────────────────────
TODAY         = str(date.today())
TODAY_DISPLAY = date.today().strftime("%A, %B ") + str(date.today().day)

PRIORITY_BADGE = {"high": "🔴", "medium": "🟡", "low": "🟢"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
TYPE_EMOJI     = {
    "exercise": "🏃", "nutrition": "🍖", "hygiene": "🛁",
    "enrichment": "🧸", "medication": "💊",
}
SPECIES_ICON = {"dog": "🐕", "cat": "🐈", "other": "🐾"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def save():
    if st.session_state.owner:
        st.session_state.owner.save_to_json(st.session_state.pets)


def priority_badge(priority: str) -> str:
    icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    icon = icons.get(priority, "")
    cls  = f"badge-{priority}"
    return (
        f"<span style='display:inline-block;padding:2px 9px;border-radius:20px;"
        f"font-size:0.72rem;font-weight:700;' class='{cls}'>"
        f"{icon} {priority.capitalize()}</span>"
    )


# ─── CSS Design System (dark mode + animations) ───────────────────────────────
st.markdown("""
<style>
  /* ── Global ── */
  .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem; }

  /* ── Animated gradient topbar ── */
  @keyframes gradientShift {
    0%   { background-position: 0%   50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0%   50%; }
  }
  .topbar {
    background: linear-gradient(135deg, #667eea, #764ba2, #9f7aea, #667eea);
    background-size: 300% 300%;
    animation: gradientShift 10s ease infinite;
    padding: 1.1rem 1.6rem; border-radius: 16px; margin-bottom: 1.4rem;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 4px 24px rgba(102,126,234,0.4);
  }
  .topbar-left h1 {
    color: white; font-size: 1.75rem; font-weight: 900;
    margin: 0; letter-spacing: -0.5px;
  }
  .topbar-left p  { color: rgba(255,255,255,0.82); font-size: 0.88rem; margin: 3px 0 0 0; }
  .topbar-right   { text-align: right; }
  .topbar-right .date { color: white; font-size: 1rem; font-weight: 700; }
  .topbar-right .meta { color: rgba(255,255,255,0.65); font-size: 0.8rem; margin-top: 2px; }

  /* ── Task row slide-in ── */
  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-8px); }
    to   { opacity: 1; transform: translateX(0);    }
  }

  /* ── Task row (dark) ── */
  .task-row {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 12px; border-radius: 8px;
    border: 1px solid #1e1e3a;
    background: #16162e;
    margin-bottom: 5px;
    animation: slideIn 0.22s ease-out both;
    transition: border-color 0.2s ease, background 0.2s ease,
                box-shadow 0.2s ease, transform 0.15s ease;
  }
  .task-row:hover {
    border-color: #667eea;
    background: #1c1c3a;
    transform: translateX(3px);
    box-shadow: 0 2px 14px rgba(102,126,234,0.18);
  }
  .task-time {
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.77rem; font-weight: 600; color: #7c8db0; min-width: 108px;
  }
  .task-name { flex: 1; font-size: 0.9rem; font-weight: 600; color: #e2e8f0; }
  .task-dur  { font-size: 0.76rem; color: #4a5880; min-width: 46px; text-align: right; }

  /* ── Batch header (dark) ── */
  .batch-header {
    background: #1a1035; border: 1px solid #3b2e6e; border-radius: 8px;
    padding: 7px 12px; margin: 10px 0 4px 0;
    font-weight: 700; font-size: 0.88rem; color: #a78bfa;
    transition: background 0.2s;
  }
  .batch-header:hover { background: #1f1440; }

  /* ── Priority badges (dark) ── */
  .badge-high   { background: #3d0f0f; color: #f87171; border: 1px solid #7f1d1d; }
  .badge-medium { background: #2e1f00; color: #fcd34d; border: 1px solid #78350f; }
  .badge-low    { background: #062010; color: #4ade80; border: 1px solid #14532d; }

  /* ── Conflict banner (dark) ── */
  @keyframes pulseWarn {
    0%, 100% { box-shadow: 0 0 0 0   rgba(249,115,22,0.3); }
    50%       { box-shadow: 0 0 0 6px rgba(249,115,22,0);   }
  }
  .conflict-card {
    background: #1e0e00; border: 1px solid #7c2d12;
    border-left: 4px solid #f97316; border-radius: 10px;
    padding: 12px 16px; margin-bottom: 8px;
    animation: pulseWarn 2.5s ease-in-out infinite;
  }

  /* ── Empty state (dark) ── */
  .empty-state {
    text-align: center; padding: 4.5rem 2rem; color: #374151;
  }
  .empty-state .icon { font-size: 3.5rem; display: block; margin-bottom: 0.75rem; }
  .empty-state h3    { font-size: 1.2rem; font-weight: 700; color: #4b5563; margin-bottom: 0.4rem; }
  .empty-state p     { font-size: 0.88rem; max-width: 320px; margin: 0 auto; color: #374151; }

  /* ── Progress bar glow on overload ── */
  @keyframes overloadPulse {
    0%, 100% { opacity: 1;    }
    50%       { opacity: 0.55; }
  }
  .overload-label { animation: overloadPulse 2s ease-in-out infinite; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem !important; }
  [data-testid="stSidebar"] .stExpander { border-radius: 8px !important; }

  /* ── Button hover lift ── */
  .stButton > button {
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(102,126,234,0.3) !important;
  }
  .stButton > button:active { transform: translateY(0) !important; }
</style>
""", unsafe_allow_html=True)


# ─── Session State ────────────────────────────────────────────────────────────
if "owner" not in st.session_state:
    loaded_owner, loaded_pets = Owner.load_from_json()
    st.session_state.owner = loaded_owner
    st.session_state.pets  = loaded_pets
if "plans" not in st.session_state:
    st.session_state.plans = {}


# ─── Render helpers ───────────────────────────────────────────────────────────

def _render_flat(tasks_to_show, pname):
    """Flat list of scheduled tasks: checkbox + time + name + duration + badge."""
    for i, sched in enumerate(tasks_to_show):
        done = sched.is_complete
        c_chk, c_time, c_icon, c_name, c_dur, c_badge = st.columns([0.4, 1.3, 0.4, 3.5, 0.7, 1.2])

        with c_chk:
            checked = st.checkbox("", value=done, key=f"flat_{pname}_{i}")
            if checked and not sched.is_complete:
                sched.mark_complete(on_date=TODAY)
            elif not checked and sched.is_complete:
                sched.task.mark_incomplete()
                sched.is_complete = False
                sched.next_task   = None

        fade = "opacity:0.35;" if done else ""

        with c_time:
            st.markdown(
                f"<span style='{fade}font-family:monospace;font-size:0.77rem;"
                f"font-weight:600;color:#64748b'>{sched.start_time}–{sched.end_time}</span>",
                unsafe_allow_html=True,
            )
        with c_icon:
            st.markdown(
                f"<span style='{fade}font-size:1rem'>"
                f"{TYPE_EMOJI.get(sched.task.task_type, '📌')}</span>",
                unsafe_allow_html=True,
            )
        with c_name:
            strike = "text-decoration:line-through;" if done else ""
            st.markdown(
                f"<span style='{fade}{strike}font-size:0.9rem;font-weight:600;color:#1e293b'>"
                f"{sched.task.name}</span>",
                unsafe_allow_html=True,
            )
            if done and sched.next_task:
                st.markdown(
                    f"<span style='font-size:0.7rem;color:#8b5cf6;font-style:italic'>"
                    f"↻ Next: {sched.next_task.due_date}</span>",
                    unsafe_allow_html=True,
                )
        with c_dur:
            st.markdown(
                f"<span style='{fade}font-size:0.76rem;color:#94a3b8'>"
                f"{sched.task.duration} min</span>",
                unsafe_allow_html=True,
            )
        with c_badge:
            if not done:
                st.markdown(priority_badge(sched.task.priority), unsafe_allow_html=True)


def _render_consolidated(plans_dict):
    """Single merged schedule across all pets, sorted by start time."""
    # Collect (pname, species, sched_task) tuples from all plans
    all_entries = []
    for pname, entry in plans_dict.items():
        pet_obj = next((p for p in st.session_state.pets if p.name == pname), None)
        icon    = SPECIES_ICON.get(pet_obj.species if pet_obj else "other", "🐾")
        for sched in entry["plan"].scheduled_tasks:
            all_entries.append((pname, icon, sched))

    # Sort by start time
    from pawpal_system import time_to_minutes
    all_entries.sort(key=lambda x: time_to_minutes(x[2].start_time))

    if not all_entries:
        st.info("No tasks scheduled.")
        return

    # Column headers
    st.markdown(
        "<div style='display:flex;gap:10px;padding:4px 12px;"
        "font-size:0.7rem;font-weight:700;letter-spacing:0.06em;"
        "text-transform:uppercase;color:#94a3b8;margin-bottom:2px;'>"
        "<span style='min-width:16px'></span>"
        "<span style='min-width:90px'>Pet</span>"
        "<span style='min-width:108px'>Time</span>"
        "<span style='flex:1'>Task</span>"
        "<span style='min-width:46px;text-align:right'>Dur</span>"
        "<span style='min-width:90px'></span>"
        "</div>",
        unsafe_allow_html=True,
    )

    for i, (pname, icon, sched) in enumerate(all_entries):
        done = sched.is_complete
        c_chk, c_pet, c_time, c_icon, c_name, c_dur, c_badge = st.columns(
            [0.4, 1.1, 1.3, 0.4, 3.2, 0.7, 1.2]
        )
        with c_chk:
            checked = st.checkbox("", value=done, key=f"con_{pname}_{i}")
            if checked and not sched.is_complete:
                sched.mark_complete(on_date=TODAY)
            elif not checked and sched.is_complete:
                sched.task.mark_incomplete()
                sched.is_complete = False
                sched.next_task   = None

        fade = "opacity:0.35;" if done else ""

        with c_pet:
            st.markdown(
                f"<span style='{fade}font-size:0.78rem;font-weight:600;color:#7c8db0'>"
                f"{icon} {pname}</span>",
                unsafe_allow_html=True,
            )
        with c_time:
            st.markdown(
                f"<span style='{fade}font-family:monospace;font-size:0.77rem;"
                f"font-weight:600;color:#64748b'>{sched.start_time}–{sched.end_time}</span>",
                unsafe_allow_html=True,
            )
        with c_icon:
            st.markdown(
                f"<span style='{fade}font-size:1rem'>"
                f"{TYPE_EMOJI.get(sched.task.task_type, '📌')}</span>",
                unsafe_allow_html=True,
            )
        with c_name:
            strike = "text-decoration:line-through;" if done else ""
            st.markdown(
                f"<span style='{fade}{strike}font-size:0.9rem;font-weight:600;color:#e2e8f0'>"
                f"{sched.task.name}</span>",
                unsafe_allow_html=True,
            )
            if done and sched.next_task:
                st.markdown(
                    f"<span style='font-size:0.7rem;color:#8b5cf6;font-style:italic'>"
                    f"↻ Next: {sched.next_task.due_date}</span>",
                    unsafe_allow_html=True,
                )
        with c_dur:
            st.markdown(
                f"<span style='{fade}font-size:0.76rem;color:#94a3b8'>"
                f"{sched.task.duration} min</span>",
                unsafe_allow_html=True,
            )
        with c_badge:
            if not done:
                st.markdown(priority_badge(sched.task.priority), unsafe_allow_html=True)


def _render_batched(batches, plan, pname):
    """Batched view: group tasks by time window with a collapsible batch header checkbox."""
    name_to_sched = {s.task.name: s for s in plan.scheduled_tasks}

    for bi, batch in enumerate(batches):
        batch_sched = [name_to_sched[t.name] for t in batch.tasks if t.name in name_to_sched]
        if not batch_sched:
            continue

        all_done    = all(s.is_complete for s in batch_sched)
        total_done  = sum(1 for s in batch_sched if s.is_complete)
        strike      = "text-decoration:line-through;opacity:0.4;" if all_done else ""

        bc1, bc2 = st.columns([0.4, 6])
        with bc1:
            all_checked = st.checkbox("", value=all_done, key=f"batch_{pname}_{bi}_{batch.label}")
            if all_checked and not all_done:
                for s in batch_sched:
                    if not s.is_complete:
                        s.mark_complete(on_date=TODAY)
        with bc2:
            st.markdown(
                f"<div class='batch-header' style='{strike}'>"
                f"{batch.label} &nbsp;·&nbsp; {batch.total_duration} min"
                f"&nbsp;·&nbsp; {total_done}/{len(batch.tasks)} done</div>",
                unsafe_allow_html=True,
            )

        if not all_done:
            for si, sched in enumerate(batch_sched):
                done = sched.is_complete
                _, sc_chk, sc_time, sc_name, sc_dur, sc_badge = st.columns([0.3, 0.4, 1.3, 3.8, 0.7, 1.2])

                with sc_chk:
                    checked = st.checkbox("", value=done, key=f"sub_{pname}_{bi}_{batch.label}_{si}")
                    if checked and not sched.is_complete:
                        sched.mark_complete(on_date=TODAY)
                    elif not checked and sched.is_complete:
                        sched.task.mark_incomplete()
                        sched.is_complete = False
                        sched.next_task   = None

                fade   = "opacity:0.35;" if done else ""
                strike = "text-decoration:line-through;" if done else ""

                with sc_time:
                    st.markdown(
                        f"<span style='{fade}font-family:monospace;font-size:0.77rem;"
                        f"font-weight:600;color:#64748b'>{sched.start_time}–{sched.end_time}</span>",
                        unsafe_allow_html=True,
                    )
                with sc_name:
                    emoji = TYPE_EMOJI.get(sched.task.task_type, "📌")
                    st.markdown(
                        f"<span style='{fade}{strike}font-size:0.88rem;font-weight:600;color:#1e293b'>"
                        f"{emoji} {sched.task.name}</span>",
                        unsafe_allow_html=True,
                    )
                    if done and sched.next_task:
                        st.markdown(
                            f"<span style='font-size:0.7rem;color:#8b5cf6;font-style:italic'>"
                            f"↻ Next: {sched.next_task.due_date}</span>",
                            unsafe_allow_html=True,
                        )
                with sc_dur:
                    st.markdown(
                        f"<span style='{fade}font-size:0.76rem;color:#94a3b8'>"
                        f"{sched.task.duration} min</span>",
                        unsafe_allow_html=True,
                    )
                with sc_badge:
                    if not done:
                        st.markdown(priority_badge(sched.task.priority), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR — all configuration
# ═══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🐾 PawPal+")
    st.caption("Smart pet care scheduling")
    st.divider()

    # ── Owner ──────────────────────────────────────────────────────────
    with st.expander("👤 Owner & Availability", expanded=st.session_state.owner is None):
        default_name = st.session_state.owner.name if st.session_state.owner else ""
        owner_name = st.text_input(
            "Your name", value=default_name, placeholder="e.g. Jordan",
            key="owner_name_input", label_visibility="collapsed",
        )
        if st.button("💾 Save Owner", type="primary", use_container_width=True):
            if owner_name.strip():
                st.session_state.owner = Owner(name=owner_name.strip())
                st.session_state.pets  = []
                st.session_state.plans = {}
                save()
                st.success(f"Welcome, {owner_name.strip()}!")
                st.rerun()
            else:
                st.warning("Enter a name first.")

        if st.session_state.owner:
            st.markdown("**⛔ Busy Time Blocks**")
            st.caption("The scheduler avoids these windows.")

            bb1, bb2 = st.columns(2)
            with bb1:
                blk_label = st.text_input("Label",       value="Work",  key="blk_lbl",   placeholder="Label",  label_visibility="collapsed")
                blk_start = st.text_input("Start (HH:MM)", value="09:00", key="blk_start", placeholder="09:00",  label_visibility="collapsed")
            with bb2:
                blk_end  = st.text_input("End (HH:MM)",  value="17:00", key="blk_end",   placeholder="17:00",  label_visibility="collapsed")
                blk_freq = st.selectbox("Frequency", ["weekdays", "daily", "weekends"],  key="blk_freq",        label_visibility="collapsed")

            if st.button("＋ Add Block", use_container_width=True):
                st.session_state.owner.add_availability(
                    AvailabilityBlock(label=blk_label, start_time=blk_start,
                                      end_time=blk_end, frequency=blk_freq)
                )
                save()
                st.rerun()

            for i, b in enumerate(st.session_state.owner.availability):
                bc, bd = st.columns([5, 1])
                with bc:
                    st.caption(f"⛔ **{b.label}** · {b.start_time}–{b.end_time} · _{b.frequency}_")
                with bd:
                    if st.button("✕", key=f"del_blk_{i}"):
                        st.session_state.owner.availability.pop(i)
                        save(); st.rerun()

            if not st.session_state.owner.availability:
                st.caption("No blocks — full day is available.")

    # ── Pets ───────────────────────────────────────────────────────────
    no_pets = st.session_state.owner is not None and not st.session_state.pets
    with st.expander("🐾 Pets", expanded=no_pets):
        if st.session_state.owner is None:
            st.caption("Set up your owner profile first.")
        else:
            pc1, pc2, pc3 = st.columns([3, 2, 1])
            with pc1:
                pet_name = st.text_input("Pet name", placeholder="e.g. Mochi", key="new_pet_name", label_visibility="collapsed")
            with pc2:
                species  = st.selectbox("Species", ["dog", "cat", "other"], key="new_pet_species", label_visibility="collapsed")
            with pc3:
                age      = st.number_input("Age", min_value=0, max_value=30, value=2, key="new_pet_age", label_visibility="collapsed")

            if st.button("＋ Add Pet", type="primary", use_container_width=True):
                if not pet_name.strip():
                    st.warning("Enter a pet name.")
                elif pet_name.strip() in [p.name for p in st.session_state.pets]:
                    st.warning(f"'{pet_name}' already exists.")
                else:
                    st.session_state.pets.append(Pet(name=pet_name.strip(), species=species, age=age))
                    save(); st.success(f"{pet_name.strip()} added!"); st.rerun()

            if st.session_state.pets:
                st.divider()
                for i, pet in enumerate(st.session_state.pets):
                    icon = SPECIES_ICON.get(pet.species, "🐾")
                    pc_info, pc_del = st.columns([5, 1])
                    with pc_info:
                        st.markdown(f"{icon} **{pet.name}** · {pet.species} · {len(pet.care_tasks)} task(s)")
                    with pc_del:
                        if st.button("✕", key=f"del_pet_{i}"):
                            st.session_state.pets.pop(i)
                            st.session_state.plans.pop(pet.name, None)
                            save(); st.rerun()

    # ── Tasks ──────────────────────────────────────────────────────────
    has_pets = bool(st.session_state.pets)
    with st.expander("📋 Tasks", expanded=has_pets):
        if not st.session_state.pets:
            st.caption("Add a pet first.")
        else:
            sel_pet_name = st.selectbox(
                "Pet", [p.name for p in st.session_state.pets],
                key="task_pet_sel", label_visibility="collapsed",
            )
            sel_pet = next(p for p in st.session_state.pets if p.name == sel_pet_name)

            tc1, tc2 = st.columns(2)
            with tc1:
                t_name = st.text_input("Task name", placeholder="e.g. Morning Walk", key="t_name", label_visibility="collapsed")
                t_type = st.selectbox("Type", ["exercise", "nutrition", "hygiene", "enrichment", "medication"], key="t_type", label_visibility="collapsed")
                t_pri  = st.selectbox("Priority", ["high", "medium", "low"], key="t_pri", label_visibility="collapsed")
            with tc2:
                t_dur  = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="t_dur", label_visibility="collapsed")
                t_freq = st.selectbox("Frequency", ["daily", "weekly", "as needed"], key="t_freq", label_visibility="collapsed")
                t_pref = st.selectbox("Time preference", ["none", "morning", "afternoon", "evening"], key="t_pref", label_visibility="collapsed")

            if st.button("＋ Add Task", type="primary", use_container_width=True):
                if not t_name.strip():
                    st.warning("Enter a task name.")
                else:
                    sel_pet.add_care_task(Task(
                        name=t_name.strip(), task_type=t_type, priority=t_pri,
                        duration=int(t_dur), frequency=t_freq,
                        time_preference=None if t_pref == "none" else t_pref,
                    ))
                    save(); st.success(f"'{t_name.strip()}' added!"); st.rerun()

            # Current task list for selected pet
            all_tasks = sel_pet.get_all_tasks()
            if all_tasks:
                st.divider()
                for task in sorted(all_tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 99)):
                    tl, tr = st.columns([5, 1])
                    with tl:
                        emoji = TYPE_EMOJI.get(task.task_type, "📌")
                        badge = PRIORITY_BADGE.get(task.priority, "")
                        st.markdown(f"{badge} {emoji} **{task.name}** · {task.duration} min")
                    with tr:
                        if st.button("✕", key=f"del_task_{sel_pet_name}_{task.name}"):
                            sel_pet.remove_care_task(task)
                            save(); st.rerun()
            else:
                st.caption("No tasks yet — add one above.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN AREA — live dashboard
# ═══════════════════════════════════════════════════════════════════════

owner_display = st.session_state.owner.name if st.session_state.owner else "there"
total_tasks   = sum(len(p.care_tasks) for p in st.session_state.pets)
pet_count     = len(st.session_state.pets)

# ── Top bar ───────────────────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <h1>🐾 PawPal+</h1>
    <p>Hey {owner_display}! Here's your pet care dashboard.</p>
  </div>
  <div class="topbar-right">
    <div class="date">{TODAY_DISPLAY}</div>
    <div class="meta">{pet_count} pet{'s' if pet_count != 1 else ''} &nbsp;·&nbsp; {total_tasks} task{'s' if total_tasks != 1 else ''}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Guard: need owner + pets ──────────────────────────────────────────
if st.session_state.owner is None:
    st.markdown("""
    <div class="empty-state">
      <span class="icon">👋</span>
      <h3>Welcome to PawPal+</h3>
      <p>Open the sidebar and set up your owner profile to get started.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not st.session_state.pets:
    st.markdown("""
    <div class="empty-state">
      <span class="icon">🐾</span>
      <h3>Add your first pet</h3>
      <p>Open the sidebar → Pets to register your pet.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Schedule controls ─────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([3, 1, 1, 1.5])
with ctrl1:
    pets_to_schedule = st.multiselect(
        "Pets", [p.name for p in st.session_state.pets],
        default=[p.name for p in st.session_state.pets],
        label_visibility="collapsed", placeholder="Select pets to schedule…",
    )
with ctrl2:
    day_start = st.text_input("Start", value="08:00", label_visibility="collapsed", placeholder="08:00")
with ctrl3:
    day_end = st.text_input("End", value="22:00", label_visibility="collapsed", placeholder="22:00")
with ctrl4:
    generate = st.button("🗓  Generate Schedule", type="primary", use_container_width=True)

if generate:
    if not pets_to_schedule:
        st.warning("Select at least one pet to schedule.")
    else:
        generated = []
        for pname in pets_to_schedule:
            pet = next(p for p in st.session_state.pets if p.name == pname)
            if not pet.get_all_tasks():
                st.warning(f"**{pet.name}** has no tasks — skipping.")
                continue
            scheduler = Scheduler(
                owner=st.session_state.owner, pet=pet, date=TODAY,
                day_start=day_start, day_end=day_end,
            )
            load    = scheduler.check_day_load(pet.get_all_tasks())
            batches = scheduler.batch_tasks(pet.get_all_tasks())
            plan    = scheduler.build_schedule()
            st.session_state.plans[pname] = {
                "plan":      plan,
                "scheduler": scheduler,
                "explanation": scheduler.explain_plan(plan),
                "load":      load,
                "batches":   batches,
                "deferred_decisions": {t.name: None for t in load["deferred_suggestions"]},
            }
            generated.append(pname)
        if generated:
            st.success(f"✅ Schedule ready for: {', '.join(generated)}")
            st.rerun()

# ── Empty state: no schedule yet ─────────────────────────────────────
if not st.session_state.plans:
    st.markdown("""
    <div class="empty-state">
      <span class="icon">📅</span>
      <h3>No schedule generated yet</h3>
      <p>Select your pets above and hit <strong>Generate Schedule</strong>.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Conflict detection ────────────────────────────────────────────────
all_plans     = [v["plan"] for v in st.session_state.plans.values()]
any_scheduler = next(iter(st.session_state.plans.values()))["scheduler"]
conflicts     = any_scheduler.detect_conflicts(*all_plans)

if conflicts:
    st.error(f"⚠️ **{len(conflicts)} conflict{'s' if len(conflicts) != 1 else ''} detected** — review and resolve below.")
    for ci, conflict in enumerate(conflicts):
        with st.expander(f"Conflict {ci + 1}: {conflict['message']}", expanded=True):
            if conflict["suggestion"]:
                st.markdown(
                    f"💡 **Suggested fix:** Move **{conflict['loser_task'].task.name}** "
                    f"({conflict['loser_pet']}) → **{conflict['suggestion']}**"
                )
                ca, cb = st.columns(2)
                with ca:
                    if st.button("✅ Apply Fix", key=f"fix_{ci}"):
                        conflict["loser_task"].update_start(conflict["suggestion"])
                        end_min = (
                            sum(int(x) * m for x, m in zip(conflict["suggestion"].split(":"), [60, 1]))
                            + conflict["loser_task"].task.duration
                        )
                        conflict["loser_task"].update_finish(f"{end_min // 60:02d}:{end_min % 60:02d}")
                        st.success("Fix applied!"); st.rerun()
                with cb:
                    if st.button("🚫 Ignore", key=f"ignore_{ci}"):
                        st.info("Conflict ignored.")
            else:
                st.warning("No open slot found to resolve this conflict automatically.")
else:
    st.success("✅ No scheduling conflicts detected.")

# ── Sort selector ─────────────────────────────────────────────────────
sort_col, _ = st.columns([2, 5])
with sort_col:
    schedule_sort = st.radio(
        "View by", ["⏱ time", "🔴 priority", "🗂 batched", "📋 consolidated"],
        horizontal=True, label_visibility="collapsed",
    )
sort_key = schedule_sort.split(" ")[1]   # strip emoji

st.write("")

# ── Consolidated view ─────────────────────────────────────────────────
if sort_key == "consolidated":
    # Overall stats across all pets
    total_all    = sum(len(e["plan"].scheduled_tasks) for e in st.session_state.plans.values())
    complete_all = sum(
        sum(1 for s in e["plan"].scheduled_tasks if s.is_complete)
        for e in st.session_state.plans.values()
    )
    remaining_all = total_all - complete_all
    prog_all      = complete_all / total_all if total_all > 0 else 0.0

    ca, cb = st.columns([4, 2])
    with ca:
        st.markdown("### 📋 All Pets — Combined Schedule")
    with cb:
        st.markdown(
            f"<div style='text-align:right;padding-top:10px;font-size:0.8rem;color:#94a3b8'>"
            f"{complete_all}/{total_all} complete"
            f"{'&nbsp;·&nbsp;' + str(remaining_all) + ' left' if remaining_all else ' — all done 🎉'}"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.progress(prog_all)
    st.write("")
    _render_consolidated(st.session_state.plans)
    st.stop()

# ── Per-pet schedule cards ────────────────────────────────────────────
for pname, entry in st.session_state.plans.items():
    plan    = entry["plan"]
    load    = entry["load"]
    batches = entry["batches"]
    pet_obj = next((p for p in st.session_state.pets if p.name == pname), None)
    icon    = SPECIES_ICON.get(pet_obj.species if pet_obj else "other", "🐾")
    status  = plan.get_completion_status()
    prog    = status["complete"] / status["total"] if status["total"] > 0 else 0.0

    with st.container():
        # Card header
        h1, h2 = st.columns([4, 2])
        with h1:
            st.markdown(f"### {icon} {pname}")
        with h2:
            st.markdown(
                f"<div style='text-align:right;padding-top:10px;font-size:0.8rem;color:#94a3b8'>"
                f"{status['complete']}/{status['total']} complete"
                f"{'&nbsp;·&nbsp;' + str(status['remaining']) + ' left' if status['remaining'] else ' — all done 🎉'}"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.progress(prog)

        if not plan.scheduled_tasks:
            st.warning(f"No tasks could be scheduled for **{pname}** — check your busy blocks.")
            st.divider()
            continue

        # Day load warning + deferral UI
        if load["overloaded"]:
            st.warning(
                f"⏱ **Day overloaded:** {load['total_task_minutes']} min of tasks, "
                f"only {load['available_minutes']} min available."
            )
            if load["deferred_suggestions"]:
                with st.expander(f"📋 {len(load['deferred_suggestions'])} deferral suggestion(s)"):
                    for dt in load["deferred_suggestions"]:
                        dl1, dl2, dl3 = st.columns([4, 1, 1])
                        with dl1:
                            st.markdown(
                                f"{PRIORITY_BADGE.get(dt.priority, '')} **{dt.name}** "
                                f"· {dt.duration} min · _{dt.priority}_"
                            )
                        with dl2:
                            if st.button("Keep", key=f"keep_{pname}_{dt.name}"):
                                entry["deferred_decisions"][dt.name] = "keep"; st.rerun()
                        with dl3:
                            if st.button("Defer", key=f"defer_{pname}_{dt.name}"):
                                entry["deferred_decisions"][dt.name] = "defer"; st.rerun()

        # Column headers
        st.markdown(
            "<div style='display:flex;gap:10px;padding:4px 12px;"
            "font-size:0.7rem;font-weight:700;letter-spacing:0.06em;"
            "text-transform:uppercase;color:#94a3b8;margin-bottom:2px;'>"
            "<span style='min-width:16px'></span>"
            "<span style='min-width:108px'>Time</span>"
            "<span style='flex:1'>Task</span>"
            "<span style='min-width:46px;text-align:right'>Dur</span>"
            "<span style='min-width:90px'></span>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Schedule rows
        if sort_key == "time":
            _render_flat(entry["scheduler"].sort_by_time(plan), pname)
        elif sort_key == "priority":
            _render_flat(
                sorted(plan.scheduled_tasks, key=lambda s: PRIORITY_ORDER.get(s.task.priority, 99)),
                pname,
            )
        elif sort_key == "batched":
            _render_batched(batches, plan, pname)

        with st.expander("💡 Why this schedule?"):
            st.text(entry["explanation"])

        st.divider()
