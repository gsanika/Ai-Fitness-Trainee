import streamlit as st
import json
import os
import glob
import random
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
st.set_page_config(
    page_title="AI Fitness Trainer",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

LOG_DIR = "workout_logs"

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

EXERCISE_GUIDE = {
    "SQUAT": {
        "emoji": "🦵", "muscles": "Quads · Glutes · Hamstrings · Core",
        "key_joints": "Hip · Knee · Ankle",
        "angles": "Standing ~170° knee → Bottom ~90° knee",
        "difficulty": 3,
        "tips": ["Keep chest tall and core braced", "Drive knees out over toes", "Weight through heels on the way up", "Aim to break parallel for full ROM"],
        "camera": "Side-on view for best knee angle detection",
    },
    "PUSH-UP": {
        "emoji": "💪", "muscles": "Chest · Triceps · Shoulders · Core",
        "key_joints": "Shoulder · Elbow · Wrist",
        "angles": "Top ~160° elbow → Bottom ~80° elbow",
        "difficulty": 2,
        "tips": ["Maintain a rigid plank — no sagging hips", "Elbows at ~45° from body", "Lower chest to 2-3 cm from floor", "Exhale on the push up"],
        "camera": "Side-on view so elbow bend is visible",
    },
    "BICEP CURL": {
        "emoji": "🏋️", "muscles": "Biceps · Brachialis · Forearms",
        "key_joints": "Shoulder · Elbow · Wrist",
        "angles": "Bottom ~150° elbow → Top ~40° elbow",
        "difficulty": 1,
        "tips": ["Keep elbows pinned at your sides", "Supinate wrist at the top", "Control the lowering phase", "Curl both arms evenly"],
        "camera": "Face the camera with arms clearly visible",
    },
    "LUNGE": {
        "emoji": "🏃", "muscles": "Quads · Glutes · Hamstrings · Calves",
        "key_joints": "Hip · Knee · Ankle",
        "angles": "Standing ~170° → Front knee ~100° at bottom",
        "difficulty": 2,
        "tips": ["Front knee must stay behind toes", "Keep torso upright", "Push through front heel to stand", "Stand fully upright between reps"],
        "camera": "Side-on view works best",
    },
    "JUMPING JACK": {
        "emoji": "🙌", "muscles": "Full body · Calves · Shoulders · Core",
        "key_joints": "Shoulder · Hip · Wrist · Ankle",
        "angles": "Arms down <45° → up >130° AND feet close → wide",
        "difficulty": 1,
        "tips": ["Arms AND feet must move together to count", "Fully extend arms overhead", "Land softly on balls of feet", "Keep core tight throughout"],
        "camera": "Full body in frame — step back from camera",
    },
    "HIGH KNEES": {
        "emoji": "🦿", "muscles": "Hip Flexors · Quads · Core · Calves",
        "key_joints": "Hip · Knee",
        "angles": "Knee Y must rise above Hip Y by 6% of frame height",
        "difficulty": 1,
        "tips": ["Drive knees up to hip height or above", "Pump arms for rhythm", "Land lightly and alternate fast", "Each leg lift = 1 rep"],
        "camera": "Face the camera, full legs visible",
    },
    "TWIST JUMP": {
        "emoji": "🌀", "muscles": "Obliques · Core · Hips · Glutes",
        "key_joints": "Shoulder midpoint vs Hip midpoint",
        "angles": "Shoulder-hip offset > 25% of shoulder width = twist",
        "difficulty": 2,
        "tips": ["Twist hips left and right, shoulders stay forward", "Full left + full right = 1 rep", "Start slow before adding jump", "Soft knees on landing"],
        "camera": "Face the camera straight-on",
    },
    "ELBOW-KNEE": {
        "emoji": "🤸", "muscles": "Obliques · Core · Hip Flexors",
        "key_joints": "Elbow · Opposite Knee",
        "angles": "Elbow-to-knee distance < 20% of frame height",
        "difficulty": 2,
        "tips": ["Left elbow to right knee, right elbow to left knee", "Crunch elbow down to knee", "Keep core engaged throughout", "Full body must be in frame"],
        "camera": "Full body — head to knee in frame",
    },
    "SHOULDER PRESS": {
        "emoji": "🔝", "muscles": "Deltoids · Triceps · Upper Traps",
        "key_joints": "Shoulder · Elbow · Wrist",
        "angles": "Hands at ears ~90° → Overhead ~160°",
        "difficulty": 2,
        "tips": ["Start with hands at ear height", "Press directly overhead", "Lock arms fully at the top", "Lower slowly with control"],
        "camera": "Face the camera with arms visible",
    },
    "PLANK": {
        "emoji": "🪵", "muscles": "Core · Shoulders · Glutes · Back",
        "key_joints": "Shoulder · Hip · Ankle",
        "angles": "Body alignment angle must stay > 155°",
        "difficulty": 2,
        "tips": ["Straight line from shoulder to ankle", "Don't let hips sag or pike", "Engage glutes and core together", "+1 rep every 5 seconds held"],
        "camera": "Side-on view for body alignment",
    },
}


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
    
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏋️ AI FITNESS</div>', unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigate", ["📊 Dashboard", "📅 History", "💡 Exercise Guide", "⚙️ Settings"])
    st.markdown("---")
    st.markdown("**Quick Start**")
    st.code("python fitness_trainer.py", language="bash")
    st.markdown('<div class="tip-box">Press <b>1–9, 0</b> to switch exercise<br><b>S</b> to save · <b>R</b> to reset · <b>ESC</b> quit</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Exercise Keys**")
    for ex, key in EXERCISE_KEY.items():
        st.markdown(f"`{key}` {EXERCISE_EMOJI.get(ex,'')} {ex.title()}")
    st.markdown("---")
    st.caption("v2.0 · AI Fitness Trainer · 10 Exercises")


sessions = load_sessions()
using_demo = len(sessions) == 0
if using_demo:
    sessions = generate_demo_sessions()
    st.info("📊 Showing **demo data** — run `python fitness_trainer.py` and press **S** to save a real session.", icon="ℹ️")

if page == "📊 Dashboard":
    st.markdown("# 📊 WORKOUT DASHBOARD")

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

    # Exercise breakdown
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
