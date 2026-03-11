import streamlit as st
import json
import os
import glob
import random
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
import subprocess
import sys
import platform
import time

st.set_page_config(
    page_title="AI Fitness Trainer",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS (unchanged) ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0a0a14; color: #e0e0ff; }
.stApp { background-color: #0a0a14; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }
.metric-card { background: linear-gradient(135deg, #141428 0%, #1e1e3a 100%); border: 1px solid #2a2a50; border-radius: 16px; padding: 24px 20px; text-align: center; margin: 8px 0; }
.metric-card .value { font-family: 'Bebas Neue', sans-serif; font-size: 3rem; color: #00e5ff; line-height: 1.1; }
.metric-card .label { font-size: 0.75rem; color: #8888aa; text-transform: uppercase; letter-spacing: 2px; margin-top: 4px; }
.exercise-card { background: linear-gradient(135deg, #0f0f22 0%, #1a1a35 100%); border: 1px solid #2a2a60; border-radius: 14px; padding: 20px; margin: 8px 0; }
.exercise-card:hover { border-color: #00e5ff; }
.exercise-card .ex-name { font-family: 'Bebas Neue', sans-serif; font-size: 1.2rem; color: #00e5ff; letter-spacing: 2px; }
.exercise-card .ex-reps { font-size: 2.2rem; font-weight: 700; color: #fff; }
.exercise-card .ex-cal { font-size: 0.85rem; color: #ffb830; }
.badge-good { background:#1a3d1a; color:#4cff88; border-radius:20px; padding:3px 12px; font-size:0.72rem; }
.section-header { font-family: 'Bebas Neue', sans-serif; font-size: 1.7rem; color: #c0c0ff; letter-spacing: 3px; border-bottom: 2px solid #2a2a60; padding-bottom: 6px; margin: 24px 0 16px 0; }
.sidebar-title { font-family: 'Bebas Neue', sans-serif; font-size: 2rem; color: #00e5ff; letter-spacing: 3px; }
.tip-box { background: linear-gradient(135deg, #0d1a2d, #1a2a1a); border-left: 4px solid #00ff99; border-radius: 0 12px 12px 0; padding: 14px; margin: 10px 0; font-size: 0.88rem; color: #b0ffcc; }
.warn-box { background: linear-gradient(135deg, #2d1a0d, #2a1a00); border-left: 4px solid #ffb830; border-radius: 0 12px 12px 0; padding: 14px; margin: 10px 0; font-size: 0.88rem; color: #ffe0a0; }
.stProgress > div > div { background-color: #00e5ff !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
LOG_DIR = "workout_logs"
LIVE_STATE_FILE = "live_state.json"

ALL_EXERCISES = [
    "SQUAT", "PUSH-UP", "BICEP CURL", "LUNGE",
    "JUMPING JACK", "HIGH KNEES", "TWIST JUMP",
    "ELBOW-KNEE", "SHOULDER PRESS", "PLANK"
]

EXERCISE_EMOJI = {
    "SQUAT": "🦵", "PUSH-UP": "💪", "BICEP CURL": "🏋️", "LUNGE": "🏃",
    "JUMPING JACK": "🙌", "HIGH KNEES": "🦿", "TWIST JUMP": "🌀",
    "ELBOW-KNEE": "🤸", "SHOULDER PRESS": "🔝", "PLANK": "🪵",
}

EXERCISE_KEY = {
    "SQUAT": "1", "PUSH-UP": "2", "BICEP CURL": "3", "LUNGE": "4",
    "JUMPING JACK": "5", "HIGH KNEES": "6", "TWIST JUMP": "7",
    "ELBOW-KNEE": "8", "SHOULDER PRESS": "9", "PLANK": "0"
}

CALORIES_PER_REP = {
    "SQUAT": 0.32, "PUSH-UP": 0.29, "BICEP CURL": 0.14, "LUNGE": 0.30,
    "JUMPING JACK": 0.10, "HIGH KNEES": 0.08, "TWIST JUMP": 0.15,
    "ELBOW-KNEE": 0.12, "SHOULDER PRESS": 0.19, "PLANK": 0.25,
}

EXERCISE_GUIDE = { ... }  # (unchanged – keep your existing full dictionary)

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_sessions():
    if not os.path.exists(LOG_DIR):
        return []
    files = sorted(glob.glob(os.path.join(LOG_DIR, "*.json")), reverse=True)
    sessions = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fp:
                sessions.append(json.load(fp))
        except Exception:
            pass
    return sessions

def generate_demo_sessions():
    random.seed(42)
    sessions = []
    base_date = datetime(2026, 3, 9)
    for day_offset in range(10):
        date = (base_date - timedelta(days=day_offset)).strftime("%Y-%m-%d %H:%M:%S")
        chosen = random.sample(ALL_EXERCISES, k=random.randint(3, 6))
        exs = {}
        for ex in chosen:
            reps = random.randint(10, 30)
            exs[ex] = {"reps": reps, "calories": round(CALORIES_PER_REP.get(ex, 0.2) * reps, 2)}
        sessions.append({"date": date, "exercises": exs})
    return sessions

def compute_streak(sessions):
    if not sessions:
        return 0
    dates = set()
    for s in sessions:
        try:
            dates.add(datetime.strptime(s["date"][:10], "%Y-%m-%d").date())
        except Exception:
            pass
    today = datetime.now().date()
    streak = 0
    check = today
    while check in dates:
        streak += 1
        check -= timedelta(days=1)
    return streak

def read_live_state():
    """Return live state dict if file exists and is recent, else None."""
    try:
        if not os.path.exists(LIVE_STATE_FILE):
            return None
        mtime = os.path.getmtime(LIVE_STATE_FILE)
        if time.time() - mtime > 3:   # older than 3 seconds → stale
            return None
        with open(LIVE_STATE_FILE, "r") as f:
            state = json.load(f)
        if not state.get("active", False):
            return None
        return state
    except Exception:
        return None

# ── Sidebar (with launch button) ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏋️ AI FITNESS</div>', unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigate", ["📊 Dashboard", "📅 History", "💡 Exercise Guide", "⚙️ Settings"])
    st.markdown("---")

    st.markdown("**Quick Start**")
    if "launch_msg" not in st.session_state:
        st.session_state.launch_msg = ""

    if st.button("▶️ Launch Fitness Trainer", use_container_width=True):
        try:
            system = platform.system()
            script = "fitness_trainer.py"
            if system == "Windows":
                subprocess.Popen(["start", "cmd", "/k", "python", script], shell=True)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", "-a", "Terminal", "python", script])
            else:  # Linux (gnome-terminal)
                subprocess.Popen(["gnome-terminal", "--", "python", script])
            st.session_state.launch_msg = "✅ Trainer launched in a new window."
        except Exception as e:
            st.session_state.launch_msg = f"❌ Could not launch: {e}"

    if st.session_state.launch_msg:
        if "✅" in st.session_state.launch_msg:
            st.success(st.session_state.launch_msg)
        else:
            st.error(st.session_state.launch_msg)

    st.markdown('<div class="tip-box">Press <b>1–9, 0</b> to switch exercise<br><b>S</b> to save · <b>R</b> to reset · <b>ESC</b> quit</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Exercise Keys**")
    for ex, key in EXERCISE_KEY.items():
        st.markdown(f"`{key}` {EXERCISE_EMOJI.get(ex,'')} {ex.title()}")
    st.markdown("---")
    st.caption("v2.0 · AI Fitness Trainer · 10 Exercises")

# ── Load historical data ─────────────────────────────────────────────────────
sessions = load_sessions()
using_demo = len(sessions) == 0
if using_demo:
    sessions = generate_demo_sessions()
    if page == "📊 Dashboard":
        st.info("📊 Showing **demo data** — run `python fitness_trainer.py` and press **S** to save a real session.", icon="ℹ️")

# ── PAGE: DASHBOARD ──────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.markdown("# 📊 WORKOUT DASHBOARD")

    # Check for live session
    live = read_live_state()
    if live:
        # Auto‑refresh every 2 seconds while live data exists
        st.markdown("""
        <meta http-equiv="refresh" content="2">
        <div style="background: #0a1f1a; padding: 10px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #00ff99;">
            🔴 <b>Live session active</b> — dashboard refreshes automatically every 2 seconds.
        </div>
        """, unsafe_allow_html=True)

        # Show live stats in a prominent card
        st.markdown('<div class="section-header">⚡ LIVE SESSION</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="value">{live.get('exercise', '?')}</div>
                <div class="label">Current Exercise</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="value">{live.get('reps', 0)}</div>
                <div class="label">Reps This Session</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="value">{live.get('calories', 0):.1f}</div>
                <div class="label">Calories Burned</div>
            </div>
            """, unsafe_allow_html=True)

        # Option to stop the live session (kill the trainer process)
        if st.button("🛑 Stop Session", type="primary"):
            try:
                if platform.system() == "Windows":
                    os.system("taskkill /f /im python.exe")  # be careful – kills all Python?
                else:
                    os.system("pkill -f fitness_trainer.py")
                st.success("Session stopped.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Could not stop: {e}")

        st.markdown("---")

    # Below live section, show historical summary (same as before)
    total_sessions = len(sessions)
    all_reps       = sum(ex["reps"] for s in sessions for ex in s["exercises"].values())
    all_calories   = sum(ex["calories"] for s in sessions for ex in s["exercises"].values())
    streak         = compute_streak(sessions)
    latest         = sessions[0] if sessions else {}

    c1, c2, c3, c4 = st.columns(4)
    for col, (val, label) in zip(
        [c1, c2, c3, c4],
        [(total_sessions, "Sessions"), (all_reps, "Total Reps"),
         (f"{all_calories:.0f}", "Calories Burned"), (f"{streak} 🔥", "Day Streak")]
    ):
        with col:
            st.markdown(f'<div class="metric-card"><div class="value">{val}</div><div class="label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("")
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-header">Latest Session</div>', unsafe_allow_html=True)
        if latest.get("exercises"):
            st.caption(f"🗓 {latest.get('date','')[:16]}")
            for ex_name, data in latest["exercises"].items():
                emoji = EXERCISE_EMOJI.get(ex_name, "")
                st.markdown(f"""
                <div class="exercise-card">
                    <div class="ex-name">{emoji} {ex_name} <span class="badge-good">✓ Done</span></div>
                    <div class="ex-reps">{data['reps']} <span style="font-size:1rem;color:#888">reps</span></div>
                    <div class="ex-cal">🔥 {data['calories']} kcal</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.write("No session data yet.")

    with col_r:
        st.markdown('<div class="section-header">7-Day Volume</div>', unsafe_allow_html=True)
        rows = []
        for s in reversed(sessions[:7]):
            try:
                dl = datetime.strptime(s["date"][:10], "%Y-%m-%d").strftime("%b %d")
            except Exception:
                dl = s["date"][:10]
            rows.append({
                "Date": dl,
                "Reps": sum(e["reps"] for e in s["exercises"].values()),
                "Calories": round(sum(e["calories"] for e in s["exercises"].values()), 1)
            })
        if rows:
            df = pd.DataFrame(rows).set_index("Date")
            tab1, tab2 = st.tabs(["📊 Reps", "🔥 Calories"])
            with tab1:
                st.bar_chart(df[["Reps"]], color="#00e5ff")
            with tab2:
                st.bar_chart(df[["Calories"]], color="#ffb830")

    # Exercise breakdown (same as before)
    st.markdown('<div class="section-header">All-Time Exercise Breakdown</div>', unsafe_allow_html=True)
    ex_totals = defaultdict(lambda: {"reps": 0, "calories": 0.0, "sessions": 0})
    for s in sessions:
        for ex_name, data in s["exercises"].items():
            ex_totals[ex_name]["reps"]     += data["reps"]
            ex_totals[ex_name]["calories"] += data["calories"]
            ex_totals[ex_name]["sessions"] += 1

    if ex_totals:
        max_reps = max(v["reps"] for v in ex_totals.values()) or 1
        items = list(ex_totals.items())
        for row_start in range(0, len(items), 5):
            row_items = items[row_start:row_start+5]
            cols = st.columns(len(row_items))
            for col, (name, stats) in zip(cols, row_items):
                with col:
                    pct = int(stats["reps"] / max_reps * 100)
                    st.markdown(f"""
                    <div class="exercise-card" style="text-align:center">
                        <div style="font-size:1.6rem">{EXERCISE_EMOJI.get(name,'')}</div>
                        <div class="ex-name" style="font-size:0.95rem">{name}</div>
                        <div class="ex-reps" style="font-size:2rem">{stats['reps']}</div>
                        <div style="font-size:0.72rem;color:#888">{stats['sessions']} session(s)</div>
                        <div class="ex-cal">🔥 {stats['calories']:.1f} kcal</div>
                    </div>""", unsafe_allow_html=True)
                    st.progress(pct)

    # Insights row
    if len(ex_totals) >= 2:
        st.markdown('<div class="section-header">Insights</div>', unsafe_allow_html=True)
        sorted_ex = sorted(ex_totals.items(), key=lambda x: x[1]["reps"], reverse=True)
        top    = sorted_ex[0]
        bottom = sorted_ex[-1]
        avg_rps = round(all_reps / total_sessions, 1) if total_sessions else 0
        i1, i2, i3 = st.columns(3)
        with i1:
            st.markdown(f"""<div class="exercise-card" style="text-align:center">
                <div style="font-size:0.72rem;color:#8888aa;letter-spacing:2px">MOST TRAINED</div>
                <div style="font-size:1.8rem">{EXERCISE_EMOJI.get(top[0],'')}</div>
                <div class="ex-name">{top[0]}</div>
                <div class="ex-reps" style="font-size:1.8rem">{top[1]['reps']} reps</div>
            </div>""", unsafe_allow_html=True)
        with i2:
            st.markdown(f"""<div class="exercise-card" style="text-align:center">
                <div style="font-size:0.72rem;color:#8888aa;letter-spacing:2px">AVG REPS / SESSION</div>
                <div style="font-size:1.8rem">📈</div>
                <div class="ex-reps" style="font-size:2.4rem">{avg_rps}</div>
                <div style="font-size:0.8rem;color:#888">reps per session</div>
            </div>""", unsafe_allow_html=True)
        with i3:
            st.markdown(f"""<div class="exercise-card" style="text-align:center">
                <div style="font-size:0.72rem;color:#8888aa;letter-spacing:2px">NEEDS MORE WORK</div>
                <div style="font-size:1.8rem">{EXERCISE_EMOJI.get(bottom[0],'')}</div>
                <div class="ex-name">{bottom[0]}</div>
                <div class="ex-reps" style="font-size:1.8rem">{bottom[1]['reps']} reps</div>
            </div>""", unsafe_allow_html=True)

# ── PAGE: HISTORY (unchanged) ────────────────────────────────────────────────
elif page == "📅 History":
    st.markdown("# 📅 WORKOUT HISTORY")
    if not sessions:
        st.warning("No sessions found. Run the trainer and press S to save.")
    else:
        summary_rows = []
        for s in sessions:
            reps = sum(e["reps"] for e in s["exercises"].values())
            cal  = sum(e["calories"] for e in s["exercises"].values())
            exs  = ", ".join(f"{EXERCISE_EMOJI.get(k,'')} {k.title()}" for k in s["exercises"].keys())
            summary_rows.append({"Date": s.get("date","")[:16], "Exercises": exs,
                                  "Total Reps": reps, "Calories": round(cal, 1)})
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        st.markdown('<div class="section-header">Session Details</div>', unsafe_allow_html=True)
        for s in sessions:
            session_reps = sum(e["reps"] for e in s["exercises"].values())
            session_cal  = sum(e["calories"] for e in s["exercises"].values())
            date_str     = s.get("date", "Unknown")[:16]
            ex_count     = len(s["exercises"])
            with st.expander(f"📅 {date_str}  ·  {ex_count} exercises  ·  {session_reps} reps  ·  {session_cal:.1f} kcal"):
                ex_items = list(s["exercises"].items())
                for row_start in range(0, len(ex_items), 4):
                    row = ex_items[row_start:row_start+4]
                    cols = st.columns(len(row))
                    for col, (ex_name, data) in zip(cols, row):
                        with col:
                            st.markdown(f"""
                            <div class="exercise-card" style="text-align:center">
                                <div style="font-size:1.4rem">{EXERCISE_EMOJI.get(ex_name,'')}</div>
                                <div class="ex-name" style="font-size:0.9rem">{ex_name}</div>
                                <div class="ex-reps" style="font-size:1.8rem">{data['reps']}</div>
                                <div style="color:#888;font-size:0.75rem">reps</div>
                                <div class="ex-cal">🔥 {data['calories']} kcal</div>
                            </div>""", unsafe_allow_html=True)

# ── PAGE: EXERCISE GUIDE (unchanged) ─────────────────────────────────────────
elif page == "💡 Exercise Guide":
    st.markdown("# 💡 EXERCISE GUIDE")
    st.caption("All 10 exercises supported by the AI Fitness Trainer.")

    diff_filter = st.select_slider("Filter by difficulty",
                                   options=["All", "★☆☆ Easy", "★★☆ Medium", "★★★ Hard"],
                                   value="All")
    diff_map = {"All": None, "★☆☆ Easy": 1, "★★☆ Medium": 2, "★★★ Hard": 3}
    selected_diff = diff_map[diff_filter]

    for ex_name, info in EXERCISE_GUIDE.items():
        if selected_diff and info["difficulty"] != selected_diff:
            continue
        diff_stars = "★" * info["difficulty"] + "☆" * (3 - info["difficulty"])
        key_num    = EXERCISE_KEY.get(ex_name, "?")
        with st.expander(f"{info['emoji']}  {ex_name}  ·  Key `{key_num}`  ·  {diff_stars}"):
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(f"**Muscles:** {info['muscles']}")
                st.markdown(f"**Key Joints:** `{info['key_joints']}`")
                st.markdown(f"**Detection Logic:** `{info['angles']}`")
                st.markdown("**Form Tips:**")
                for tip in info["tips"]:
                    st.markdown(f"- {tip}")
            with c2:
                st.markdown(f"**Difficulty:** {diff_stars}")
                st.markdown(f'<div class="tip-box"><b>📸 Camera tip:</b><br>{info["camera"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="warn-box"><b>⌨️ Shortcut:</b> Press <b>{key_num}</b> in the trainer window to switch to this exercise.</div>', unsafe_allow_html=True)

# ── PAGE: SETTINGS (unchanged) ───────────────────────────────────────────────
elif page == "⚙️ Settings":
    st.markdown("# ⚙️ SETTINGS")
    existing = {}
    settings_path = os.path.join("config", "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, encoding="utf-8") as f:
                existing = json.load(f)
            st.success("✅ Loaded existing settings from config/settings.json")
        except Exception:
            pass

    st.markdown('<div class="section-header">Webcam</div>', unsafe_allow_html=True)
    cam_idx = st.selectbox("Camera index", [0, 1, 2], index=existing.get("cam_idx", 0))
    res     = st.selectbox("Resolution", ["1280x720", "960x540", "640x480"],
                           index=["1280x720","960x540","640x480"].index(existing.get("resolution","1280x720")) if existing.get("resolution","1280x720") in ["1280x720","960x540","640x480"] else 0)

    st.markdown('<div class="section-header">Pose Detection</div>', unsafe_allow_html=True)
    complexity_opts   = ["Lite (fast)", "Full (accurate)"]
    default_comp      = 0 if existing.get("model_complexity", 1) == 0 else 1
    complexity        = st.radio("Model complexity", complexity_opts, index=default_comp)
    min_conf          = st.slider("Min detection confidence", 0.3, 0.9, float(existing.get("min_detection_confidence", 0.6)), 0.05)
    min_track         = st.slider("Min tracking confidence",  0.3, 0.9, float(existing.get("min_tracking_confidence",  0.6)), 0.05)

    st.markdown('<div class="section-header">Feedback</div>', unsafe_allow_html=True)
    angle_vis = st.toggle("Show angle overlays on video", value=existing.get("angle_visualization", True))
    st.toggle("Voice feedback", value=False, disabled=True, help="Coming in a future update")

    st.markdown('<div class="section-header">User Profile</div>', unsafe_allow_html=True)
    st.caption("Used for more accurate calorie estimation.")
    col1, col2, col3 = st.columns(3)
    with col1:
        weight = st.number_input("Weight (kg)", 40, 150, int(existing.get("weight_kg", 70)))
    with col2:
        age    = st.number_input("Age", 15, 80, int(existing.get("age", 28)))
    with col3:
        gender = st.selectbox("Gender", ["Male", "Female", "Other"],
                              index=["Male","Female","Other"].index(existing.get("gender","Male")))

    st.markdown('<div class="section-header">Startup Default</div>', unsafe_allow_html=True)
    default_ex = st.selectbox("Start with exercise", ALL_EXERCISES,
                              index=ALL_EXERCISES.index(existing.get("default_exercise","SQUAT")))

    st.markdown("")
    if st.button("💾 Save Settings", type="primary"):
        cfg = {
            "cam_idx": cam_idx, "resolution": res,
            "model_complexity": 0 if "Lite" in complexity else 1,
            "min_detection_confidence": min_conf,
            "min_tracking_confidence":  min_track,
            "angle_visualization": angle_vis,
            "weight_kg": weight, "age": age,
            "gender": gender, "default_exercise": default_ex,
        }
        os.makedirs("config", exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        st.success("✅ Settings saved to config/settings.json")
        st.json(cfg)
