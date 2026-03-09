import cv2
import mediapipe as mp
import numpy as np
import time
import json
import os
from datetime import datetime
from collections import deque

def calculate_angle(a, b, c):
    """Calculate the angle at joint b, given three points a, b, c."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
    return angle


def get_landmark(landmarks, idx, w, h):
    """Return (x, y) pixel coords for a given landmark index."""
    lm = landmarks[idx]
    return [lm.x * w, lm.y * h]

class ExerciseDetector:
    def __init__(self):
        self.counter = 0
        self.stage = None          # 'up' / 'down' / 'standing' / etc.
        self.feedback = "Get Ready"
        self.angle_history = deque(maxlen=5)
        self.last_rep_time = time.time()
        self.correct_form = True
        self.form_errors = []

    def reset(self):
        self.counter = 0
        self.stage = None
        self.feedback = "Get Ready"
        self.correct_form = True
        self.form_errors = []


class SquatDetector(ExerciseDetector):
    """
    Landmarks used: Hip, Knee, Ankle (both sides averaged).
    Rules:
        Standing  → knee angle ≥ 160°
        Squatting → knee angle ≤ 100°
    """

    def process(self, landmarks, w, h):
        self.form_errors = []

        # Left side
        l_hip   = get_landmark(landmarks, 23, w, h)
        l_knee  = get_landmark(landmarks, 25, w, h)
        l_ankle = get_landmark(landmarks, 27, w, h)
        l_shoulder = get_landmark(landmarks, 11, w, h)

        # Right side
        r_hip   = get_landmark(landmarks, 24, w, h)
        r_knee  = get_landmark(landmarks, 26, w, h)
        r_ankle = get_landmark(landmarks, 28, w, h)

        left_knee_angle  = calculate_angle(l_hip, l_knee, l_ankle)
        right_knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
        knee_angle = (left_knee_angle + right_knee_angle) / 2

        # Hip angle for back form check
        left_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)

        self.angle_history.append(knee_angle)

        # Posture feedback
        if left_hip_angle < 50:
            self.form_errors.append("Lean forward less!")
        if abs(left_knee_angle - right_knee_angle) > 20:
            self.form_errors.append("Balance both knees evenly")

        self.correct_form = len(self.form_errors) == 0

        # Rep counting
        if knee_angle > 160:
            if self.stage == "down":
                self.counter += 1
                self.last_rep_time = time.time()
            self.stage = "up"
            self.feedback = "Stand straight" if self.correct_form else self.form_errors[0]
        elif knee_angle < 100:
            self.stage = "down"
            self.feedback = "Good squat depth!" if self.correct_form else self.form_errors[0]
        else:
            self.feedback = "Keep going..." if self.stage == "down" else "Start squatting"

        return {
            "name": "SQUAT",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(knee_angle, 1),
            "angle_label": "Knee Angle",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }


class PushupDetector(ExerciseDetector):
    """
    Landmarks: Shoulder, Elbow, Wrist.
    Rules:
        Up   → elbow angle ≥ 160°
        Down → elbow angle ≤ 80°
    """

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_shoulder = get_landmark(landmarks, 11, w, h)
        l_elbow    = get_landmark(landmarks, 13, w, h)
        l_wrist    = get_landmark(landmarks, 15, w, h)
        l_hip      = get_landmark(landmarks, 23, w, h)
        l_knee     = get_landmark(landmarks, 25, w, h)

        r_shoulder = get_landmark(landmarks, 12, w, h)
        r_elbow    = get_landmark(landmarks, 14, w, h)
        r_wrist    = get_landmark(landmarks, 16, w, h)

        left_elbow_angle  = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
        elbow_angle = (left_elbow_angle + right_elbow_angle) / 2

        # Body alignment check
        body_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        if body_angle < 160:
            self.form_errors.append("Keep body straight!")

        # Shoulder alignment
        if abs(left_elbow_angle - right_elbow_angle) > 25:
            self.form_errors.append("Balance both arms")

        self.correct_form = len(self.form_errors) == 0

        if elbow_angle > 160:
            if self.stage == "down":
                self.counter += 1
                self.last_rep_time = time.time()
            self.stage = "up"
            self.feedback = "Arms extended" if self.correct_form else self.form_errors[0]
        elif elbow_angle < 80:
            self.stage = "down"
            self.feedback = "Good depth!" if self.correct_form else self.form_errors[0]
        else:
            self.feedback = "Push up!" if self.stage == "down" else "Lower down"

        return {
            "name": "PUSH-UP",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(elbow_angle, 1),
            "angle_label": "Elbow Angle",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }


class BicepCurlDetector(ExerciseDetector):
    """
    Landmarks: Shoulder, Elbow, Wrist.
    Up   → elbow angle ≤ 40°
    Down → elbow angle ≥ 150°
    """

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_shoulder = get_landmark(landmarks, 11, w, h)
        l_elbow    = get_landmark(landmarks, 13, w, h)
        l_wrist    = get_landmark(landmarks, 15, w, h)

        r_shoulder = get_landmark(landmarks, 12, w, h)
        r_elbow    = get_landmark(landmarks, 14, w, h)
        r_wrist    = get_landmark(landmarks, 16, w, h)

        left_angle  = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
        avg_angle = (left_angle + right_angle) / 2

        if abs(left_angle - right_angle) > 30:
            self.form_errors.append("Curl both arms evenly")

        self.correct_form = len(self.form_errors) == 0

        if avg_angle > 150:
            if self.stage == "up":
                self.counter += 1
                self.last_rep_time = time.time()
            self.stage = "down"
            self.feedback = "Curl up!" if self.correct_form else self.form_errors[0]
        elif avg_angle < 40:
            self.stage = "up"
            self.feedback = "Full curl!" if self.correct_form else self.form_errors[0]
        else:
            self.feedback = "Keep curling" if self.stage == "down" else "Lower down"

        return {
            "name": "BICEP CURL",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(avg_angle, 1),
            "angle_label": "Elbow Angle",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }


class LungeDetector(ExerciseDetector):
    """
    Front knee angle drops below 100° → lunge position.
    """

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_hip   = get_landmark(landmarks, 23, w, h)
        l_knee  = get_landmark(landmarks, 25, w, h)
        l_ankle = get_landmark(landmarks, 27, w, h)

        r_hip   = get_landmark(landmarks, 24, w, h)
        r_knee  = get_landmark(landmarks, 26, w, h)
        r_ankle = get_landmark(landmarks, 28, w, h)

        left_angle  = calculate_angle(l_hip, l_knee, l_ankle)
        right_angle = calculate_angle(r_hip, r_knee, r_ankle)
        front_knee  = min(left_angle, right_angle)

        self.correct_form = len(self.form_errors) == 0

        if front_knee > 160:
            if self.stage == "down":
                self.counter += 1
                self.last_rep_time = time.time()
            self.stage = "up"
            self.feedback = "Step into lunge"
        elif front_knee < 100:
            self.stage = "down"
            self.feedback = "Deep lunge!" if self.correct_form else "Keep knee behind toe"
        else:
            self.feedback = "Lower more" if self.stage == "down" else "Stand up straight"

        return {
            "name": "LUNGE",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(front_knee, 1),
            "angle_label": "Front Knee",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }


class JumpingJackDetector(ExerciseDetector):
    """
    Jumping Jacks — tracks BOTH arm abduction AND foot spread simultaneously.
    Arms:  Hip->Shoulder->Wrist angle  (down <40, up >130)
    Feet:  horizontal ankle spread vs shoulder width ratio
    Rep counted when arms+feet go OUT together, then return IN/DOWN.
    """

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_shoulder = get_landmark(landmarks, 11, w, h)
        l_hip      = get_landmark(landmarks, 23, w, h)
        l_wrist    = get_landmark(landmarks, 15, w, h)
        l_ankle    = get_landmark(landmarks, 27, w, h)

        r_shoulder = get_landmark(landmarks, 12, w, h)
        r_hip      = get_landmark(landmarks, 24, w, h)
        r_wrist    = get_landmark(landmarks, 16, w, h)
        r_ankle    = get_landmark(landmarks, 28, w, h)

        left_arm_angle  = calculate_angle(l_hip, l_shoulder, l_wrist)
        right_arm_angle = calculate_angle(r_hip, r_shoulder, r_wrist)
        avg_arm_angle   = (left_arm_angle + right_arm_angle) / 2

        shoulder_width = abs(r_shoulder[0] - l_shoulder[0]) + 1e-6
        ankle_spread   = abs(r_ankle[0] - l_ankle[0])
        spread_ratio   = ankle_spread / shoulder_width

        arms_up    = avg_arm_angle > 130
        arms_down  = avg_arm_angle < 45
        feet_wide  = spread_ratio > 1.4
        feet_close = spread_ratio < 0.7

        if arms_up and not feet_wide:
            self.form_errors.append("Spread feet wider!")

        self.correct_form = len(self.form_errors) == 0

        if arms_up and feet_wide:
            self.stage = "open"
            self.feedback = "Great Jack!" if self.correct_form else self.form_errors[0]
        elif arms_down and feet_close:
            if self.stage == "open":
                self.counter += 1
                self.last_rep_time = time.time()
            self.stage = "closed"
            self.feedback = "Jump out!" if self.correct_form else self.form_errors[0]
        else:
            self.feedback = "Full range — arms AND feet!"

        return {
            "name": "JUMPING JACK",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(avg_arm_angle, 1),
            "angle_label": "Arm Angle",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }


class HighKneeDetector(ExerciseDetector):
    """
    High Knees — lift legs high alternately.
    Knee must rise above the hip Y coordinate by a threshold.
    Each knee lift (L or R) counts as 1 rep.
    """

    def __init__(self):
        super().__init__()
        self.last_knee = None

    def reset(self):
        super().reset()
        self.last_knee = None

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_hip  = get_landmark(landmarks, 23, w, h)
        l_knee = get_landmark(landmarks, 25, w, h)
        r_hip  = get_landmark(landmarks, 24, w, h)
        r_knee = get_landmark(landmarks, 26, w, h)

        threshold = h * 0.06

        left_high  = l_knee[1] < (l_hip[1] - threshold)
        right_high = r_knee[1] < (r_hip[1] - threshold)

        best_lift = max(l_hip[1] - l_knee[1], r_hip[1] - r_knee[1])
        lift_pct  = min(100, round(best_lift / (h * 0.15) * 100))

        if not left_high and not right_high:
            self.form_errors.append("Lift knees higher!")

        self.correct_form = len(self.form_errors) == 0

        if left_high and self.last_knee != "left":
            self.last_knee = "left"
            self.counter += 1
            self.last_rep_time = time.time()
            self.stage = "left"
            self.feedback = "Left knee HIGH!" if self.correct_form else self.form_errors[0]
        elif right_high and self.last_knee != "right":
            self.last_knee = "right"
            self.counter += 1
            self.last_rep_time = time.time()
            self.stage = "right"
            self.feedback = "Right knee HIGH!" if self.correct_form else self.form_errors[0]
        else:
            self.stage = self.stage or "ready"
            self.feedback = self.form_errors[0] if self.form_errors else "Drive knees up! ({}%)".format(lift_pct)

        return {
            "name": "HIGH KNEES",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(best_lift, 1),
            "angle_label": "Knee Lift (px)",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }


class TwistJumpDetector(ExerciseDetector):
    """
    Twist Jump — torso rotates while hips face forward.
    Detection: horizontal offset of shoulder midpoint vs hip midpoint
    normalised by shoulder width. Threshold 0.25 = meaningful twist.
    Left twist then right twist = 1 rep.
    """

    def __init__(self):
        super().__init__()
        self.last_twist = None

    def reset(self):
        super().reset()
        self.last_twist = None

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_shoulder = get_landmark(landmarks, 11, w, h)
        r_shoulder = get_landmark(landmarks, 12, w, h)
        l_hip      = get_landmark(landmarks, 23, w, h)
        r_hip      = get_landmark(landmarks, 24, w, h)

        shoulder_mid_x = (l_shoulder[0] + r_shoulder[0]) / 2
        hip_mid_x      = (l_hip[0] + r_hip[0]) / 2
        shoulder_width = abs(r_shoulder[0] - l_shoulder[0]) + 1e-6

        twist_offset = (shoulder_mid_x - hip_mid_x) / shoulder_width
        twist_deg    = round(abs(twist_offset) * 45, 1)

        threshold     = 0.25
        twisted_right = twist_offset >  threshold
        twisted_left  = twist_offset < -threshold

        if abs(twist_offset) < 0.10:
            self.stage = "center"

        self.correct_form = True

        if twisted_right and self.last_twist != "right":
            self.last_twist = "right"
            self.stage = "right"
            self.feedback = "Twist RIGHT!"
        elif twisted_left and self.last_twist != "left":
            if self.last_twist == "right":
                self.counter += 1
                self.last_rep_time = time.time()
            self.last_twist = "left"
            self.stage = "left"
            self.feedback = "Twist LEFT!"
        elif self.stage == "center":
            self.feedback = "Jump & twist hips!"
        else:
            self.feedback = "Bigger twist! ({:.0f}deg)".format(twist_deg)

        return {
            "name": "TWIST JUMP",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": twist_deg,
            "angle_label": "Twist Angle",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }


class ElbowKneeDetector(ExerciseDetector):
    """
    Elbow-to-Knee Collision (cross-body crunch).
    Left elbow -> Right knee and Right elbow -> Left knee.
    Counts when Euclidean pixel distance < 20% of frame height.
    Each side hit = 1 rep. Alternates sides.
    """

    def __init__(self):
        super().__init__()
        self.last_side = None

    def reset(self):
        super().reset()
        self.last_side = None

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_elbow = get_landmark(landmarks, 13, w, h)
        r_elbow = get_landmark(landmarks, 14, w, h)
        l_knee  = get_landmark(landmarks, 25, w, h)
        r_knee  = get_landmark(landmarks, 26, w, h)

        def dist(a, b):
            return np.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

        left_cross  = dist(l_elbow, r_knee)
        right_cross = dist(r_elbow, l_knee)

        collision_threshold = h * 0.20

        left_hit  = left_cross  < collision_threshold
        right_hit = right_cross < collision_threshold

        left_pct  = max(0, int((1 - left_cross  / (h * 0.4)) * 100))
        right_pct = max(0, int((1 - right_cross / (h * 0.4)) * 100))
        best_pct  = max(left_pct, right_pct)

        self.correct_form = True

        if left_hit and self.last_side != "left":
            self.last_side = "left"
            self.counter += 1
            self.last_rep_time = time.time()
            self.stage = "left_hit"
            self.feedback = "Left Elbow + Right Knee!"
        elif right_hit and self.last_side != "right":
            self.last_side = "right"
            self.counter += 1
            self.last_rep_time = time.time()
            self.stage = "right_hit"
            self.feedback = "Right Elbow + Left Knee!"
        else:
            self.stage = self.stage or "ready"
            self.feedback = "Crunch & drive! {}% close".format(best_pct)

        return {
            "name": "ELBOW-KNEE",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(min(left_cross, right_cross), 1),
            "angle_label": "Proximity (px)",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }

class ShoulderPressDetector(ExerciseDetector):
    """
    Elbow angle at shoulder height:
    Down → elbow angle ≤ 90°  (arms bent, hands near ears)
    Up   → elbow angle ≥ 160° (arms fully extended overhead)
    Rep = down → up transition.
    """

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_shoulder = get_landmark(landmarks, 11, w, h)
        l_elbow    = get_landmark(landmarks, 13, w, h)
        l_wrist    = get_landmark(landmarks, 15, w, h)

        r_shoulder = get_landmark(landmarks, 12, w, h)
        r_elbow    = get_landmark(landmarks, 14, w, h)
        r_wrist    = get_landmark(landmarks, 16, w, h)

        left_angle  = calculate_angle(l_shoulder, l_elbow, l_wrist)
        right_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
        avg_angle   = (left_angle + right_angle) / 2

        if abs(left_angle - right_angle) > 25:
            self.form_errors.append("Press both arms evenly")

        self.correct_form = len(self.form_errors) == 0

        if avg_angle > 160:
            if self.stage == "down":
                self.counter += 1
                self.last_rep_time = time.time()
            self.stage = "up"
            self.feedback = "Arms locked out!" if self.correct_form else self.form_errors[0]
        elif avg_angle < 90:
            self.stage = "down"
            self.feedback = "Press up!" if self.correct_form else self.form_errors[0]
        else:
            self.feedback = "Keep pressing" if self.stage == "down" else "Lower to ears"

        return {
            "name": "SHOULDER PRESS",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(avg_angle, 1),
            "angle_label": "Elbow Angle",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }


class PlankDetector(ExerciseDetector):
    """
    Measures body alignment (shoulder–hip–ankle angle).
    Plank hold → angle > 160° for sustained duration.
    Counts every 5 seconds held in position.
    """

    def __init__(self):
        super().__init__()
        self.hold_start = None
        self.seconds_held = 0

    def reset(self):
        super().reset()
        self.hold_start = None
        self.seconds_held = 0

    def process(self, landmarks, w, h):
        self.form_errors = []

        l_shoulder = get_landmark(landmarks, 11, w, h)
        l_hip      = get_landmark(landmarks, 23, w, h)
        l_ankle    = get_landmark(landmarks, 27, w, h)

        body_angle = calculate_angle(l_shoulder, l_hip, l_ankle)

        if body_angle < 150:
            self.form_errors.append("Raise your hips!")
        elif body_angle > 190:
            self.form_errors.append("Lower your hips!")

        self.correct_form = len(self.form_errors) == 0

        if self.correct_form and body_angle > 155:
            if self.hold_start is None:
                self.hold_start = time.time()
            self.seconds_held = int(time.time() - self.hold_start)
            # Count 1 rep per 5 seconds held
            new_count = self.seconds_held // 5
            if new_count > self.counter:
                self.counter = new_count
                self.last_rep_time = time.time()
            self.stage = "hold"
            self.feedback = f"Holding {self.seconds_held}s — great!" if self.correct_form else self.form_errors[0]
        else:
            self.hold_start = None
            self.seconds_held = 0
            self.stage = "rest"
            self.feedback = self.form_errors[0] if self.form_errors else "Get into plank position"

        return {
            "name": "PLANK",
            "count": self.counter,
            "stage": self.stage,
            "feedback": self.feedback,
            "angle": round(body_angle, 1),
            "angle_label": "Body Angle",
            "correct_form": self.correct_form,
            "errors": self.form_errors
        }

CALORIES_PER_REP = {
    "SQUAT":          0.32,
    "PUSH-UP":        0.29,
    "BICEP CURL":     0.14,
    "LUNGE":          0.30,
    "JUMPING JACK":   0.10,
    "HIGH KNEES":     0.08,   # per knee lift
    "TWIST JUMP":     0.15,
    "ELBOW-KNEE":     0.12,
    "SHOULDER PRESS": 0.19,
    "PLANK":          0.25,   # per 5-second hold unit
}

def estimate_calories(exercise_name, reps):
    return round(CALORIES_PER_REP.get(exercise_name, 0.2) * reps, 2)


class SessionLogger:
    def __init__(self, log_dir="workout_logs"):
        os.makedirs(log_dir, exist_ok=True)
        self.log_dir = log_dir
        self.session_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exercises": {}
        }

    def update(self, exercise_name, reps, calories):
        self.session_data["exercises"][exercise_name] = {
            "reps": reps,
            "calories": calories
        }

    def save(self):
        filename = os.path.join(
            self.log_dir,
            f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(filename, "w") as f:
            json.dump(self.session_data, f, indent=2)
        print(f"\n✅ Session saved to: {filename}")
        return filename

def draw_rounded_rect(img, x, y, w, h, r, color, alpha=0.6):
    overlay = img.copy()
    cv2.rectangle(overlay, (x + r, y), (x + w - r, y + h), color, -1)
    cv2.rectangle(overlay, (x, y + r), (x + w, y + h - r), color, -1)
    cv2.circle(overlay, (x + r,     y + r),     r, color, -1)
    cv2.circle(overlay, (x + w - r, y + r),     r, color, -1)
    cv2.circle(overlay, (x + r,     y + h - r), r, color, -1)
    cv2.circle(overlay, (x + w - r, y + h - r), r, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def draw_ui(frame, result, fps, elapsed, total_calories):
    h, w = frame.shape[:2]

   
    draw_rounded_rect(frame, 0, 0, w, 64, 0, (15, 15, 30), alpha=0.85)
    cv2.putText(frame, "AI FITNESS TRAINER", (20, 42),
                cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 220, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 130, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 1, cv2.LINE_AA)

    mins, secs = divmod(int(elapsed), 60)
    cv2.putText(frame, f"{mins:02d}:{secs:02d}", (w - 260, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 180), 2, cv2.LINE_AA)

   
    draw_rounded_rect(frame, 10, 80, 200, 180, 12, (20, 20, 50), alpha=0.8)

    cv2.putText(frame, result["name"], (20, 108),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 200, 255), 2, cv2.LINE_AA)

   
    rep_str = str(result["count"])
    cv2.putText(frame, rep_str, (55, 200),
                cv2.FONT_HERSHEY_DUPLEX, 3.5, (255, 255, 255), 4, cv2.LINE_AA)
    cv2.putText(frame, "REPS", (68, 235),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (140, 140, 180), 1, cv2.LINE_AA)

    draw_rounded_rect(frame, 10, 275, 200, 90, 12, (20, 20, 50), alpha=0.8)
    cv2.putText(frame, result["angle_label"], (20, 300),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{result['angle']}°", (20, 345),
                cv2.FONT_HERSHEY_DUPLEX, 1.6, (0, 255, 200), 2, cv2.LINE_AA)

    draw_rounded_rect(frame, 10, 380, 200, 80, 12, (20, 20, 50), alpha=0.8)
    cv2.putText(frame, "CALORIES", (20, 405),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 200), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{total_calories:.1f} kcal", (18, 445),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 190, 50), 2, cv2.LINE_AA)

    form_color = (0, 220, 100) if result["correct_form"] else (0, 80, 255)
    form_label = "✓ GOOD FORM" if result["correct_form"] else "✗ CORRECT FORM"
    draw_rounded_rect(frame, 0, h - 70, w, 70, 0, (15, 15, 40), alpha=0.85)

    cv2.putText(frame, result["feedback"], (20, h - 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (230, 230, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, form_label, (w - 230, h - 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, form_color, 2, cv2.LINE_AA)


    stage_text = (result["stage"] or "---").upper()
    stage_col  = (0, 200, 100) if result["stage"] == "up" else (0, 120, 255)
    draw_rounded_rect(frame, w // 2 - 60, h - 140, 120, 40, 10, stage_col, alpha=0.75)
    cv2.putText(frame, stage_text, (w // 2 - 30, h - 112),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)


def draw_exercise_menu(frame, exercises, current_idx):
    h, w = frame.shape[:2]
    draw_rounded_rect(frame, w - 210, 80, 200, 40 * len(exercises) + 20, 10, (20, 20, 50), alpha=0.85)
    cv2.putText(frame, "EXERCISES", (w - 200, 105),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 180, 255), 1, cv2.LINE_AA)
    for i, ex in enumerate(exercises):
        color = (0, 220, 255) if i == current_idx else (160, 160, 200)
        prefix = "► " if i == current_idx else "  "
        cv2.putText(frame, f"{prefix}{i+1}. {ex}", (w - 198, 130 + i * 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1 if i != current_idx else 2, cv2.LINE_AA)


def draw_controls(frame):
    h, w = frame.shape[:2]
    controls = ["[1-9,0] Switch Exercise", "[R] Reset Reps", "[S] Save Session", "[ESC] Quit"]
    for i, c in enumerate(controls):
        cv2.putText(frame, c, (w - 310, h - 200 + i * 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (120, 120, 160), 1, cv2.LINE_AA)

def main():
    mp_pose    = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_styles  = mp.solutions.drawing_styles

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )

    detectors = [
        SquatDetector(),
        PushupDetector(),
        BicepCurlDetector(),
        LungeDetector(),
        JumpingJackDetector(),
        HighKneeDetector(),
        TwistJumpDetector(),
        ElbowKneeDetector(),
        ShoulderPressDetector(),
        PlankDetector(),
    ]
    exercise_names = ["SQUAT", "PUSH-UP", "BICEP CURL", "LUNGE",
                      "JUMPING JACK", "HIGH KNEES", "TWIST JUMP",
                      "ELBOW-KNEE", "SHOULDER PRESS", "PLANK"]
    current_ex = 0

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    logger        = SessionLogger()
    session_start = time.time()
    prev_time     = time.time()

    print("\n🏋️  AI FITNESS TRAINER STARTED")
    print("Controls: [1-9,0] switch exercise | [R] reset | [S] save | [ESC] quit\n")

    result = {
        "name": exercise_names[current_ex],
        "count": 0, "stage": None,
        "feedback": "Get Ready",
        "angle": 0.0, "angle_label": "Angle",
        "correct_form": True, "errors": []
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]

        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        output = pose.process(rgb)

        if output.pose_landmarks:
            # Custom drawing style
            mp_drawing.draw_landmarks(
                frame,
                output.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(
                    color=(0, 255, 200), thickness=3, circle_radius=4),
                connection_drawing_spec=mp_drawing.DrawingSpec(
                    color=(0, 160, 255), thickness=2)
            )

            result = detectors[current_ex].process(
                output.pose_landmarks.landmark, w, h
            )

        # FPS
        now      = time.time()
        fps      = 1.0 / (now - prev_time + 1e-6)
        prev_time = now
        elapsed  = now - session_start

        # Calories across all exercises
        total_cal = sum(
            estimate_calories(exercise_names[i], detectors[i].counter)
            for i in range(len(detectors))
        )

        # Draw UI
        draw_ui(frame, result, fps, elapsed, total_cal)
        draw_exercise_menu(frame, exercise_names, current_ex)
        draw_controls(frame)

        cv2.imshow("AI Fitness Trainer", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:   # ESC
            break
        elif key == ord('1'):
            current_ex = 0
        elif key == ord('2'):
            current_ex = 1
        elif key == ord('3'):
            current_ex = 2
        elif key == ord('4'):
            current_ex = 3
        elif key == ord('5'):
            current_ex = 4
        elif key == ord('6'):
            current_ex = 5
        elif key == ord('7'):
            current_ex = 6
        elif key == ord('8'):
            current_ex = 7
        elif key == ord('9'):
            current_ex = 8
        elif key == ord('0'):
            current_ex = 9
        elif key == ord('r') or key == ord('R'):
            detectors[current_ex].reset()
            print(f"🔄 Reset {exercise_names[current_ex]} counter")
        elif key == ord('s') or key == ord('S'):
            for i, det in enumerate(detectors):
                logger.update(
                    exercise_names[i],
                    det.counter,
                    estimate_calories(exercise_names[i], det.counter)
                )
            logger.save()

    cap.release()
    cv2.destroyAllWindows()
    print("\n👋 Session ended. Goodbye!")


if __name__ == "__main__":
    main()
