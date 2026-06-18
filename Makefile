# Makefile for PiCar-X ROS2 Jazzy MVP

WS_DIR := ws
SRC_DIR := $(WS_DIR)/src

SHELL := /bin/bash

.PHONY: all build run_camera run_motor run_teleop run_recorder run_all clean

all: build

build:
	@echo "[BUILD] Sourcing ROS 2 Jazzy and building colcon workspace..."
	@source /opt/ros/jazzy/setup.bash && 	cd $(WS_DIR) && 	colcon build --packages-select picarx_camera picarx_motor

run_camera:
	@echo "[RUN] Starting picarx_camera_node..."
	@source /opt/ros/jazzy/setup.bash && 	source $(WS_DIR)/install/setup.bash && 	ros2 run picarx_camera camera_node

run_motor:
	@echo "[RUN] Starting picarx_motor_node..."
	@source /opt/ros/jazzy/setup.bash && 	source $(WS_DIR)/install/setup.bash && 	ros2 run picarx_motor motor_controller_node

run_teleop:
	@echo "[RUN] Starting teleop_twist_keyboard..."
	@source /opt/ros/jazzy/setup.bash && 	source $(WS_DIR)/install/setup.bash && 	ros2 run teleop_twist_keyboard teleop_twist_keyboard

run_recorder:
	@echo "[RUN] Recording /camera/image_raw /camera/camera_info /cmd_vel to rosbag2..."
	@mkdir -p bags && 	cd bags && 	source /opt/ros/jazzy/setup.bash && 	source ../$(WS_DIR)/install/setup.bash && 	ros2 bag record /camera/image_raw /camera/camera_info /cmd_vel

run_all:
	@echo "[RUN] Starting camera, motor, teleop, and recorder (each in its own terminal)."
	@echo "Open four terminals on the Pi and run:"
	@echo "  1) make run_camera"
	@echo "  2) make run_motor"
	@echo "  3) make run_teleop"
	@echo "  4) make run_recorder"

clean:
	@echo "[CLEAN] Removing build/ install/ log/ in ws..."
	@cd $(WS_DIR) && 	rm -rf build install log