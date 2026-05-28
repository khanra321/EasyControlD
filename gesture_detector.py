import cv2
import mediapipe as mp
import numpy as np
import time

class GestureDetector:
    """Detect gestures with the exact original logic and thresholds."""

    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.55,
        )

        self.is_armed = False
        self.arm_expiry_time = 0.0
        self.arm_timeout = 1.0
        self.armed_stable_frames = 0
        self.trigger_stable_frames = 0
        self.next_prev_stable_frames = 0
        self.volume_brightness_stable_frames = 0

        self.required_stable_frames = 3
        self.required_next_prev_frames = 5
        self.required_volume_brightness_frames = 1

        self.last_media_action_time = 0.0
        self.media_cooldown = 1.2
        self.next_prev_cooldown = 0.8

    @staticmethod
    def get_dist(l1, l2):
        return np.linalg.norm(np.array([l1.x - l2.x, l1.y - l2.y, l1.z - l2.z]))

    @staticmethod
    def get_pixel_distance(l1, l2, width, height):
        x1, y1 = int(l1.x * width), int(l1.y * height)
        x2, y2 = int(l2.x * width), int(l2.y * height)
        return np.hypot(x2 - x1, y2 - y1)

    def detect(self, frame):
        """Process a camera frame using the original resolution."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        gesture = None
        hand_type = None

        if results.multi_hand_landmarks:
            landmarks = results.multi_hand_landmarks[0].landmark
            hand_type = results.multi_handedness[0].classification[0].label
            h, w, _ = frame.shape

            if self.is_volume_brightness_trigger(landmarks, w, h):
                pixel_distance = self.get_pixel_distance(landmarks[4], landmarks[8], w, h)
                hand_size = self.get_pixel_distance(landmarks[0], landmarks[9], w, h)

                normalized_dist = pixel_distance / max(hand_size, 1.0)
                value = np.interp(normalized_dist, [0.35, 1.2], [0.0, 1.0])
                value = float(np.clip(value, 0.0, 1.0))

                if value < 0.03: value = 0.0
                elif value > 0.97: value = 1.0

                self.volume_brightness_stable_frames += 1
                if self.volume_brightness_stable_frames >= self.required_volume_brightness_frames:
                    gesture = 'VOLUME' if hand_type == 'Right' else 'BRIGHTNESS'
                    return gesture, value, hand_type
                return None, 0.0, hand_type

            if self.is_next_previous_trigger(landmarks, w, h):
                self.next_prev_stable_frames += 1
                if self.next_prev_stable_frames >= self.required_next_prev_frames:
                    gesture = 'NEXT' if hand_type == 'Right' else 'PREVIOUS'
                    self.reset_gesture_state()
                    return gesture, 1.0, hand_type
            else:
                self.next_prev_stable_frames = 0
                self.volume_brightness_stable_frames = 0
                gesture, value = self.handle_media_gesture_logic(landmarks, w, h)
                if gesture:
                    return gesture, value, hand_type
        else:
            self.reset_gesture_state()

        return None, 0.0, hand_type

    def get_finger_states(self, landmarks, width, height):
        wrist = landmarks[0]
        def is_up(tip_idx, base_idx):
            return self.get_pixel_distance(landmarks[tip_idx], wrist, width, height) > \
                   self.get_pixel_distance(landmarks[base_idx], wrist, width, height)

        index_up, middle_up, ring_up, pinky_up = is_up(8, 6), is_up(12, 10), is_up(16, 14), is_up(20, 18)
        thumb_dist = self.get_pixel_distance(landmarks[4], wrist, width, height)
        hand_ref = self.get_pixel_distance(landmarks[0], landmarks[9], width, height)
        thumb_up = thumb_dist > (hand_ref * 0.9)

        return thumb_up, index_up, middle_up, ring_up, pinky_up

    def is_volume_brightness_trigger(self, landmarks, width, height):
        thumb_up, index_up, middle_up, ring_up, pinky_up = self.get_finger_states(landmarks, width, height)
        return pinky_up and index_up and not middle_up and not ring_up

    def is_next_previous_trigger(self, landmarks, width, height):
        thumb_up, index_up, middle_up, ring_up, pinky_up = self.get_finger_states(landmarks, width, height)
        gap = self.get_pixel_distance(landmarks[8], landmarks[12], width, height)
        return not thumb_up and index_up and middle_up and not ring_up and not pinky_up and gap > (width * 0.10)

    def handle_media_gesture_logic(self, landmarks, width, height):
        current_time = time.time()
        wrist, hand_size = landmarks[0], self.get_dist(landmarks[0], landmarks[9])
        thumb_index_dist = self.get_dist(landmarks[4], landmarks[8])
        is_circle = thumb_index_dist < (hand_size * 0.35)

        if is_circle:
            middle_up = self.get_dist(landmarks[12], wrist) > self.get_dist(landmarks[10], wrist) * 1.1
            ring_up = self.get_dist(landmarks[16], wrist) > self.get_dist(landmarks[14], wrist) * 1.1
            pinky_up = self.get_dist(landmarks[20], wrist) > self.get_dist(landmarks[18], wrist) * 1.1

            if middle_up and ring_up and pinky_up:
                self.armed_stable_frames += 1
                if self.armed_stable_frames >= self.required_stable_frames:
                    self.is_armed, self.arm_expiry_time = True, current_time + self.arm_timeout
                self.trigger_stable_frames = 0
            elif self.is_armed:
                middle_down = self.get_dist(landmarks[12], wrist) < self.get_dist(landmarks[10], wrist)
                ring_down = self.get_dist(landmarks[16], wrist) < self.get_dist(landmarks[14], wrist)

                if middle_down and ring_down:
                    self.trigger_stable_frames += 1
                    if self.trigger_stable_frames >= 3 and current_time < self.arm_expiry_time:
                        self.reset_gesture_state()
                        return 'PLAY_PAUSE', 1.0
                else: self.trigger_stable_frames = 0
        elif current_time > self.arm_expiry_time: self.reset_gesture_state()
        return None, 0.0

    def reset_gesture_state(self):
        self.is_armed = False
        self.armed_stable_frames = self.trigger_stable_frames = self.next_prev_stable_frames = self.volume_brightness_stable_frames = 0
        self.arm_expiry_time = 0.0
