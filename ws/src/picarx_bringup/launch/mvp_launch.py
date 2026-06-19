# ws/src/picarx_bringup/launch/mvp_launch.py

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.eventhandlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


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

    recorder_node = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-o', 'bags/mvp_bag',
            '/camera/image_raw',
            '/camera/camera_info',
            '/cmd_vel',
        ],
        output='screen',
        condition=IfCondition(start_recorder),
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

    return LaunchDescription([
        DeclareLaunchArgument(
            'start_recorder',
            default_value='true',
            description='Start rosbag2 recording.',
        ),
        camera_node,
        motor_node,
        recorder_node,
        shutdown_on_camera_exit,
        shutdown_on_motor_exit,
        shutdown_on_recorder_exit,
    ])