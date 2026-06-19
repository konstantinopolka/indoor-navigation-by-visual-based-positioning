# ws/src/picarx_bringup/launch/mvp_launch.py

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from datetime import datetime

bag_output = 'bags/mvp_bag_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def generate_launch_description():
    start_recorder = LaunchConfiguration('start_recorder')

    camera_node = Node(
        package='picarx_camera',
        executable='camera_node',
        name='picarx_camera_node',
        output='screen',
    )

    motor_node = Node(
        package='picarx_motor',
        executable='motor_controller_node',
        name='picarx_motor_node',
        output='screen',
    )

    # Note that it has more arguments than the command in Makefile because we want to record more topics for better debugging and analysis.
    recorder_node = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-o', bag_output,
            '/camera/image_raw',
            '/camera/camera_info',
            '/cmd_vel',
            '/pose_orb1',
            '/pose_orb2',
            '/odom',
            '/tracked_mappoints',
            '/tracking_image',
        ],
        output='screen',
        condition=IfCondition(start_recorder),
    )
    
    monocular_slam_node = Node(
        package='orbslam3_pose',
        executable='mono',
        name='orbslam3_mono_node',
        output='screen',
        arguments=[
            'ws/src/orb_slam3_ros2_mono_publisher/vocabulary/ORBvoc.txt',
            'ws/src/orb_slam3_ros2_mono_publisher/config/monocular/calib.yaml',
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

    return LaunchDescription([
        DeclareLaunchArgument(
            'start_recorder',
            default_value='true',
            description='Start rosbag2 recording.',
        ),
        camera_node,
        motor_node,
        recorder_node,
        monocular_slam_node,
        shutdown_on_camera_exit,
        shutdown_on_motor_exit,
        shutdown_on_recorder_exit,
        shutdown_on_slam_exit,
    ])