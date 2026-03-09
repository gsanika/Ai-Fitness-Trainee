# 🏋️ AI Fitness Trainer

> Real-time exercise detection, rep counting, and posture feedback using your webcam — powered by OpenCV and MediaPipe Pose.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green?style=flat-square&logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.9-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

---

## 📌 About

AI Fitness Trainer is a computer vision project that uses your webcam to detect body pose in real time, automatically count exercise repetitions, and give live posture feedback — no wearables or sensors required.

It detects **33 body landmarks** using Google's MediaPipe Pose model, calculates joint angles frame-by-frame, and applies rule-based logic to identify exercise stages and count reps.

---

## 🎯 Features

- 📹 **Live webcam pose detection** with skeleton overlay
- 🔢 **Automatic rep counting** for 10 exercises
- ⚠️ **Real-time posture correction** feedback
- 📐 **Joint angle display** on screen
- 🔥 **Calories burned estimation**
- ⏱️ **Session timer** and FPS counter
- 💾 **Session logging** to JSON files
- 📊 **Streamlit dashboard** for workout history and analytics

---

## 🏃 Exercises Supported

| Key | Exercise | Detection Method |
|-----|----------|-----------------|
| `1` | Squat | Knee angle: 170° → 90° |
| `2` | Push-up | Elbow angle: 160° → 80° |
| `3` | Bicep Curl | Elbow angle: 150° → 40° |
| `4` | Lunge | Front knee angle: 170° → 100° |
| `5` | Jumping Jack | Arm angle + ankle spread ratio |
| `6` | High Knees | Knee Y position above hip threshold |
| `7` | Twist Jump | Shoulder vs hip horizontal offset |
| `8` | Elbow-Knee | Cross-body proximity distance |
| `9` | Shoulder Press | Elbow angle: 90° → 160° overhead |
| `0` | Plank | Body alignment angle hold timer |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.8+ | Core language |
| OpenCV | Webcam capture and UI rendering |
| MediaPipe Pose | 33-point body landmark detection |
| NumPy | Angle and distance calculations |
| Streamlit | Workout dashboard (optional) |

---

## ⚙️ Installation

**1. Clone the repository**
```bash
git clone https://github.com/your-username/ai-fitness-trainer.git
cd ai-fitness-trainer
```

**2. Create a virtual environment (recommended)**
```bash
python -m venv fitness_env
fitness_env\Scripts\activate        # Windows
source fitness_env/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

> ⚠️ Use **mediapipe==0.10.9** specifically. Newer versions removed the `solutions` API.

---

## 🚀 Usage

**Run the trainer (webcam required)**
```bash
python fitness_trainer.py
```

**Run the analytics dashboard**
```bash
streamlit run dashboard.py
```

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| `1` – `0` | Switch exercise |
| `R` | Reset rep counter |
| `S` | Save session to file |
| `ESC` | Quit |

> Click on the **webcam window** first to make sure it has keyboard focus.

---

## 📂 Project Structure

```
ai-fitness-trainer/
├── fitness_trainer.py    # Main application (webcam + CV pipeline)
├── dashboard.py          # Streamlit analytics dashboard
├── requirements.txt      # Python dependencies
├── workout_logs/         # Auto-created JSON session files
└── config/               # Auto-created settings file
```

---

## 🔬 How It Works

```
Webcam Feed
    ↓
OpenCV Video Capture (flipped mirror view)
    ↓
MediaPipe Pose — detects 33 body landmarks
    ↓
Landmark Extraction — pixel coordinates per joint
    ↓
Angle / Distance Calculation (NumPy dot product)
    ↓
Exercise State Machine (up / down / hold stages)
    ↓
Rep Counter + Posture Feedback
    ↓
OpenCV HUD Overlay → Display
```

**Angle formula used:**
```
angle at B = arccos( dot(BA, BC) / (|BA| × |BC|) )
```

---

## 📊 Dashboard Preview

The Streamlit dashboard reads your saved session JSON files and shows:
- Total sessions, reps, calories, and streak
- 7-day rep volume bar chart
- Per-exercise breakdown with progress bars
- Full session history
- Exercise guide with form tips
- Settings panel

```bash
streamlit run dashboard.py
```

---

## 🔮 Roadmap

- [ ] Voice feedback using pyttsx3
- [ ] ML-based pose classification with TFLite
- [ ] Workout recommendation engine
- [ ] Mobile support via MediaPipe Tasks API
- [ ] Real-time posture scoring (0–100)
- [ ] Multi-person detection

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙌 Acknowledgements

- [MediaPipe](https://mediapipe.dev/) by Google for the pose estimation model
- [OpenCV](https://opencv.org/) for video capture and drawing utilities
- [Streamlit](https://streamlit.io/) for the dashboard framework
