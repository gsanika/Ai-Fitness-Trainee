"""
AI Fitness Trainer – Streamlit Workout Dashboard
Run with: streamlit run dashboard.py
"""

import streamlit as st
import json
import os
import glob
from datetime import datetime
import random

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Fitness Trainer",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a14;
    color: #e0e0ff;
}

.stApp { background-color: #0a0a14; }

h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }

.metric-card {
    background: linear-gradient(135deg, #141428 0%, #1e1e3a 100%);
    border: 1px solid #2a2a50;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    margin: 8px 0;
}
.metric-card .value {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    color: #00e5ff;
    line-height: 1.1;
}
.metric-card .label {
    font-size: 0.75rem;
    color: #8888aa;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 4px;
}

.exercise-card {
    background: linear-gradient(135deg, #0f0f22 0%, #1a1a35 100%);
    border: 1px solid #2a2a60;
    border-radius: 14px;
    padding: 20px;
    margin: 8px 0;
    transition: border-color 0.2s;
}
.exercise-card:hover { border-color: #00e5ff; }
.exercise-card .ex-name {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.5rem;
    color: #00e5ff;
    letter-spacing: 2px;
}
.exercise-card .ex-reps {
    font-size: 2.5rem;
    font-weight: 700;
    color: #fff;
}
.exercise-card .ex-cal {
    font-size: 0.85rem;
    color: #ffb830;
}

.badge-good  { background:#1a3d1a; color:#4cff88; border-radius:20px; padding:4px 14px; font-size:0.75rem; }
.badge-warn  { background:#3d2a00; color:#ffb830; border-radius:20px; padding:4px 14px; font-size:0.75rem; }

.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    color: #c0c0ff;
    letter-spacing: 3px;
    border-bottom: 2px solid #2a2a60;
    padding-bottom: 6px;
    margin: 24px 0 16px 0;
}

.sidebar-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    color: #00e5ff;
    letter-spacing: 3px;
}

.tip-box {
    background: linear-gradient(135deg, #0d1a2d, #1a2a1a);
    border-left: 4px solid #00ff99;
    border-radius: 0 12px 12px 0;
    padding: 16px;
    margin: 12px 0;
    font-size: 0.9rem;
    color: #b0ffcc;
}

.stProgress > div > div { background-color: #00e5ff !important; }
</style>
""", unsafe_allow_html=True)


# ── Load session logs ─────────────────────────────────────────────────────────
LOG_DIR = "workout_logs"

def load_sessions():
    if not os.path.exists(LOG_DIR):
        return []
    files = sorted(glob.glob(os.path.join(LOG_DIR, "*.json")), reverse=True)
    sessions = []
    for f in files:
        try:
            with open(f) as fp:
                sessions.append(json.load(fp))
        except Exception:
            pass
    return sessions


def generate_demo_sessions():
    """Generate demo data when no real sessions exist."""
    exercises = ["SQUAT", "PUSH-UP", "BICEP CURL", "LUNGE"]
    sessions = []
    for day_offset in range(7):
        date = f"2025-03-{9 - day_offset:02d} 08:00:00"
        exs  = {ex: {
            "reps":     random.randint(8, 25),
            "calories": round(random.uniform(2.5, 8.0), 2)
        } for ex in random.sample(exercises, k=random.randint(2, 4))}
        sessions.append({"date": date, "exercises": exs})
    return sessions


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏋️ AI FITNESS</div>', unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio("Navigate", ["📊 Dashboard", "📅 History", "💡 Exercise Guide", "⚙️ Settings"])
    st.markdown("---")

    st.markdown("**Quick Start**")
    st.code("python fitness_trainer.py", language="bash")
    st.markdown('<div class="tip-box">Press <b>1–4</b> to switch exercises, <b>S</b> to save session.</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("v1.0 · AI Fitness Trainer")


# ── Load data ─────────────────────────────────────────────────────────────────
sessions = load_sessions()
using_demo = len(sessions) == 0
if using_demo:
    sessions = generate_demo_sessions()
    st.info("📊 Showing **demo data** – run `fitness_trainer.py` to create real sessions!", icon="ℹ️")


# ════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ════════════════════════════════════════════════════
if page == "📊 Dashboard":

    st.markdown("# 📊 WORKOUT DASHBOARD")

    # Aggregate stats
    total_sessions = len(sessions)
    all_reps       = sum(
        ex["reps"]
        for s in sessions for ex in s["exercises"].values()
    )
    all_calories   = sum(
        ex["calories"]
        for s in sessions for ex in s["exercises"].values()
    )
    latest = sessions[0] if sessions else {}

    # ── KPI Cards ──────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{total_sessions}</div>
            <div class="label">Sessions</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{all_reps}</div>
            <div class="label">Total Reps</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{all_calories:.0f}</div>
            <div class="label">Calories Burned</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        streak = min(total_sessions, 7)
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{streak}</div>
            <div class="label">Day Streak 🔥</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Latest Session + Weekly Volume ──────────────
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.markdown('<div class="section-header">Latest Session</div>', unsafe_allow_html=True)
        if latest.get("exercises"):
            for ex_name, data in latest["exercises"].items():
                badge = '<span class="badge-good">✓ Completed</span>'
                st.markdown(f"""
                <div class="exercise-card">
                    <div class="ex-name">{ex_name} {badge}</div>
                    <div class="ex-reps">{data['reps']} <span style="font-size:1rem;color:#888">reps</span></div>
                    <div class="ex-cal">🔥 {data['calories']} kcal</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.write("No session data yet.")

    with col_r:
        st.markdown('<div class="section-header">7-Day Rep Volume</div>', unsafe_allow_html=True)

        import json as _json  # already imported but just for clarity

        # Build chart data
        chart_labels = []
        chart_values = []
        for s in reversed(sessions[:7]):
            date_str = s["date"][:10]
            reps     = sum(e["reps"] for e in s["exercises"].values())
            chart_labels.append(date_str[-5:])   # MM-DD
            chart_values.append(reps)

        if chart_values:
            import pandas as pd
            df = pd.DataFrame({"Date": chart_labels, "Reps": chart_values})
            st.bar_chart(df.set_index("Date"), color="#00e5ff")

    # ── Per-exercise breakdown ───────────────────────
    st.markdown('<div class="section-header">Exercise Breakdown</div>', unsafe_allow_html=True)

    ex_totals = {}
    for s in sessions:
        for ex_name, data in s["exercises"].items():
            if ex_name not in ex_totals:
                ex_totals[ex_name] = {"reps": 0, "calories": 0, "sessions": 0}
            ex_totals[ex_name]["reps"]     += data["reps"]
            ex_totals[ex_name]["calories"] += data["calories"]
            ex_totals[ex_name]["sessions"] += 1

    if ex_totals:
        max_reps = max(v["reps"] for v in ex_totals.values())
        cols     = st.columns(len(ex_totals))
        for i, (name, stats) in enumerate(ex_totals.items()):
            with cols[i]:
                pct = int(stats["reps"] / max_reps * 100)
                st.markdown(f"""
                <div class="exercise-card" style="text-align:center">
                    <div class="ex-name">{name}</div>
                    <div class="ex-reps">{stats['reps']}</div>
                    <div style="font-size:0.75rem;color:#888">total reps · {stats['sessions']} sessions</div>
                    <div class="ex-cal" style="margin-top:8px">🔥 {stats['calories']:.1f} kcal</div>
                </div>""", unsafe_allow_html=True)
                st.progress(pct)


# ════════════════════════════════════════════════════
# PAGE: HISTORY
# ════════════════════════════════════════════════════
elif page == "📅 History":
    st.markdown("# 📅 WORKOUT HISTORY")

    for i, s in enumerate(sessions):
        session_reps = sum(e["reps"] for e in s["exercises"].values())
        session_cal  = sum(e["calories"] for e in s["exercises"].values())
        date_str     = s.get("date", "Unknown date")

        with st.expander(f"📅 {date_str}  ·  {session_reps} reps  ·  {session_cal:.1f} kcal"):
            cols = st.columns(len(s["exercises"]) or 1)
            for j, (ex_name, data) in enumerate(s["exercises"].items()):
                with cols[j % len(cols)]:
                    st.markdown(f"""
                    <div class="exercise-card" style="text-align:center">
                        <div class="ex-name">{ex_name}</div>
                        <div class="ex-reps">{data['reps']}</div>
                        <div style="color:#888;font-size:0.8rem">reps</div>
                        <div class="ex-cal">🔥 {data['calories']} kcal</div>
                    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# PAGE: EXERCISE GUIDE
# ════════════════════════════════════════════════════
elif page == "💡 Exercise Guide":
    st.markdown("# 💡 EXERCISE GUIDE")

    exercises = {
        "🦵 SQUAT": {
            "key_joints": "Hip · Knee · Ankle",
            "angles": "Standing: ~170° knee · Bottom: ~90° knee",
            "tips": [
                "Keep chest tall and core braced",
                "Drive knees out over toes",
                "Weight through heels on the way up",
                "Aim to break parallel for full ROM"
            ],
            "muscles": "Quads · Glutes · Hamstrings · Core",
            "difficulty": 3,
        },
        "💪 PUSH-UP": {
            "key_joints": "Shoulder · Elbow · Wrist",
            "angles": "Top: ~160° elbow · Bottom: ~80° elbow",
            "tips": [
                "Keep body in a rigid plank",
                "Elbows at ~45° from body",
                "Lower chest to 2–3 cm from floor",
                "Exhale on the push"
            ],
            "muscles": "Chest · Triceps · Shoulders · Core",
            "difficulty": 2,
        },
        "🏋️ BICEP CURL": {
            "key_joints": "Shoulder · Elbow · Wrist",
            "angles": "Bottom: ~150° elbow · Top: ~40° elbow",
            "tips": [
                "Keep elbows tucked at your sides",
                "Avoid swinging the torso",
                "Supinate wrist at the top",
                "Control the eccentric phase"
            ],
            "muscles": "Biceps · Brachialis · Forearms",
            "difficulty": 1,
        },
        "🏃 LUNGE": {
            "key_joints": "Hip · Knee · Ankle",
            "angles": "Front knee: ~100° at bottom · ~170° standing",
            "tips": [
                "Front knee stays behind toe",
                "Torso upright throughout",
                "Push through front heel to rise",
                "Alternate legs for balance"
            ],
            "muscles": "Quads · Glutes · Hamstrings · Calves",
            "difficulty": 2,
        },
    }

    for name, info in exercises.items():
        with st.expander(name):
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(f"**Key Joints:** {info['key_joints']}")
                st.markdown(f"**Angle Targets:** `{info['angles']}`")
                st.markdown(f"**Muscles Worked:** {info['muscles']}")
                st.markdown("**Form Tips:**")
                for tip in info["tips"]:
                    st.markdown(f"- {tip}")
            with c2:
                difficulty_str = "★" * info["difficulty"] + "☆" * (3 - info["difficulty"])
                st.markdown(f"**Difficulty:** {difficulty_str}")
                st.markdown('<div class="tip-box">Set up your camera so your full body is visible for best detection accuracy.</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════
# PAGE: SETTINGS
# ════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown("# ⚙️ SETTINGS")

    st.subheader("Webcam")
    cam_idx = st.selectbox("Camera index", [0, 1, 2], index=0)
    res     = st.selectbox("Resolution", ["1280×720", "960×540", "640×480"])

    st.subheader("Pose Detection")
    complexity = st.radio("Model complexity", ["Lite (fast)", "Full (accurate)"], index=1)
    min_conf   = st.slider("Min detection confidence", 0.3, 0.9, 0.6, 0.05)
    min_track  = st.slider("Min tracking confidence",  0.3, 0.9, 0.6, 0.05)

    st.subheader("Feedback")
    voice_fb  = st.toggle("Voice feedback (future feature)", value=False, disabled=True)
    angle_vis = st.toggle("Show angle overlays on video", value=True)

    st.subheader("User Profile (for calorie estimation)")
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("Weight (kg)", 40, 150, 70)
    with col2:
        age = st.number_input("Age", 15, 80, 28)

    if st.button("💾 Save Settings"):
        import json
        cfg = {
            "cam_idx": cam_idx, "resolution": res,
            "model_complexity": 0 if "Lite" in complexity else 1,
            "min_detection_confidence": min_conf,
            "min_tracking_confidence":  min_track,
            "angle_visualization": angle_vis,
            "weight_kg": weight, "age": age
        }
        os.makedirs("config", exist_ok=True)
        with open("config/settings.json", "w") as f:
            json.dump(cfg, f, indent=2)
        st.success("✅ Settings saved to config/settings.json")
