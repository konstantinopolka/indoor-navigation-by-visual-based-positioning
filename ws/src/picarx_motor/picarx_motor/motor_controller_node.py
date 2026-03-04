#!/usr/bin/env python3
import sys
sys.path.insert(0, '/robot-hat')
sys.path.insert(0, '/picar-x')

# Monkey-patch gpiozero's LGPIOFactory to force gpiochip0
# This is required on RPi5 in Docker — gpiozero hardcodes gpiochip4
# which is only a symlink; inside Docker the symlink does not resolve.
# See: https://github.com/gpiozero/gpiozero/issues/1166
import lgpio
import gpiozero.pins.lgpio as _gz_lgpio
from gpiozero import Device

def _patched_lgpio_init(self, chip=None):
    _gz_lgpio.LGPIOFactory.__bases__[0].__init__(self)
    self._handle = lgpio.gpiochip_open(0)   # force chip 0
    self._chip = 0
    self.pin_class = _gz_lgpio.LGPIOPin

_gz_lgpio.LGPIOFactory.__init__ = _patched_lgpio_init
Device.pin_factory = _gz_lgpio.LGPIOFactory()

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
