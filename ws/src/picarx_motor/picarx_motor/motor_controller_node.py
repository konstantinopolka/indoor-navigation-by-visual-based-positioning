#!/usr/bin/env python3
import sys
sys.path.insert(0, '/robot-hat')
sys.path.insert(0, '/picar-x')

# Force gpiozero to use lgpio with chip 0 BEFORE any robot_hat import
from gpiozero.pins.lgpio import LGPIOFactory
from gpiozero import Device
Device.pin_factory = LGPIOFactory(chip=0)

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from picarx import Picarx

class PiCarXMotorNode(Node):
    def __init__(self):
        super().__init__('picarx_motor_node')

        # Initialize PiCar-X
        self.px = Picarx()

        # Subscriber for cmd_vel
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info('Motor controller node started')

    def cmd_vel_callback(self, msg: Twist):
        linear = msg.linear.x    # forward/backward (-1.0 to 1.0)
        angular = msg.angular.z  # left/right (-1.0 to 1.0)

        # Scale to PiCar-X values
        speed = int(linear * 50)   # max 50 PWM
        angle = int(angular * 30)  # max ±30° steering angle

        # Send to PiCar-X
        self.px.set_dir_servo_angle(angle)
        if linear > 0:
            self.px.forward(abs(speed))
        elif linear < 0:
            self.px.backward(abs(speed))
        else:
            self.px.stop()

        self.get_logger().debug(f'Speed: {speed}, Angle: {angle}')

    def destroy_node(self):
        self.px.stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PiCarXMotorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
