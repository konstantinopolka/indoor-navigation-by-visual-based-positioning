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
    && rm -rf /var/lib/apt/lists/*

# ROS2 packages
RUN apt-get update && apt-get install -y \
    ros-rolling-image-transport \
    ros-rolling-image-transport-plugins \
    ros-rolling-cv-bridge \
    ros-rolling-teleop-twist-keyboard \
    ros-rolling-rosbag2 \
    && rm -rf /var/lib/apt/lists/*

# Make system Python packages (libcamera, gpiozero) visible to pip-installed packages
ENV PYTHONPATH=/usr/lib/python3/dist-packages:${PYTHONPATH}

# Python dependencies
RUN pip3 install --break-system-packages \
    smbus2 \
    adafruit-pca9685 \
    rpi-ws281x \
    picamera2 \
    gpiozero

# Workspace setup
RUN mkdir -p /ws/src
WORKDIR /ws

# Entry point
RUN echo 'source /opt/ros/rolling/setup.bash' >> ~/.bashrc
CMD ["bash"]
