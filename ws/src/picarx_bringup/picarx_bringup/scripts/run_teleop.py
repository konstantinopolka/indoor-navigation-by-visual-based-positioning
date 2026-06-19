#!/usr/bin/env python3
"""
Launcher for teleop_twist_keyboard.
Reads the cmd_vel topic name from picarx_interfaces.topics
and passes it as a ROS 2 remapping argument.
This script replaces itself with the ros2 run process (via execvp),
so the terminal behavior is identical to calling ros2 run directly.
"""
import os
import sys

from picarx_interfaces.topics import CMD_VEL

# ROS 2 remapping syntax: --ros-args -r /from:=/to
# teleop_twist_keyboard publishes to /cmd_vel by default.
# We remap it to our canonical CMD_VEL constant (which is also /cmd_vel,
# but now it's driven by the constant — if you ever rename it, only
# topics.py needs to change).
def main():
    ros_args = ["--ros-args", "-r", f"/cmd_vel:={CMD_VEL}"]
    cmd = ["ros2", "run", "teleop_twist_keyboard", "teleop_twist_keyboard"] + ros_args
    os.execvp("ros2", cmd)

if __name__ == "__main__":
    main()