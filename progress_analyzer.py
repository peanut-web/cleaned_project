import cv2
import os
from skimage.metrics import structural_similarity as ssim

def run_progress_check(expected_path, actual_path):
    try:
        ext_expected = os.path.splitext(expected_path)[1].lower()
        ext_actual = os.path.splitext(actual_path)[1].lower()

        if ext_expected in ['.jpg', '.jpeg', '.png'] and ext_actual in ['.jpg', '.jpeg', '.png']:
            img1 = cv2.imread(expected_path)
            img2 = cv2.imread(actual_path)
            if img1 is None or img2 is None:
                return "❌ Failed to read one or both images."

            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            score, _ = ssim(gray1, gray2, full=True)
            return round(score * 100, 2)

        elif ext_expected in ['.mp4', '.avi', '.mov', '.mkv'] and ext_actual in ['.mp4', '.avi', '.mov', '.mkv']:
            cap1 = cv2.VideoCapture(expected_path)
            cap2 = cv2.VideoCapture(actual_path)

            if not cap1.isOpened() or not cap2.isOpened():
                return "❌ One or both videos could not be opened."

            total_progress = 0
            count = 0
            max_frames = 10
            frame_step = 10

            while count < max_frames:
                ret1, frame1 = cap1.read()
                ret2, frame2 = cap2.read()

                if not ret1 or not ret2:
                    break

                if count % frame_step == 0:
                    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

                    if gray1.shape != gray2.shape:
                        gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

                    score, _ = ssim(gray1, gray2, full=True)
                    total_progress += score * 100

                count += 1

            cap1.release()
            cap2.release()

            if count == 0:
                return "❌ No frames compared."

            avg_progress = total_progress / (count / frame_step)
            return round(avg_progress, 2)
        else:
            return "❌ Unsupported file types or mismatch between files."
    except Exception as e:
        return f"⚠️ Error comparing media: {e}"
