FROM nvidia/cuda:12.6.1-runtime-ubi9

# Update the system and install Python
RUN dnf update -y && \
    dnf install -y python3.12 python3.12-pip && \
    dnf clean all


# Verify the installation
RUN python3.12 --version && pip3.12 --version


# Install APT dependency
RUN dnf install -y mesa-libGL



# Set the working directory in the container
WORKDIR /app


# Copy
COPY processing.py .
COPY requirements.txt .

# Install pip req
RUN pip3.12 install -r ./requirements.txt

# Download Mediapipe model
RUN curl -o pose_landmarker.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task

# Command to run when the container starts
ENTRYPOINT ["python3.12", "./processing.py"]