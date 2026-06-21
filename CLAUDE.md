# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ROS 2 Jazzy monocular visual SLAM pipeline for the PiCar-X robot (Raspberry Pi 5). A camera node streams images to ORB-SLAM3, a motor node drives the car from `/cmd_vel` Twist messages, and teleop provides keyboard control. The launch file ties everything together with automatic rosbag2 recording for offline analysis.

## Prerequisites / Environment

- **ROS 2 Jazzy** built from source under `~/ros2_jazzy` (not a system package — all `source` paths point to `~/ros2_jazzy/install/setup.bash`).
- **Python dependencies**: `picamera2`, `cv_bridge`, `lgpio`, `gpiozero` (PiCar-X libraries at `/robot-hat` and `/picar-x`).
- **ORB-SLAM3**: external submodule at `ws/src/orb_slam3_ros2_mono_publisher` (C++ package `orbslam3_pose`). Needs vocabulary file at `vocabulary/ORBvoc.txt` and calibration at `config/monocular/calib.yaml`.
- **teleop_twist_keyboard**: external ROS 2 package under `ws/src/`.
- **Hardware**: PiCar-X robot hat with I2C motor control, Picamera2 camera, Raspberry Pi 5 GPIO (must use `gpiochip0`, not the default `gpiochip4` — the motor node monkey-patches `gpiozero` for this).

## Commands

Everything is driven by the root `Makefile`. All `ros2` commands require sourcing both ROS 2 and the workspace overlay:

```
source ~/ros2_jazzy/install/setup.bash && source ws/install/setup.bash
```

### Build

```bash
make all.build      # build everything (interfaces, camera, motor, bringup, teleop, SLAM)
make camera.build   # build only picarx_camera
make motor.build    # build only picarx_motor
make slam.build     # build only orbslam3_pose
make teleop.build   # build only teleop_twist_keyboard
```

### Run

```bash
make all.run        # full system via launch file (camera + motor + SLAM + recorder)
make camera.run     # camera node in background (PID stored in .pids/)
make motor.run      # motor node in background
make slam.run       # ORB-SLAM3 mono node in background
make teleop.run     # keyboard teleop in foreground (must have real TTY)
make recorder.run   # rosbag2 recording in foreground
```

### Stop

```bash
make camera.stop    # kill via saved PID
make motor.stop
make slam.stop
make all.stop       # stop all background nodes
make all.clean      # wipe build/, install/, log/, and .pids/
```

## Architecture

### Package Dependency Graph

```
picarx_interfaces  (shared topic/node name constants — no runtime dependencies)
     ↑
     ├── picarx_camera     (publishes /camera/image_raw, /camera/camera_info)
     ├── picarx_motor      (subscribes /cmd_vel → drives PiCar-X motors)
     ├── picarx_bringup    (launch file + teleop/recorder launcher scripts)
     └── orbslam3_pose     (C++; subscribes /camera/image_raw, publishes pose/map topics)
```

### Topic Flow

```
[camera] ──/camera/image_raw──→ [orbslam3_pose] ──/pose_orb1, /pose_orb2, /odom, /tracked_mappoints──→ [rosbag2]
                                    ↑
[teleop_twist_keyboard] ──/cmd_vel──→ [motor]  (Twist → PWM speed + servo angle)
```

All topic names are centralized in `picarx_interfaces/topics.py`. Node names are in `picarx_interfaces/nodes.py`. The C++ SLAM node uses ROS 2 remappings in the launch file to align its hardcoded topic names with these constants — no C++ source modification needed.

### Key Source Files

| File | Role |
|------|------|
| `ws/src/picarx_bringup/launch/mvp_launch.py` | Master launch: starts camera, motor, SLAM, recorder; shuts down if any node exits |
| `ws/src/picarx_camera/picarx_camera/camera_node.py` | Picamera2 → ROS Image publisher (~30 FPS, 640×480 RGB) |
| `ws/src/picarx_motor/picarx_motor/motor_controller_node.py` | Twist subscriber → `Picarx()` motor commands |
| `ws/src/picarx_interfaces/picarx_interfaces/topics.py` | Single source of truth for all ROS topic names |
| `ws/src/picarx_interfaces/picarx_interfaces/nodes.py` | Single source of truth for all ROS node names |
| `ws/src/picarx_bringup/picarx_bringup/scripts/run_teleop.py` | Wraps `teleop_twist_keyboard` with dynamic `--ros-args` remapping from topic constants |
| `ws/src/picarx_bringup/picarx_bringup/scripts/run_recorder.py` | Wraps `ros2 bag record` with topic list from constants |
| `ws/src/picarx_bringup/config/params.yaml` | Runtime parameters for camera and motor nodes (loaded via launch file) |

### Docker Support

There are Dockerfiles for containerized deployment on the RPi5:

- `Dockerfile` — base image (`ros:rolling`) with libcamera, kmsxx, picamera2, and all Python dependencies compiled from source for RPi5.
- `Dockerfile.motor` — extends the base image with motor-specific lgpio/gpiozero patches. Force-installs `lgpio` and creates a `gpio` group for `/dev/gpiochip0` access.
- `docker-compose.yml` — runs `camera`, `motor`, `teleop`, and `recorder` as separate containers with host networking, privileged mode, device mounts for GPIO/I2C/DRM, and volume mounts for the Robot HAT and PiCar-X Python libraries.

**Note**: These are in the working tree as deleted (`D` in git status) — they were present in earlier commits but appear to have been removed from HEAD. The current workflow uses the Makefile on bare-metal ROS 2 Jazzy instead.

### RPi5 GPIO Quirk

On Raspberry Pi 5, `gpiozero` defaults to `gpiochip4`, which is a kernel symlink that doesn't resolve inside Docker. The motor controller node monkey-patches `lgpio.LGPIOFactory` to force `gpiochip0` (the real hardware chip). This comes from `/dev/gpiochip0` in the `docker-compose.yml` device mounts.

### Bag Recording

rosbag2 records to timestamped directories under `bags/` (e.g., `bags/mvp_bag_2026-06-21_14-30-00`). The topic list is defined in `run_recorder.py` using `picarx_interfaces` constants. The launch file can disable recording via `start_recorder:=false`.

## Adding a New Topic

1. Add the constant to `picarx_interfaces/topics.py`.
2. If needed, add the topic to `run_recorder.py`'s `TOPICS_TO_RECORD` list.
3. If needed, add it to the `ExecuteProcess` cmd list in `mvp_launch.py`.
4. If the SLAM node needs to publish it, add a remapping in `mvp_launch.py`.
