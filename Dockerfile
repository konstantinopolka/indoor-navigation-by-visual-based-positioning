FROM ros:rolling

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    meson \
    ninja-build \
    pkg-config \
    libyaml-dev \
    python3-yaml \
    python3-ply \
    python3-jinja2 \
    libevent-dev \
    libdrm-dev \
    libcap-dev \
    python3-pip \
    python3-opencv \
    git \
    i2c-tools \
    python3-gpiozero \
    python3-lgpio \
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

# Use /build as working dir for compiling C++ libraries
WORKDIR /build

# libcamera — pinned commit for picamera2 compatibility
RUN git clone https://github.com/raspberrypi/libcamera.git && \
    cd libcamera && \
    git checkout 6ddd79b

# Configure build (separate layer — cached if meson succeeds)
RUN meson setup libcamera/build libcamera/ \
    -Dpipelines=rpi/vc4,rpi/pisp \
    -Dipas=rpi/vc4,rpi/pisp \
    --buildtype=release

# Compile and install (separate layer — only re-runs if above changes)
RUN ninja -C libcamera/build/ install && ldconfig

# kmsxx — required by picamera2's DrmPreview (imported unconditionally)
RUN git clone https://github.com/tomba/kmsxx.git
RUN meson setup kmsxx/build kmsxx/ --buildtype=release
RUN ninja -C kmsxx/build/ install && ldconfig

# Python path: libcamera bindings (installed) + kmsxx bindings (build dir only)
ENV PYTHONPATH=/usr/local/lib/aarch64-linux-gnu/python3.12/site-packages:/build/kmsxx/build/py

# Python dependencies
RUN pip3 install --break-system-packages \
    smbus2 \
    adafruit-pca9685 \
    rpi-ws281x \
    gpiozero \
    lgpio \
    pyaudio \
    picamera2

# Switch to ROS workspace
RUN mkdir -p /ws/src
WORKDIR /ws

# Entry point
RUN echo 'source /opt/ros/rolling/setup.bash' >> ~/.bashrc
CMD ["bash"]
