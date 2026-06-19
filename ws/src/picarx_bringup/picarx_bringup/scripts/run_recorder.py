#!/usr/bin/env python3
"""
Launcher for rosbag2 recording.
Builds the topic list from picarx_interfaces.topics constants
and calls ros2 bag record.
"""
import os
import sys
from datetime import datetime

from picarx_interfaces.topics import (
    CAMERA_IMAGE_RAW,
    CAMERA_INFO,
    CMD_VEL,
    POSE_ORB1,
    POSE_ORB2,
    ODOM,
    TRACKED_MAPPOINTS,
    TRACKING_IMAGE,
)

# All topics to record — edit this list here if you add/remove topics.
# No topic string is hardcoded anywhere else.
TOPICS_TO_RECORD = [
    CAMERA_IMAGE_RAW,
    CAMERA_INFO,
    CMD_VEL,
    POSE_ORB1,
    POSE_ORB2,
    ODOM,
    TRACKED_MAPPOINTS,
    TRACKING_IMAGE,
]

def main():
    bag_output = "bags/mvp_bag_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    cmd = [
        "ros2",
        "bag",
        "record",
        "-o", 
        bag_output,
        "--topics",
        ] + TOPICS_TO_RECORD
    print(f"[RECORDER] Recording {len(TOPICS_TO_RECORD)} topics → {bag_output}")
    for t in TOPICS_TO_RECORD:
        print(f"           {t}")
    os.execvp("ros2", cmd)

if __name__ == "__main__":
    main()