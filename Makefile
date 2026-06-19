# Makefile for PiCar-X ROS2 Jazzy MVP
# Per-node sections with build / run / stop / clean targets

WS_DIR  := ws
SRC_DIR := $(WS_DIR)/src

SHELL   := /bin/bash
# Common ROS 2 environment for all run/stop commands
SETUP   := source $(HOME)/ros2_jazzy/install/setup.bash && source $(WS_DIR)/install/setup.bash

# ORB-SLAM3 assets
VOCAB   := $(SRC_DIR)/orb_slam3_ros2_mono_publisher/vocabulary/ORBvoc.txt
CFG     := $(SRC_DIR)/orb_slam3_ros2_mono_publisher/config/monocular/calib.yaml

# PID files so we can stop nodes started via make
PID_DIR     := .pids
CAMERA_PID  := $(PID_DIR)/camera.pid
MOTOR_PID   := $(PID_DIR)/motor.pid
TELEOP_PID  := $(PID_DIR)/teleop.pid
SLAM_PID    := $(PID_DIR)/slam.pid

.PHONY: \
	all all.build all.run all.stop all.clean \
	camera.build camera.run camera.stop camera.clean \
	motor.build motor.run motor.stop motor.clean \
	teleop.build teleop.run teleop.stop teleop.clean \
	slam.build slam.run slam.stop slam.clean \
	recorder.run recorder.stop

###############################################################################
# TOP-LEVEL (ALL) SECTION
###############################################################################

all: all.build

# Single colcon build for all relevant packages (one liner, as before)
all.build:
	@echo "[ALL] Building full workspace (interfaces + nodes + bringup + teleop + SLAM)..."
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --symlink-install \
			--packages-select picarx_interfaces picarx_camera picarx_motor \
			                  picarx_bringup teleop_twist_keyboard orbslam3_pose

# Use the bringup launch as the "all.run"
all.run:
	@echo "[ALL] Launching full MVP via picarx_bringup/mvp_launch.py..."
	$(SHELL) -c "$(SETUP) && ros2 launch picarx_bringup mvp_launch.py"

all.stop:
	@echo "[ALL] Stopping individual nodes started via make (best effort)..."
	$(MAKE) camera.stop
	$(MAKE) motor.stop
	$(MAKE) teleop.stop
	$(MAKE) slam.stop

all.clean:
	@echo "[ALL] Cleaning workspace build/install/log and PID files..."
	cd $(WS_DIR) && rm -rf build install log
	@rm -rf $(PID_DIR)

###############################################################################
# CAMERA SECTION
###############################################################################

camera.build:
	@echo "[CAMERA] Building picarx_camera..."
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --symlink-install --packages-select picarx_camera

camera.run:
	@echo "[CAMERA] Starting picarx_camera_node..."
	@mkdir -p $(PID_DIR)
	@$(SHELL) -c "$(SETUP) && ros2 run picarx_camera camera_node & echo $$! > $(CAMERA_PID)"
	@echo "[CAMERA] PID stored in $(CAMERA_PID)"

camera.stop:
	@echo "[CAMERA] Stopping picarx_camera_node (if running)..."
	@if [ -f $(CAMERA_PID) ]; then \
		PID=$$(cat $(CAMERA_PID)); \
		echo "[CAMERA] Killing PID $$PID"; \
		kill $$PID 2>/dev/null || true; \
		rm -f $(CAMERA_PID); \
	else \
		echo "[CAMERA] No PID file, nothing to stop."; \
	fi

camera.clean:
	@echo "[CAMERA] Cleaning picarx_camera from build/install..."
	cd $(WS_DIR) && rm -rf build/picarx_camera install/picarx_camera

###############################################################################
# MOTOR SECTION
###############################################################################

motor.build:
	@echo "[MOTOR] Building picarx_motor..."
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --symlink-install --packages-select picarx_motor

motor.run:
	@echo "[MOTOR] Starting picarx_motor_node..."
	@mkdir -p $(PID_DIR)
	@$(SHELL) -c "$(SETUP) && ros2 run picarx_motor motor_controller_node & echo $$! > $(MOTOR_PID)"
	@echo "[MOTOR] PID stored in $(MOTOR_PID)"

motor.stop:
	@echo "[MOTOR] Stopping picarx_motor_node (if running)..."
	@if [ -f $(MOTOR_PID) ]; then \
		PID=$$(cat $(MOTOR_PID)); \
		echo "[MOTOR] Killing PID $$PID"; \
		kill $$PID 2>/dev/null || true; \
		rm -f $(MOTOR_PID); \
	else \
		echo "[MOTOR] No PID file, nothing to stop."; \
	fi

motor.clean:
	@echo "[MOTOR] Cleaning picarx_motor from build/install..."
	cd $(WS_DIR) && rm -rf build/picarx_motor install/picarx_motor

###############################################################################
# TELEOP SECTION
###############################################################################

teleop.build:
	@echo "[TELEOP] Building teleop_twist_keyboard..."
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --symlink-install --packages-select teleop_twist_keyboard

teleop.run:
	@echo "[TELEOP] Starting teleop_twist_keyboard in the current terminal..."
	@echo "[TELEOP] Use this terminal to send key commands; CTRL-C to quit."
	$(SHELL) -c "$(SETUP) && ros2 run teleop_twist_keyboard teleop_twist_keyboard"

# teleop.stop is mostly symbolic, because teleop.run blocks until CTRL-C
teleop.stop:
	@echo "[TELEOP] No background teleop process to stop; exit the teleop terminal with CTRL-C."

teleop.clean:
	@echo "[TELEOP] Cleaning teleop_twist_keyboard from build/install..."
	cd $(WS_DIR) && rm -rf build/teleop_twist_keyboard install/teleop_twist_keyboard

###############################################################################
# SLAM SECTION (orbslam3_pose wrapper node)
###############################################################################

slam.build:
	@echo "[SLAM] Building orbslam3_pose..."
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --symlink-install --packages-select orbslam3_pose

slam.run:
	@echo "[SLAM] Starting ORB-SLAM3 mono node..."
	@mkdir -p $(PID_DIR)
	@$(SHELL) -c "$(SETUP) && ros2 run orbslam3_pose mono $(VOCAB) $(CFG) & echo $$! > $(SLAM_PID)"
	@echo "[SLAM] PID stored in $(SLAM_PID)"

slam.stop:
	@echo "[SLAM] Stopping ORB-SLAM3 mono node (if running)..."
	@if [ -f $(SLAM_PID) ]; then \
		PID=$$(cat $(SLAM_PID)); \
		echo "[SLAM] Killing PID $$PID"; \
		kill $$PID 2>/dev/null || true; \
		rm -f $(SLAM_PID); \
	else \
		echo "[SLAM] No PID file, nothing to stop."; \
	fi

slam.clean:
	@echo "[SLAM] Cleaning orbslam3_pose from build/install..."
	cd $(WS_DIR) && rm -rf build/orbslam3_pose install/orbslam3_pose

###############################################################################
# RECORDER (optional manual control)
###############################################################################

recorder.run:
	@echo "[RECORDER] Recording topics to rosbag2 (camera + cmd_vel)..."
	@mkdir -p bags
	$(SHELL) -c "$(SETUP) && cd bags && ros2 bag record \
		/camera/image_raw /camera/camera_info /cmd_vel"

recorder.stop:
	@echo "[RECORDER] Stop the recorder with Ctrl-C in the recorder terminal."