import cv2
from ultralytics import YOLO

# Confidence thresholds
vest_threshold = 0.5
helmet_threshold = 0.6
person_threshold = 0.6


def generate_frames():
    # Load model INSIDE function 
    model = YOLO(r"C:\Users\dhanu\Downloads\bestest.pt")
    class_names = model.names
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break
        results = model(frame, stream=True)
        person_detected = helmet_detected = vest_detected = False

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = class_names[cls_id].lower()
                conf = float(box.conf[0])

                if "person" in label and conf >= person_threshold:
                    person_detected = True
                elif "helmet" in label and conf >= helmet_threshold:
                    helmet_detected = True
                elif "vest" in label and conf >= vest_threshold:
                    vest_detected = True

        # Draw detection summary on frame
        blue = (255, 0, 0)
        green = (0, 255, 0)
        red = (0, 0, 255)

        summary = [
            ("person", person_detected),
            ("helmet", helmet_detected),
            ("vest", vest_detected),
        ]

        x_start = frame.shape[1] - 300
        y_start = 40

        for i, (label, detected) in enumerate(summary):
            label_pos = (x_start, y_start + i * 40)
            value_pos = (x_start + 140, y_start + i * 40)

            cv2.putText(frame, f"{label}:", label_pos,
                        cv2.FONT_HERSHEY_TRIPLEX, 0.8, blue, 2)
            cv2.putText(frame, "yes" if detected else "no", value_pos,
                        cv2.FONT_HERSHEY_TRIPLEX, 0.8,
                        green if detected else red, 2)

        # Encode the frame and yield for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()
