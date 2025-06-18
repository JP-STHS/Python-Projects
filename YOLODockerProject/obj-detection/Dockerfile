FROM python:3.9-slim

WORKDIR /obj-detection

# Install system dependencies for OpenCV (including libGL)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

COPY . /obj-detection
COPY Shrek_character.png /app/images/

RUN pip install --upgrade pip
RUN pip install ultralytics pytesseract


CMD ["python", "obj-detection.py"]
