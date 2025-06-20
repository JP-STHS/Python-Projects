# from ultralytics import YOLO

# model = YOLO('yolov8n.pt')  # Replace with the model you want to use
# results = model('/app/images/Shrek_character.png')  # Replace with an actual image path
# results[0].save(filename="/app/images/output.jpg")  # Display the results

from ultralytics import YOLO
import cv2
import math
import easyocr
reader = easyocr.Reader(['en'])
# import pytesseract
# start webcam
cap = cv2.VideoCapture("http://host.docker.internal:8080/video_feed")
cap.set(3, 640)
cap.set(4, 480)

# model
model = YOLO("models/best.pt")

# object classes
classNames = ["license plate"]

while True:
    success, img = cap.read()
    if not success:
        break

    results = model(img, stream=True)

    # coordinates
    for r in results:
        boxes = r.boxes

        for box in boxes:
            # bounding box
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values

            # put box in cam
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

            # confidence
            confidence = math.ceil((box.conf[0]*100))/100

            # class name
            cls = int(box.cls[0])
            label = classNames[cls]
            print("Class:", cls, "| Confidence:", confidence, "| Box:", (x1, y1, x2, y2))


            # object details
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (255, 0, 0)
            thickness = 2

            cv2.putText(img, classNames[cls], org, font, fontScale, color, thickness)
            # If it's a license plate, apply OCR
            print("Label is:", label)
            if label == "license plate":
                plate_roi = img[y1:y2, x1:x2]
                # plate_gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
                # plate_eq = cv2.equalizeHist(plate_gray)
                # _, plate_thresh = cv2.threshold(plate_eq, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                # Send the preprocessed image to Tesseract
                # text = pytesseract.image_to_string(plate_thresh, config='--psm 7')
                # print(f"Detected Plate Text: {text.strip()}")

                # OCR using EasyOCR
                ocr_results = reader.readtext(plate_roi)
                for (bbox, text, conf) in ocr_results:
                    print(f"[EasyOCR] Text: {text} | Confidence: {conf:.2f}")

                # Optional: overlay the detected text
                #cv2.putText(img, text.strip(), (x1, y2 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # cv2.imshow('Webcam', img)
    # if cv2.waitKey(1) == ord('q'):
    #     break
    # Save one image every 30 frames 
    # frame_count = 0
    # save frames for later
    # if frame_count % 30 == 0:
    #     cv2.imwrite(f"/app/images/frame_{frame_count}.jpg", img)
    # frame_count += 1


cap.release()
cv2.destroyAllWindows()