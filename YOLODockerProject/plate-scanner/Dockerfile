# FROM python:latest
FROM docker.io/pytorch/pytorch

WORKDIR /plate-scanner
# Install system dependencies

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

COPY . /plate-scanner/

RUN pip install --upgrade pip
RUN pip install pymongo 'numpy<2' ultralytics easyocr opencv-python flask