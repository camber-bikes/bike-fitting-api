FROM ubuntu:24.04

RUN apt update && apt install -y python3 python3-pip libgl1 curl libglib2.0-0

WORKDIR /app

COPY processing.py .
COPY constants.py .
COPY calculation.py .
COPY drawing.py .
COPY file_operations.py .
COPY gpu.py .

COPY requirements.txt . 

RUN pip3 install --break-system-packages -r ./requirements.txt

RUN curl -o pose_landmarker.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task
RUN curl -o selfie_segmenter.tflite https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite

CMD ["python3", "./processing.py"]
