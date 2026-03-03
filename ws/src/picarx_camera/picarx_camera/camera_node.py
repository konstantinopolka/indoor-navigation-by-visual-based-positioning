#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from picamera2 import Picamera2


class PiCarXCameraNode(Node):
    def __init__(self):
        super().__init__('picarx_camera_node')

        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)

        # CV Bridge (OpenCV <-> ROS Image converter)
        self.bridge = CvBridge()

        # Picamera2 Setup
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.camera.configure(config)
        self.camera.start()

        # Timer: ~30 FPS
        self.timer = self.create_timer(0.033, self.publish_frame)

        self.get_logger().info('Camera node started')

    def publish_frame(self):
        # Capture frame
        frame = self.camera.capture_array()

        # Convert to ROS Image message
        msg = self.bridge.cv2_to_imgmsg(frame, encoding='rgb8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'

        # Publish image
        self.image_pub.publish(msg)

        # Camera Info (simplified, add calibration later)
        info_msg = CameraInfo()
        info_msg.header = msg.header
        info_msg.height = 480
        info_msg.width = 640
        self.info_pub.publish(info_msg)

    def destroy_node(self):
        self.camera.stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PiCarXCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
