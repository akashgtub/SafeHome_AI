import os
import cv2
import uuid
import datetime
import numpy as np
from typing import Dict, Any, List, Tuple
from ..config import settings

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}

class VideoProcessor:
    @staticmethod
    def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Unsupported format '{ext}'. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            return False, f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        
        return True, ""

    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, Any]:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video file at {file_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        duration = float(frame_count / fps) if fps > 0 else 0.0

        cap.release()

        return {
            "fps": round(fps, 2),
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration": round(duration, 2)
        }

    @classmethod
    def anonymize_frame(cls, frame: np.ndarray, face_cascade=None) -> Tuple[np.ndarray, int]:
        """
        Detects faces using Haar cascade and applies strong Gaussian blur to each face region
        to protect occupant privacy before frames are displayed or sent to external vision providers.
        Returns (anonymized_frame, face_count).
        """
        output = frame.copy()
        if face_cascade is None:
            try:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception as e:
                print(f"[VideoProcessor] Warning: Could not initialize face cascade: {e}")
                face_cascade = None

        if face_cascade is None or face_cascade.empty():
            return output, 0

        try:
            gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))
            for (fx, fy, fw, fh) in faces:
                face_roi = output[fy:fy+fh, fx:fx+fw]
                ksize = max(25, (fw // 2) * 2 + 1)
                blurred_roi = cv2.GaussianBlur(face_roi, (ksize, ksize), 45)
                output[fy:fy+fh, fx:fx+fw] = blurred_roi
            return output, len(faces)
        except Exception as e:
            print(f"[VideoProcessor] Face blurring error: {e}")
            return output, 0

    @classmethod
    def sample_frames_and_detect_motion(
        cls,
        video_id: int,
        file_path: str,
        sample_interval_sec: float = 1.0,
        progress_callback = None,
        blur_faces: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Samples frames at regular intervals and uses OpenCV MOG2 background
        subtractor to detect motion contours, bounding boxes, and activity scores.
        Optionally blurs detected human faces if blur_faces is True (Privacy Mode).
        """
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {file_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        duration = total_frames / fps

        # Background subtractor for computer vision motion detection
        bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=30, detectShadows=True)

        face_cascade = None
        if blur_faces:
            try:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            except Exception as e:
                print(f"[VideoProcessor] Warning: Could not initialize face cascade: {e}")

        frames_sampled = []
        frame_index = 0
        step_frames = max(1, int(fps * sample_interval_sec))
        
        video_frame_dir = os.path.join(settings.FRAMES_DIR, f"vid_{video_id}")
        os.makedirs(video_frame_dir, exist_ok=True)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Feed to background subtractor to build background model
            fg_mask = bg_subtractor.apply(frame)

            if frame_index % step_frames == 0:
                current_sec = round(frame_index / fps, 2)
                mins = int(current_sec // 60)
                secs = int(current_sec % 60)
                time_str = f"{mins:02d}:{secs:02d}"

                # Remove shadows (gray in MOG2) by thresholding
                _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                motion_detected = False
                motion_score = 0.0
                bounding_boxes = []

                frame_area = frame.shape[0] * frame.shape[1]

                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > frame_area * 0.005: # more than 0.5% of frame
                        motion_detected = True
                        x, y, w, h = cv2.boundingRect(cnt)
                        bounding_boxes.append({"x": x, "y": y, "width": w, "height": h})
                        motion_score += (area / frame_area)

                motion_score = min(round(motion_score * 3.0, 3), 1.0) # normalize

                # Save sampled frame image
                frame_filename = f"frame_{mins:02d}_{secs:02d}.jpg"
                frame_out_path = os.path.join(video_frame_dir, frame_filename)

                save_frame = frame.copy()

                # Facial Anonymization Blur (if enabled in privacy preferences)
                # Strictly applied to the frame before any cloud transmission
                if blur_faces:
                    save_frame, _ = cls.anonymize_frame(save_frame, face_cascade)

                if motion_detected and bounding_boxes:
                    for b in bounding_boxes[:3]:
                        # Draw soft green bounding box for computer vision indicator
                        cv2.rectangle(save_frame, (b['x'], b['y']), (b['x'] + b['width'], b['y'] + b['height']), (83, 134, 22), 2)

                cv2.imwrite(frame_out_path, save_frame)

                relative_frame_url = f"/api/videos/frames/{video_id}/{frame_filename}"

                frames_sampled.append({
                    "timestamp_sec": current_sec,
                    "time_str": time_str,
                    "frame_path": frame_out_path,
                    "frame_url": relative_frame_url,
                    "motion_detected": motion_detected,
                    "motion_score": motion_score,
                    "bounding_boxes": bounding_boxes,
                    "faces_blurred": blur_faces,
                    "frame_width": frame.shape[1],
                    "frame_height": frame.shape[0]
                })

                if progress_callback:
                    pct = min(int((frame_index / total_frames) * 70), 70)
                    progress_callback(pct)

            frame_index += 1

        cap.release()
        return frames_sampled

    @staticmethod
    def generate_demo_video(target_path: str, duration_sec: int = 20) -> str:
        """
        Creates a realistic synthetic front-door security camera video clip in MP4 format.
        Features porch, walkway, front door, timestamp overlay, a simulated person walking up to porch,
        and a passing vehicle in the background.
        """
        if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
            return target_path

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        fps = 20
        total_frames = duration_sec * fps
        width, height = 720, 480

        # Try mp4v or avc1
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(target_path, fourcc, fps, (width, height))

        for f in range(total_frames):
            t = f / fps
            img = np.zeros((height, width, 3), dtype=np.uint8)

            # Sky / Background
            img[0:180, :] = [215, 200, 175] # warm outdoor daylight

            # Distant Street & Lawn
            img[180:260, :] = [80, 80, 80] # asphalt street
            img[260:340, :] = [45, 110, 50] # lawn grass green

            # Porch Floor & Pavers
            img[340:, :] = [180, 190, 195] # stone porch pavers

            # Pillars / Porch Architecture
            cv2.rectangle(img, (60, 40), (120, 360), (235, 235, 230), -1) # left pillar
            cv2.rectangle(img, (580, 40), (640, 360), (235, 235, 230), -1) # right pillar

            # Front Door Frame on left side
            cv2.rectangle(img, (0, 80), (80, 420), (100, 70, 50), -1) # wood door
            cv2.circle(img, (65, 250), 6, (220, 200, 120), -1) # brass handle

            # Planter / Plants on Porch
            cv2.rectangle(img, (130, 290), (170, 350), (60, 70, 120), -1) # pot
            cv2.circle(img, (150, 275), 25, (30, 120, 40), -1) # foliage

            # Vehicle passing on street between 00:12 and 00:16
            if 12.0 <= t <= 16.0:
                car_progress = (t - 12.0) / 4.0
                car_x = int(car_progress * (width + 200) - 100)
                car_y = 210
                # Car body (silver sedan)
                cv2.rectangle(img, (car_x, car_y), (car_x + 130, car_y + 35), (200, 205, 210), -1)
                cv2.rectangle(img, (car_x + 25, car_y - 20), (car_x + 95, car_y), (180, 185, 190), -1)
                # Wheels
                cv2.circle(img, (car_x + 25, car_y + 35), 10, (20, 20, 20), -1)
                cv2.circle(img, (car_x + 105, car_y + 35), 10, (20, 20, 20), -1)

            # Person walking to entrance between 00:04 and 00:11
            if 4.0 <= t <= 11.0:
                if t < 7.0:
                    # Walking up the walkway towards porch
                    prog = (t - 4.0) / 3.0
                    px = int(450 - prog * 160)
                    py = int(240 + prog * 110)
                    scale = 0.7 + prog * 0.4
                elif t < 9.0:
                    # Pausing near porch entrance, looking down at phone / door
                    px = 290
                    py = 350
                    scale = 1.1
                else:
                    # Turning and walking away
                    prog = (t - 9.0) / 2.0
                    px = int(290 + prog * 160)
                    py = int(350 - prog * 100)
                    scale = 1.1 - prog * 0.3

                head_radius = int(18 * scale)
                body_width = int(32 * scale)
                body_height = int(65 * scale)

                # Head (cap)
                cv2.circle(img, (px, py - body_height - head_radius), head_radius, (40, 40, 45), -1)
                # Jacket / Torso (dark jacket like in screenshot)
                cv2.rectangle(img, (px - body_width // 2, py - body_height), (px + body_width // 2, py - body_height // 3), (35, 45, 45), -1)
                # Backpack
                cv2.rectangle(img, (px + body_width // 3, py - body_height + 5), (px + body_width // 2 + 10, py - body_height // 2), (20, 20, 25), -1)
                # Legs / Jeans
                cv2.line(img, (px - 8, py - body_height // 3), (px - 10, py), (30, 40, 70), 6)
                cv2.line(img, (px + 8, py - body_height // 3), (px + 10, py), (30, 40, 70), 6)

            # Camera Timestamp Overlay in top right (like Ring camera: "Oct 18, 2026 04:32:15 PM")
            sec_display = int(t)
            time_str = f"Oct 18, 2026 04:32:{15 + sec_display:02d} PM"
            cv2.rectangle(img, (width - 240, 10), (width - 15, 36), (20, 20, 20), -1)
            cv2.putText(img, time_str, (width - 232, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

            # Camera name overlay in top left
            cv2.rectangle(img, (15, 10), (140, 36), (20, 20, 20), -1)
            cv2.putText(img, "Front Door Cam", (25, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

            out.write(img)

        out.release()
        return target_path
