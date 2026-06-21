#!/usr/bin/env python3
import sys
# Force inject the system package path where hailo_platform lives before ROS isolates it
sys.path.append('/usr/lib/python3/dist-packages')

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
import cv2
import numpy as np

# PyHailoRT imports
from hailo_platform import (HEF, VDevice, HailoStreamInterface, InferVStreams, 
                            ConfigureParams, InputVStreamParams, OutputVStreamParams, FormatType)

from picarx_interfaces.nodes import DETECTION_NODE
from picarx_interfaces.topics import (
    CAMERA_IMAGE_RAW,
    DETECTIONS,
)

HEF_PATH = '/usr/local/hailo/resources/models/hailo8/yolov8m.hef'  # Update this path to your HEF file

class HailoObjectDetectionNode(Node):
    def __init__(self):
        super().__init__(DETECTION_NODE)
        
        # ROS 2 Pub/Sub
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(Image, CAMERA_IMAGE_RAW, self.image_callback, 10)
        self.detection_pub = self.create_publisher(Detection2DArray, DETECTIONS, 10)
        
        # Load Hailo HEF (Ensure you have downloaded a YOLOv8 HEF with NMS included)
        # Using yolov8s as an example (good balance of speed/accuracy for Pi 5)
        self.hef_path = HEF_PATH
        self.target = VDevice()
        self.hef = HEF(self.hef_path)
        
        # Configure the target
        self.configure_params = ConfigureParams.create_from_hef(self.hef, interface=HailoStreamInterface.PCIe)
        self.network_groups = self.target.configure(self.hef, self.configure_params)
        self.network_group = self.network_groups[0]
        self.network_group_params = self.network_group.create_params()
        
        # Setup VStreams (Uint8 for images, Float32 for bounding box outputs)
        self.input_vstreams_params = InputVStreamParams.make(self.network_group, format_type=FormatType.UINT8)
        self.output_vstreams_params = OutputVStreamParams.make(self.network_group, format_type=FormatType.FLOAT32)
        
        # Get expected input shape dynamically (Usually 640x640x3 for YOLO)
        self.input_vstream_info = self.hef.get_input_vstream_infos()[0]
        self.input_shape = self.input_vstream_info.shape 
        
        # Open Infer pipeline & Activate Network
        self.infer_pipeline = InferVStreams(self.network_group, self.input_vstreams_params, self.output_vstreams_params)
        self.infer_pipeline.__enter__()
        self.activated_network = self.network_group.activate(self.network_group_params)
        self.activated_network.__enter__()
        
        self.get_logger().info("Hailo-8 YOLOv8 Node initialized and waiting for /camera/image_raw")

    def image_callback(self, msg):
        # 1. Convert ROS Image to OpenCV Format
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        orig_h, orig_w, _ = cv_image.shape
        
        # 2. Preprocess (Resize to HEF input shape)
        h, w = self.input_shape[1], self.input_shape[2]
        resized_img = cv2.resize(cv_image, (w, h))
        input_data = {self.input_vstream_info.name: np.expand_dims(resized_img, axis=0)}
        
        # 3. Run hardware inference on the Hailo NPU
        infer_results = self.infer_pipeline.infer(input_data)
        
        # 4. Extract BBoxes (Hailo NMS models output a single tensor per frame)
        # Tensor structure: [ymin, xmin, ymax, xmax, confidence_score, class_id]
        output_name = list(infer_results.keys())[0]
        detections = infer_results[output_name][0] 
        
        # 5. Build and Publish the vision_msgs payload
        det_array = Detection2DArray()
        det_array.header = msg.header # Preserve timestamp to sync with ORB-SLAM3 later!
        
        for det in detections:
            ymin, xmin, ymax, xmax, score, class_id = det
            
            # Discard low-confidence garbage
            if score < 0.5: 
                continue
            
            detection = Detection2D()
            detection.header = msg.header
            
            # Map normalized NMS coordinates (0.0 - 1.0) back to original camera resolution
            box_w = (xmax - xmin) * orig_w
            box_h = (ymax - ymin) * orig_h
            center_x = xmin * orig_w + box_w / 2.0
            center_y = ymin * orig_h + box_h / 2.0
            
            detection.bbox.center.position.x = float(center_x)
            detection.bbox.center.position.y = float(center_y)
            detection.bbox.size_x = float(box_w)
            detection.bbox.size_y = float(box_h)
            
            hypothesis = ObjectHypothesisWithPose()
            hypothesis.hypothesis.class_id = str(int(class_id))
            hypothesis.hypothesis.score = float(score)
            detection.results.append(hypothesis)
            
            det_array.detections.append(detection)
            
        self.detection_pub.publish(det_array)

    def destroy_node(self):
        # Gracefully release the NPU to prevent driver lockups
        self.activated_network.__exit__(None, None, None)
        self.infer_pipeline.__exit__(None, None, None)
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = HailoObjectDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()