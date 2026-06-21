# PiCar-X ROS2 Jazzy Makefile Overview

This document summarizes how the  `Makefile` for the PiCar-X ROS 2 Jazzy MVP is structured and how to use it to build and run the different components (camera, motor, teleop, SLAM, detection, recorder, and full bringup).

The Makefile lives in the project root:

```bash
~/indoor-navigation-by-visual-based-positioning/Makefile
```

and controls the ROS 2 workspace:

```bash
~/indoor-navigation-by-visual-based-positioning/ws
```

The Makefile assumes:

- ROS 2 Jazzy is built from source under `~/ros2_jazzy`.
- Your per-project workspace is under `ws/`.
- `setup.bash` in `~/ros2_jazzy/install` and `ws/install` must be sourced before any `ros2` command.

---

## Workspace Structure

The workspace contains the following packages:

```
ws/src/
├── picarx_interfaces          # Shared topic and node name constants
├── picarx_camera              # Camera node
├── picarx_motor               # Motor controller node
├── hailo_object_detection     # Hailo-8 NPU YOLOv8 object detection node
├── picarx_bringup             # Launch file, recorder and teleop scripts
├── teleop_twist_keyboard      # External keyboard teleop package
└── orb_slam3_ros2_mono_publisher  # ORB-SLAM3 monocular wrapper (orbslam3_pose)
```

### `picarx_interfaces` — Shared Constants

All ROS 2 topic names and node names are defined as Python constants in the `picarx_interfaces` package:

- `picarx_interfaces/topics.py` — topic name constants (e.g. `CAMERA_IMAGE_RAW`, `CMD_VEL`, `POSE_ORB1`)
- `picarx_interfaces/nodes.py` — node name constants (e.g. `CAMERA_NODE`, `SLAM_NODE`)

All Python nodes and the launch file import from this package. The C++ SLAM node is connected via ROS 2 remappings in the launch file, so its topic names are also driven by the constants without modifying its source code.

### `picarx_bringup/scripts/` — Teleop and Recorder Launchers

The bringup package contains two Python scripts that use the topic constants from `picarx_interfaces`:

- `run_teleop.py` — launches `teleop_twist_keyboard` with the correct `cmd_vel` topic remapping
- `run_recorder.py` — launches `ros2 bag record` with the full canonical topic list

These are invoked by the Makefile targets `teleop.run` and `recorder.run`.

---

## Global Variables and Layout

Key variables at the top of the Makefile:

- `WS_DIR := ws`  
  Path to the ROS 2 workspace.

- `SRC_DIR := $(WS_DIR)/src`  
  Path to source packages.

- `SETUP := source $(HOME)/ros2_jazzy/install/setup.bash && source $(WS_DIR)/install/setup.bash`  
  Common environment setup used for all `ros2` commands.

- `VOCAB` and `CFG`  
  Paths to ORB-SLAM3 vocabulary and monocular calibration config:
  ```make
  VOCAB := $(SRC_DIR)/orb_slam3_ros2_mono_publisher/vocabulary/ORBvoc.txt
  CFG   := $(SRC_DIR)/orb_slam3_ros2_mono_publisher/config/monocular/calib.yaml
  ```

- PID management for background nodes:
  ```make
  PID_DIR        := .pids
  CAMERA_PID     := $(PID_DIR)/camera.pid
  MOTOR_PID      := $(PID_DIR)/motor.pid
  SLAM_PID       := $(PID_DIR)/slam.pid
  DETECTION_PID  := $(PID_DIR)/detection.pid
  ```

PID files are used to stop camera, motor, detection, and SLAM nodes started in the background.

---

## Top-Level Targets (`all.*`)

### `make all` / `make all.build`

Builds all relevant packages in **one** colcon invocation:

```make
all.build:
	@echo "[ALL] Building full workspace (interfaces + nodes + bringup + teleop + SLAM)..."
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build \
			--packages-select picarx_interfaces picarx_camera picarx_motor \
			                  picarx_bringup hailo_object_detection \
				                  teleop_twist_keyboard orbslam3_pose
```

This compiles:

- `picarx_interfaces` (constants for topics and node names)
- `picarx_camera`
- `picarx_motor`
- `picarx_bringup` (launch file + teleop/recorder scripts)
- `hailo_object_detection` (Hailo-8 YOLOv8 object detection)
- `teleop_twist_keyboard`
- `orbslam3_pose` (ORB-SLAM3 wrapper)

Use:

```bash
make all.build
```

### `make all.run`

Runs the full system via the bringup launch file:

```make
all.run:
	@echo "[ALL] Launching full MVP via picarx_bringup/mvp_launch.py..."
	$(SHELL) -c "$(SETUP) && ros2 launch picarx_bringup mvp_launch.py"
```

Use:

```bash
make all.run
```

This starts:

- Camera node (`picarx_camera`)
- Motor node (`picarx_motor`)
- Hailo object detection node (`hailo_object_detection`)
- Recorder (`ros2 bag record` with topics defined via `picarx_interfaces` constants)
- ORB-SLAM3 mono node (`orbslam3_pose`)

### `make all.stop`

Best-effort stop for nodes started via individual `make *.run` targets:

```make
all.stop:
	$(MAKE) camera.stop
	$(MAKE) motor.stop
	$(MAKE) teleop.stop
	$(MAKE) slam.stop
	$(MAKE) detection.stop
```

### `make all.clean`

Cleans the full workspace build/install/log and all PID files:

```make
all.clean:
	cd $(WS_DIR) && rm -rf build install log
	@rm -rf $(PID_DIR)
```

---

## Camera Section (`camera.*`)

### `make camera.build`

Builds only the camera package:

```make
camera.build:
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --packages-select picarx_camera
```

### `make camera.run`

Runs the camera node in the background and stores its PID:

```make
camera.run:
	@$(SHELL) -c "$(SETUP) && ros2 run picarx_camera camera_node & echo $$! > $(CAMERA_PID)"
```

The node publishes:

- `/camera/image_raw`
- `/camera/camera_info`

### `make camera.stop`

Stops the camera node using the stored PID file.

### `make camera.clean`

Removes only the camera package's build/install artifacts.

---

## Motor Section (`motor.*`)

### `make motor.build`

Builds only the motor package.

### `make motor.run`

Runs the motor controller node in the background:

```make
motor.run:
	@$(SHELL) -c "$(SETUP) && ros2 run picarx_motor motor_controller_node & echo $$! > $(MOTOR_PID)"
```

The node subscribes to `/cmd_vel` (via the `CMD_VEL` constant from `picarx_interfaces`) and drives the PiCar-X motors and steering accordingly.

### `make motor.stop`

Stops the motor node using the stored PID file.

### `make motor.clean`

Removes only the motor package's build/install artifacts.

---

## Teleop Section (`teleop.*`)

`teleop_twist_keyboard` is an external package that reads keyboard input and publishes `Twist` messages to `/cmd_vel`. It must run attached to a **real terminal** and cannot be daemonized with `&`.

### `make teleop.build`

```make
teleop.build:
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --packages-select teleop_twist_keyboard
```

### `make teleop.run`

Runs teleop in the foreground via the `run_teleop.py` script from `picarx_bringup`:

```make
teleop.run:
	$(SHELL) -c "$(SETUP) && python3 $(SRC_DIR)/picarx_bringup/picarx_bringup/scripts/run_teleop.py"
```

The script passes a ROS 2 remapping argument so that teleop publishes to the canonical `CMD_VEL` topic defined in `picarx_interfaces`. Use `Ctrl-C` to stop.

### `make teleop.stop`

Symbolic — teleop is stopped by `Ctrl-C` in its terminal.

### `make teleop.clean`

Removes the teleop package's build/install artifacts.

---

## SLAM Section (`slam.*`)

Controls the ORB-SLAM3 monocular wrapper node `orbslam3_pose`.

### `make slam.build`

```make
slam.build:
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --packages-select orbslam3_pose
```

### `make slam.run`

Runs the mono SLAM node in the background:

```make
slam.run:
	@$(SHELL) -c "$(SETUP) && ros2 run orbslam3_pose mono $(VOCAB) $(CFG) & echo $$! > $(SLAM_PID)"
```

The node subscribes to `/camera/image_raw` and publishes:

- `/pose_orb1`, `/pose_orb2` — camera pose estimates
- `/odom` — odometry
- `/tracked_mappoints`, `/all_mappoints` — 3D map points
- `/tracking_image` — debug visualization of tracked features
- `/orbslam3_mono_node/kf_markers` — keyframe markers for RViz

### `make slam.stop`

Stops the SLAM node using the stored PID file.

### `make slam.clean`

Removes the SLAM package's build/install artifacts.

---
## Detection Section (`detection.*`)

Controls the Hailo-8 NPU YOLOv8 object detection node `hailo_object_detection`.

### `make detection.build`

Builds only the detection package:

```make
detection.build:
	@echo "[HAILO] Building hailo_object_detection..."
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --symlink-install --packages-select hailo_object_detection
```

### `make detection.run`

Runs the Hailo object detection node in the background:

```make
detection.run:
	@echo "[HAILO] Starting Hailo object detection node..."
	@mkdir -p $(PID_DIR)
	@$(SHELL) -c "$(SETUP) && ros2 run hailo_object_detection detector_node & echo $$! > $(DETECTION_PID)"
	@echo "[HAILO] PID stored in $(DETECTION_PID)"
```

The node subscribes to `/camera/image_raw` (`CAMERA_IMAGE_RAW`) and publishes:

- `/hailo/detections` — `vision_msgs/Detection2DArray` with bounding boxes, class IDs, and confidence scores

Requires a Hailo-8 NPU with HailoRT driver and a YOLOv8 HEF model file.

### `make detection.stop`

Stops the detection node using the stored PID file.

```make
detection.stop:
	@echo "[HAILO] Stopping Hailo object detection node (if running)..."
	@if [ -f $(DETECTION_PID) ]; then \
		PID=$$(cat $(DETECTION_PID)); \
		echo "[HAILO] Killing PID $$PID"; \
		kill $$PID 2>/dev/null || true; \
		rm -f $(DETECTION_PID); \
	else \
		echo "[HAILO] No PID file, nothing to stop."; \
	fi
```

### `make detection.clean`

Removes only the detection package's build/install artifacts.

```make
detection.clean:
	@echo "[HAILO] Cleaning hailo_object_detection from build/install..."
	rm -rf build/hailo_object_detection install/hailo_object_detection
```


---

## Recorder Section (`recorder.*`)

Manual control of rosbag2 recording, independent of the full bringup launch.

### `make recorder.run`

Records all canonical topics via the `run_recorder.py` script from `picarx_bringup`:

```make
recorder.run:
	@mkdir -p bags
	$(SHELL) -c "$(SETUP) && python3 $(SRC_DIR)/picarx_bringup/picarx_bringup/scripts/run_recorder.py"
```

The script reads the topic list from `picarx_interfaces` constants and records to a timestamped bag under `bags/`. Topics recorded:

- `/camera/image_raw`
- `/camera/camera_info`
- `/cmd_vel`
- `/pose_orb1`, `/pose_orb2`
- `/odom`
- `/tracked_mappoints`
- `/tracking_image`
- `/hailo/detections` (Hailo-8 YOLOv8 object detections)

Stop with `Ctrl-C`.

### `make recorder.stop`

Reminder-only — recording is stopped with `Ctrl-C` in the recorder terminal.

---

## Typical Workflows

### 1. Full system (recommended)

```bash
# From project root
make all.build      # build everything once
make all.run        # run full MVP via launch file
# CTRL-C to stop
```

### 2. Debugging nodes individually

Example: camera + detection + SLAM + teleop in separate terminals:

```bash
# Terminal 1 – camera (background)
make camera.run

# Terminal 2 – detection (background)
make detection.run

# Terminal 3 – SLAM (background)
make slam.run

# Terminal 4 – teleop (foreground, keyboard input here)
make teleop.run

# Terminal 5 – recorder (optional, foreground)
make recorder.run
```

To stop background nodes:

```bash
make camera.stop
make detection.stop
make slam.stop
# teleop and recorder are stopped with CTRL-C in their own terminals
```

### 3. Clean rebuild

```bash
make all.clean
make all.build
```
