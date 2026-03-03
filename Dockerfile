FROM ros:rolling

# System dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-opencv \
    git \
    i2c-tools \
    libcamera-dev \
    python3-libcamera \
    python3-gpiozero \
    libcap-dev \
    portaudio19-dev \
    python3-pyaudio \
    && rm -rf /var/lib/apt/lists/*

# ROS2 packages
RUN apt-get update && apt-get install -y \
    ros-rolling-image-transport \
    ros-rolling-image-transport-plugins \
    ros-rolling-cv-bridge \
    ros-rolling-teleop-twist-keyboard \
    ros-rolling-rosbag2 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/usr/lib/python3/dist-packages

# Python dependencies
RUN pip3 install --break-system-packages \
    smbus2 \
    adafruit-pca9685 \
    rpi-ws281x \
    gpiozero \
    pyaudio

# Workspace setup
RUN mkdir -p /ws/src
WORKDIR /ws

# Entry point
RUN echo 'source /opt/ros/rolling/setup.bash' >> ~/.bashrc
CMD ["bash"]
