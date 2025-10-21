# FROM python:3.9-slim
FROM docker.io/pytorch/pytorch


WORKDIR /obj-detection

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

COPY . /obj-detection

RUN pip install --upgrade pip
# RUN pip install ultralytics pytesseract
RUN pip install ultralytics easyocr opencv-python

CMD ["python", "obj-detection.py"]
