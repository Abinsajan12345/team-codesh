import cv2
import mediapipe as mp
import math
from collections import deque
import logging
import json
import threading
from flask import Flask
from flask_socketio import SocketIO

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Flask & SocketIO Setup ---
app = Flask(__name__)
# Allow all origins for easier development. For production, you might want to restrict this.
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Global Settings & State ---
CURRENT_MODE = 'letters'
TOUCH_THRESHOLD = 0.07

FONT_NAMES = [
    "Lobster, cursive",
    "'Playfair Display', serif",
    "'Roboto Mono', monospace",
    "Georgia, serif",
    "'Comic Sans MS', cursive",
]

# --- Helper Functions (No changes from previous version) ---

def get_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def get_hand_angle(hand_landmarks):
    wrist = hand_landmarks.landmark[0]
    middle_finger_base = hand_landmarks.landmark[9]
    dx = middle_finger_base.x - wrist.x
    dy = middle_finger_base.y - wrist.y
    raw_angle = math.degrees(math.atan2(-dy, dx))
    control_angle = -1.5 * raw_angle + 202.5
    return max(0, min(control_angle, 180))

def is_back_of_hand_facing(hand_landmarks):
    p0, p5, p17 = hand_landmarks.landmark[0], hand_landmarks.landmark[5], hand_landmarks.landmark[17]
    v1 = (p5.x - p0.x, p5.y - p0.y)
    v2 = (p17.x - p0.x, p17.y - p0.y)
    cross_product_z = v1[0] * v2[1] - v1[1] * v2[0]
    return cross_product_z > 0.01

def is_thumbs_up(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    thumb_is_up = thumb_tip.y < thumb_ip.y
    fingers_are_curled = (
        hand_landmarks.landmark[8].y > hand_landmarks.landmark[6].y and
        hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y and
        hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y and
        hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y
    )
    return thumb_is_up and fingers_are_curled

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    logger.info("Client connected to Socket.IO")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected from Socket.IO")

# --- Blocking Hand Tracking Function (to be run in a background thread) ---

def run_hand_tracking_blocking():
    """Main hand tracking loop that emits SocketIO events."""
    global CURRENT_MODE
    
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Could not open video device. Hand tracking thread will not start.")
        return

    letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    angle_history = deque(maxlen=15)
    
    print_was_active, delete_was_active, space_was_active = False, False, False
    last_font_index, last_size_value = -1, -1
    last_selected_letter = None

    logger.info("Hand tracking thread started.")

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Failed to grab frame. Exiting hand tracking loop.")
            break

        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip = (hand_landmarks.landmark[i] for i in [4, 8, 12, 16, 20])

                new_mode = CURRENT_MODE
                if get_distance(thumb_tip, middle_tip) < TOUCH_THRESHOLD: new_mode = 'letters'
                elif get_distance(thumb_tip, ring_tip) < TOUCH_THRESHOLD: new_mode = 'fonts'
                elif get_distance(thumb_tip, pinky_tip) < TOUCH_THRESHOLD: new_mode = 'size'
                
                if new_mode != CURRENT_MODE:
                    CURRENT_MODE = new_mode
                    socketio.emit('gesture_event', json.dumps({"type": "MODE_CHANGE", "mode": CURRENT_MODE}))
                    socketio.emit('gesture_event', json.dumps({"type": "SELECTION_UPDATE", "char": ""}))
                    last_selected_letter = None

                delete_is_active = is_back_of_hand_facing(hand_landmarks)
                if delete_is_active and not delete_was_active:
                    socketio.emit('gesture_event', json.dumps({"type": "DELETE"}))
                
                print_is_active = get_distance(thumb_tip, index_tip) < TOUCH_THRESHOLD
                space_is_active = is_thumbs_up(hand_landmarks)

                angle = get_hand_angle(hand_landmarks)
                angle_history.append(angle)
                smoothed_angle = sum(angle_history) / len(angle_history)

                if CURRENT_MODE == 'letters':
                    idx = int((smoothed_angle / 180) * (len(letters) - 1))
                    current_letter = letters[idx]
                    if current_letter != last_selected_letter:
                        socketio.emit('gesture_event', json.dumps({"type": "SELECTION_UPDATE", "char": current_letter}))
                        last_selected_letter = current_letter
                    if print_is_active and not print_was_active:
                        socketio.emit('gesture_event', json.dumps({"type": "PRINT", "char": current_letter}))
                    if space_is_active and not space_was_active:
                        socketio.emit('gesture_event', json.dumps({"type": "PRINT", "char": " "}))
                
                elif CURRENT_MODE == 'fonts':
                    font_index = int((smoothed_angle / 180) * (len(FONT_NAMES) - 1))
                    if font_index != last_font_index:
                        font_name = FONT_NAMES[font_index]
                        socketio.emit('gesture_event', json.dumps({"type": "FONT_CHANGE", "font": font_name}))
                        last_font_index = font_index
                
                elif CURRENT_MODE == 'size':
                    size_value = 2 + (smoothed_angle / 180) * 10
                    if abs(size_value - last_size_value) > 0.2:
                        socketio.emit('gesture_event', json.dumps({"type": "SIZE_CHANGE", "size": size_value}))
                        last_size_value = size_value

                print_was_active, delete_was_active, space_was_active = print_is_active, delete_is_active, space_is_active
        
        socketio.sleep(0.01)

    cap.release()
    logger.info("Hand tracking thread has stopped.")

# --- Main Execution ---
if __name__ == '__main__':
    logger.info("Starting Flask-SocketIO server.")
    # Start the hand tracking in a background thread
    socketio.start_background_task(target=run_hand_tracking_blocking)
    # Run the server. Use eventlet for best performance with SocketIO.
    socketio.run(app, host='0.0.0.0', port=5000)
