from ultralytics import YOLO
import cv2
import math
import easyocr
import re
import pymongo
from pymongo import MongoClient
from flask import Flask, request, render_template, redirect, url_for, jsonify
import threading

app = Flask(__name__)

cluster = MongoClient("mongodb://host.docker.internal:27017/")
db = cluster["LicensePlateScanner"]
cars = db["Cars"]
students = db["Students"]
studentcars = db["StudentCars"]

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
# shared variable
last_detected = {"stuplate": None, "student": None, "plate": None}
last_detected = {"stuplate": "TESTSTUDENT", "student": "John Doe", "plate": "PLATETEST"}

# frame_count = 0
# plate_pattern = re.compile(r"^[A-Z]{3}-?\d{3}$")  # Adjust per region
plate_pattern = re.compile(r"^[A-Z0-9\- ]{1,8}$") #most US plates

@app.route('/')
def index():
    student_list = list(students.find({}))
    return render_template('index.html', students=student_list) # Make sure templates/index.html/db exists

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form['name']
    sid = int(request.form['id'])  # Convert to int
    res_status = request.form['res-status']
    if students.find_one({"_id": sid}): return "Student ID already exists", 400
    new_student = {
        "_id": sid,
        "Name": name,
        "ResidentialStatus": res_status
    }

    students.insert_one(new_student)
    return redirect(url_for('index'))

@app.route('/add_car', methods=['POST'])
def add_car():
    plate = request.form['plate'].strip().upper()
    make = request.form['make']
    model = request.form['model']
    state = request.form['state']
    country = request.form['country']
    color = request.form['color']
    year = request.form['year']
    student_id = int(request.form['student_id'])

    car_result = cars.insert_one({
        "LicensePlate": plate,
        "Make": make,
        "Model": model,
        "State": state,
        "Country": country,
        "Color": color,
        "Year": year
    })
    car_id = car_result.inserted_id

    studentcars.insert_one({
        "CarID": car_id,
        "StuID": student_id
    })

    return redirect(url_for('index'))


@app.route('/view_students')
def view_students():
    student_list = list(students.find({}))
    for s in student_list:
        s['_id'] = str(s['_id'])  # convert ObjectId for safe rendering
    return render_template('view_students.html', students=student_list)
@app.route('/view_cars')
def view_cars():
    car_list = list(cars.find({}))
    for c in car_list:
        c['_id'] = str(c['_id'])  # convert ObjectId for safe rendering
    return render_template('view_cars.html', cars=car_list)
@app.route('/find_student')
def find_student():
    try:
        stu_id = int(request.args.get('id'))
    except (ValueError, TypeError):
        return "Invalid student ID.", 400

    stu = students.find_one({"_id": stu_id})
    if not stu:
        return render_template("find_students.html", students=[], searched=stu_id)

    #find car links in studentcars
    links = list(studentcars.find({"StuID": stu_id}))

    car_ids = [link["CarID"] for link in links]
    linked_cars = list(cars.find({"_id": {"$in": car_ids}}))

    stu["cars"] = linked_cars
    return render_template("find_students.html", students=[stu], searched=stu_id)


@app.route('/last_detection')
def get_last_detection():
    return jsonify(last_detected)

def plate_detection():
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
                #Round Up
                #confidence = math.ceil((box.conf[0]*100))/100
                #Round to 2 decimals
                confidence = round(float(box.conf[0]), 2)
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
                    margin = 5
                    plate_roi = img[max(y1+margin,0):max(y2-margin,0), max(x1+margin,0):max(x2-margin,0)]

                    # Enhance plate for OCR
                    gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    enhanced = clahe.apply(gray)
                    # plate_eq = cv2.equalizeHist(plate_gray)
                    # _, plate_thresh = cv2.threshold(plate_eq, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    # Send the preprocessed image to Tesseract
                    # text = pytesseract.image_to_string(plate_thresh, config='--psm 7')
                    # print(f"Detected Plate Text: {text.strip()}")

                    # OCR using EasyOCR
                    ocr_results = reader.readtext(enhanced)
                    for (bbox, text, conf) in ocr_results:
                        cleaned = text.strip().replace(" ", "").upper()
                        if conf > 0.5 and plate_pattern.match(cleaned):
                            print(f"[MATCHED] Text: {cleaned} | Confidence: {conf:.2f}")
                            #mongo code
                            #link plate to car
                            car = cars.find_one({"LicensePlate": cleaned})
                            last_detected["plate"] = cleaned
                            if car:
                                car_id = car["_id"]

                                #link car id to corresponding student id
                                mapping = studentcars.find_one({"CarID": car_id})

                                if mapping:
                                    student_id = mapping["StuID"]

                                    #link student id to student
                                    student = students.find_one({"_id": student_id})

                                    if student:
                                        print("Student found:")
                                        print(student)
                                        last_detected["stuplate"] = cleaned
                                        last_detected["student"] = student["Name"]  # or student["FirstName"] if structured                                        
                                    else:
                                        print("No student found for this car.")
                                else:
                                    print("No student-car mapping found for this plate.")
                            else:
                                print("No car found with this plate.")
                        # print(f"[EasyOCR] Text: {text} | Confidence: {conf:.2f}")

                    #superflous optional chagpt suggestion: overlay the detected text
                    #cv2.putText(img, text.strip(), (x1, y2 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    #thread dedicated to stream as flask runs
    threading.Thread(target=plate_detection, daemon=True).start()
    app.run(host='0.0.0.0', debug=True)