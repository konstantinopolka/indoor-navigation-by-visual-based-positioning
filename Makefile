# Makefile for PiCar-X ROS2 Jazzy MVP

WS_DIR := ws
SRC_DIR := $(WS_DIR)/src
SETUP := source $(HOME)/ros2_jazzy/install/setup.bash && source $(WS_DIR)/install/setup.bash

SHELL := /bin/bash
VOCAB := $(SRC_DIR)/orb_slam3_ros2_mono_publisher/vocabulary/ORBvoc.txt
CFG := $(SRC_DIR)/orb_slam3_ros2_mono_publisher/config/monocular/calib.yaml

.PHONY: all build run_camera run_motor run_teleop run_recorder run_all clean

all: build

build:
	@echo "[BUILD] Building colcon workspace..."
# 	cd $(WS_DIR) && source $(HOME)/ros2_jazzy/install/setup.bash && colcon build --symlink-install --packages-select 
	cd $(WS_DIR) && source $(HOME)/ros2_jazzy/install/setup.bash && colcon build --symlink-install --packages-select picarx_interfaces picarx_camera picarx_motor picarx_bringup teleop_twist_keyboard orbslam3_pose

run_camera:
	@echo "[RUN] Starting picarx_camera_node..."
	@echo "[RUN] the command: ros2 run picarx_camera camera_node"
	$(SHELL) -c "$(SETUP) && ros2 run picarx_camera camera_node"

run_motor:
	@echo "[RUN] Starting picarx_motor_node..."
	@echo "[RUN] the command: ros2 run picarx_motor motor_controller_node"
	$(SHELL) -c "$(SETUP) && ros2 run picarx_motor motor_controller_node"

run_teleop:
	@echo "[RUN] Starting teleop_twist_keyboard..."
	@echo "[RUN] the command: ros2 run teleop_twist_keyboard teleop_twist_keyboard"
	$(SHELL) -c "$(SETUP) && ros2 run teleop_twist_keyboard teleop_twist_keyboard"

run_recorder:
	@echo "[RUN] Recording topics to rosbag2..."
	@mkdir -p bags
	$(SHELL) -c "$(SETUP) && cd bags && ros2 bag record /camera/image_raw /camera/camera_info /cmd_vel"

run_slam:
	@echo "[RUN] Starting ORB SLAM3 Mono Publisher..."
	@echo "[RUN] the command: ros2 run orbslam3_pose mono $(VOCAB) $(CFG)"
	@echo "Make sure to run the camera node first to provide the necessary topics for SLAM."
	$(SHELL) -c "$(SETUP) && ros2 run orbslam3_pose mono $(VOCAB) $(CFG)"
	
run_all:
	@echo "[RUN] Starting full MVP launch..."
	$(SHELL) -c "$(SETUP) && ros2 launch picarx_bringup mvp_launch.py"

run_all_tmux:
	@echo "[RUN] Starting full MVP in tmux..."
	@tmux new-session -d -s picarx_mvp "$(SHELL) -lc '$(SETUP) && ros2 launch picarx_bringup mvp_launch.py'"
	@tmux attach -t picarx_mvp

clean:
	@echo "[CLEAN] Removing build/ install/ log/ in ws..."
	cd $(WS_DIR) && rm -rf build install log