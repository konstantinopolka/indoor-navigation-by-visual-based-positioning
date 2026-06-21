# ws/src/picarx_bringup/launch/mvp_launch.py

# standard library
import os

# third-party
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from datetime import datetime

# first-party
from picarx_interfaces.topics import (
    CAMERA_IMAGE_RAW, CAMERA_INFO, CMD_VEL,
    POSE_ORB1, POSE_ORB2, ODOM,
    TRACKED_MAPPOINTS, TRACKING_IMAGE, ALL_MAPPOINTS,
    DETECTIONS,
)
from picarx_interfaces.nodes import CAMERA_NODE, MOTOR_NODE, SLAM_NODE, DETECTION_NODE

bag_output = 'bags/mvp_bag_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

# Resolve the path to the params.yaml file installed by picarx_bringup
params_file = os.path.join(
    get_package_share_directory('picarx_bringup'),
    'config', 'params.yaml'
)

# global definitions 
VOCAB_FILE = 'ws/src/orb_slam3_ros2_mono_publisher/vocabulary/ORBvoc.txt'
CALIB_FILE = 'ws/src/orb_slam3_ros2_mono_publisher/config/monocular/calib.yaml'

def generate_launch_description():
    start_recorder = LaunchConfiguration('start_recorder')

    camera_node = Node(
        package='picarx_camera',
        executable='camera_node',
        name=CAMERA_NODE,
        output='screen',
        # parameters=[params_file]
    )

    motor_node = Node(
        package='picarx_motor',
        executable='motor_controller_node',
        name=MOTOR_NODE,
        output='screen',
        # parameters=[params_file]
    )

    detection_node = Node(
        package='hailo_object_detection',
        executable='detector_node',
        name=DETECTION_NODE,
        output='screen',
    )

    # Note that it has more arguments than the command in Makefile because we want to record more topics for better debugging and analysis.
    recorder_node = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-o', bag_output,
            CAMERA_IMAGE_RAW,
            CAMERA_INFO,
            CMD_VEL,
            POSE_ORB1,
            POSE_ORB2,
            ODOM,
            TRACKED_MAPPOINTS,
            TRACKING_IMAGE,
            DETECTIONS,
        ],
        output='screen',
        condition=IfCondition(start_recorder),
    )
    
    monocular_slam_node = Node(
        package='orbslam3_pose',
        executable='mono',
        name=SLAM_NODE,
        output='screen',
        arguments=[
            VOCAB_FILE,
            CALIB_FILE,
        ],
        remappings=[
            ('/camera/image_raw', CAMERA_IMAGE_RAW),
            ('/camera/camera_info', CAMERA_INFO),
            ('/pose_orb1', POSE_ORB1),
            ('/pose_orb2', POSE_ORB2),
            ('/tracked_mappoints', TRACKED_MAPPOINTS),
            ('/tracking_image', TRACKING_IMAGE),
            ('all_mappoints', ALL_MAPPOINTS),
        ],
    )

    shutdown_on_camera_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=camera_node,
            on_exit=[
                LogInfo(msg='Camera node exited. Shutting down launch.'),
                EmitEvent(event=Shutdown(reason='camera node exited')),
            ],
        )
    )

    shutdown_on_motor_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=motor_node,
            on_exit=[
                LogInfo(msg='Motor node exited. Shutting down launch.'),
                EmitEvent(event=Shutdown(reason='motor node exited')),
            ],
        )
    )

    shutdown_on_recorder_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=recorder_node,
            on_exit=[
                LogInfo(msg='Recorder exited. Shutting down launch.'),
                EmitEvent(event=Shutdown(reason='recorder exited')),
            ],
        )
    )
    
    shutdown_on_slam_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=monocular_slam_node,
            on_exit=[
                LogInfo(msg='SLAM node exited. Shutting down launch.'),
                EmitEvent(event=Shutdown(reason='SLAM node exited')),
            ],
        )
    )

    shutdown_on_detection_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=detection_node,
            on_exit=[
                LogInfo(msg='Hailo detection node exited. Shutting down launch.'),
                EmitEvent(event=Shutdown(reason='detection node exited')),
            ],
        )
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'start_recorder',
            default_value='true',
            description='Start rosbag2 recording.',
        ),
        camera_node,
        motor_node,
        detection_node,
        recorder_node,
        monocular_slam_node,
        shutdown_on_camera_exit,
        shutdown_on_motor_exit,
        shutdown_on_recorder_exit,
        shutdown_on_slam_exit,
        shutdown_on_detection_exit,
    ])