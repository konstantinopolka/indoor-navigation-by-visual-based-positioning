#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2


class PiCarXCameraNode(Node):
    def __init__(self):
        super().__init__('picarx_camera_node')

        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        self.bridge = CvBridge()

        # Open camera via V4L2 (Video4Linux2) - works in Docker with /dev/video0
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not self.cap.isOpened():
            self.get_logger().error('Cannot open camera /dev/video0')
            raise RuntimeError('Camera not available')

        # Timer: ~30 FPS
        self.timer = self.create_timer(0.033, self.publish_frame)

        self.get_logger().info('Camera node started via V4L2')

    def publish_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn('Failed to capture frame')
            return

        # OpenCV captures in BGR, convert to RGB for ROS
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        msg = self.bridge.cv2_to_imgmsg(frame_rgb, encoding='rgb8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'
        self.image_pub.publish(msg)

        # Camera Info (simplified, add calibration later)
        info_msg = CameraInfo()
        info_msg.header = msg.header
        info_msg.height = 480
        info_msg.width = 640
        self.info_pub.publish(info_msg)

    def destroy_node(self):
        self.cap.release()
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
