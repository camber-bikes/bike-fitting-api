FROM nvidia/cuda:12.6.1-runtime-ubi9

# Update the system and install Python
RUN dnf update -y && \
    dnf install -y python3.12 python3.12-pip mesa-libGL && \
    dnf clean all


# Set the working directory in the container
WORKDIR /app


# Copy
COPY processing.py .
COPY constants.py .
COPY calculation.py .
COPY drawing.py .

COPY requirements.txt .

# Install pip req
RUN pip3.12 install -r ./requirements.txt

# Download Mediapipe model
RUN curl -o pose_landmarker.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task
RUN curl -o selfie_segmenter.tflite https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite

# Command to run when the container starts
ENTRYPOINT ["python3.12", "./processing.py"]