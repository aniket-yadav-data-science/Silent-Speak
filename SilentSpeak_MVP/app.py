import streamlit as st
import cv2
import mediapipe as mp
import pyttsx3
import threading

# ================== THREADED TEXT TO SPEECH ==================
def speak(text):
    def run():
        engine = pyttsx3.init()
        engine.setProperty("rate", 155)
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run, daemon=True).start()

# ================== STREAMLIT CONFIG ==================
st.set_page_config(page_title="SilentSpeak", layout="wide")
st.title(":shushing_face: SilentSpeak – Silent Authentication & Communication System")

# ================== SESSION STATE ==================
if "lip_intro_spoken" not in st.session_state:
    st.session_state.lip_intro_spoken = False
if "lip_unlocked_spoken" not in st.session_state:
    st.session_state.lip_unlocked_spoken = False
if "last_gesture" not in st.session_state:
    st.session_state.last_gesture = ""
if "face_intro_spoken" not in st.session_state:
    st.session_state.face_intro_spoken = False
if "prev_mode" not in st.session_state:
    st.session_state.prev_mode = ""

# ================== SIDEBAR ==================
mode = st.sidebar.selectbox(
    "Select Mode",
    ["Lip Lock", "Hand Gesture Translation", "Facial Expression"]
)

# -------- RESET STATES ON MODE CHANGE --------
if st.session_state.prev_mode != mode:
    st.session_state.lip_intro_spoken = False
    st.session_state.lip_unlocked_spoken = False
    st.session_state.last_gesture = ""
    st.session_state.face_intro_spoken = False
    st.session_state.prev_mode = mode

# ================== MEDIAPIPE ==================
mp_face = mp.solutions.face_mesh
mp_hands = mp.solutions.hands

# ============================================================
# :closed_lock_with_key: LIP LOCK (OPEN + BLINK + VOICE)
# ============================================================
if mode == "Lip Lock":

    if not st.session_state.lip_intro_spoken:
        speak("Welcome back master, please show the password")
        st.session_state.lip_intro_spoken = True

    st.subheader(":closed_lock_with_key: Lip Lock Authentication")

    cam = cv2.VideoCapture(0)
    face_mesh = mp_face.FaceMesh(refine_landmarks=True)

    open_counter = 0
    blink_counter = 0
    unlocked = False

    frame_box = st.image([])

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        if result.multi_face_landmarks:
            face = result.multi_face_landmarks[0].landmark

            # Lip OPEN detection
            lip_gap = abs(face[13].y - face[14].y)
            if lip_gap > 0.035:
                open_counter += 1
            else:
                open_counter = max(0, open_counter - 1)

            # Blink detection
            eye_gap = abs(face[159].y - face[145].y)
            if eye_gap < 0.008:
                blink_counter += 1

            if open_counter > 25 and blink_counter >= 1:
                unlocked = True

        frame_box.image(frame, channels="BGR")

        if unlocked:
            st.success(":white_check_mark: UNLOCKED")
            break

    cam.release()

    if unlocked and not st.session_state.lip_unlocked_spoken:
        speak("Unlocked")
        st.session_state.lip_unlocked_spoken = True

# ============================================================
# :hand: HAND GESTURE TRANSLATION (WITH VOICE)
# ============================================================

elif mode == "Hand Gesture Translation":

    st.subheader(":hand: Hand Gesture Translation")

    cam = cv2.VideoCapture(0)
    hands = mp_hands.Hands(max_num_hands=1)

    frame_box = st.image([])   # :white_check_mark: REQUIRED
    text_box = st.empty()

    text = "No Hand"

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        text = "No Hand"   # :white_check_mark: RESET EVERY FRAME

        if result.multi_hand_landmarks:
            lm = result.multi_hand_landmarks[0].landmark

            # Finger states
            thumb_open = lm[4].x > lm[3].x
            index_open = lm[8].y < lm[6].y
            middle_open = lm[12].y < lm[10].y
            ring_open = lm[16].y < lm[14].y
            pinky_open = lm[20].y < lm[18].y

            # -------- GESTURE RULES --------
            if thumb_open and index_open and middle_open and ring_open and pinky_open:
                text = "HELLO"

            elif index_open and middle_open and not ring_open and not pinky_open:
                text = "PEACE"

            elif thumb_open and not index_open and not middle_open and not ring_open and not pinky_open:
                text = "GOOD"

            elif index_open and not middle_open and not ring_open and not pinky_open:
                text = "YOU"

            elif index_open and middle_open and ring_open and pinky_open:
                text = "HELP"

            elif not thumb_open and not index_open and not middle_open and not ring_open and not pinky_open:
                text = "YES"

        # :white_check_mark: TEXT OUTPUT
        text_box.markdown(f"### Meaning: **{text}**")

        # :white_check_mark: VOICE OUTPUT
        if text != "No Hand":
            if st.session_state.last_gesture != text:
                speak(text)
                st.session_state.last_gesture = text

        # :white_check_mark: VIDEO RENDER (THIS WAS MISSING)
        frame_box.image(frame, channels="BGR")

    cam.release()


# ============================================================
# :slightly_smiling_face: FACIAL EXPRESSION (INTRO VOICE ONLY ONCE)
# ============================================================
elif mode == "Facial Expression":

    if not st.session_state.face_intro_spoken:
        speak("Welcome to facial expression teller")
        st.session_state.face_intro_spoken = True

    st.subheader(":slightly_smiling_face: Facial Expression Detection")

    cam = cv2.VideoCapture(0)
    face_mesh = mp_face.FaceMesh()

    frame_box = st.image([])
    text_box = st.empty()

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        emotion = "Neutral"

        if result.multi_face_landmarks:
            face = result.multi_face_landmarks[0].landmark

            mouth_gap = abs(face[13].y - face[14].y)
            smile = face[61].y < face[291].y
            brow = face[65].y > face[55].y

            if mouth_gap > 0.04:
                emotion = "Crying"
            elif smile:
                emotion = "Happy"
            elif brow:
                emotion = "Angry"
            else:
                emotion = "Sad"

        text_box.markdown(f"### Expression: **{emotion}**")
        frame_box.image(frame, channels="BGR")

    cam.release()