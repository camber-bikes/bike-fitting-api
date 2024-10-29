FROM ubuntu:24.04

RUN apt update && apt install -y python3 python3-pip libgl1 curl libglib2.0-0 ffmpeg

WORKDIR /app

COPY main.py .
COPY handlers.py .
COPY media.py .
COPY constants.py .
COPY calculation.py .
COPY config.py .
COPY drawing.py .
COPY storage.py .

COPY requirements.txt . 

RUN pip3 install --break-system-packages -r ./requirements.txt

RUN mkdir -p /app/models && \
    curl -o /app/models/pose_landmarker.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task && \
    curl -o /app/models/selfie_segmenter.tflite https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite

CMD ["python3", "./main.py"]
