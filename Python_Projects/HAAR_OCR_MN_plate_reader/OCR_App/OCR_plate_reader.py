#12/16/2024 - 12/30/2024
import cv2
import numpy as np

#load in custom cascade
plate_cascade = cv2.CascadeClassifier(r"assets\cascade.xml")

#turn on camera - press "Q" to exit program
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Unable to access the camera")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Camera feed unavailable")
        break

    flip_img = cv2.flip(frame, 1)
    gray = cv2.cvtColor(flip_img, cv2.COLOR_BGR2GRAY)

    # Resize for faster processing
    small_frame = cv2.resize(gray, (320, 240))

    # Only process every 3rd frame
    frame_count += 1
    if frame_count % 3 == 0:
        plates = plate_cascade.detectMultiScale(
            small_frame,
            scaleFactor=1.2,
            minNeighbors=4,
            minSize=(50, 50),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

        for (x, y, w, h) in plates:
            # Scale back to original resolution
            x, y, w, h = x * 2, y * 2, w * 2, h * 2
            cv2.rectangle(flip_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow("Camera Feed", flip_img)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
