# Schritt 1: Kamera + ROS2 Basics – MVP Implementierung

Dieser Leitfaden zeigt dir konkret, wie du den ersten Schritt (Kamera + ROS2 basics) in Docker-Containern umsetzt, mit allen nötigen Nodes, Packages und einem klaren Workflow.

## Überblick: Was baust du in diesem Schritt?

Du erstellst eine **Mini-Anwendung**, die:
1. Kamera-Bilder von der PiCar-X CSI-Kamera in ROS2 streamt
2. Die Bilder in RViz visualisiert (Live-Vorschau)
3. Gleichzeitig Kameradaten in eine `rosbag2`-Datei aufzeichnet
4. Den Roboter manuell per Tastatur steuert (während du die Kameraansicht siehst)

**Praktisches Ziel:** Du fährst mit dem PiCar-X durch einen Raum, siehst das Live-Kamerabild in RViz auf deinem Laptop, und zeichnest alles für spätere SLAM-Tests auf.

## Benötigte ROS2 Nodes (eine pro Container)

### 1. `picarx_camera_node` (Python)
**Was er tut:**
- Nutzt `Picamera2` (wie in den SunFounder-Beispielen)
- Captured Frames von der CSI-Kamera
- Publiziert:
  - `/camera/image_raw` (`sensor_msgs/msg/Image`)
  - `/camera/camera_info` (`sensor_msgs/msg/CameraInfo`)

**Warum wichtig:** Alle anderen Nodes (SLAM, Objekterkennung) brauchen diese Bilder.

### 2. `picarx_motor_controller_node` (Python)
**Was er tut:**
- Spricht mit Robot HAT MCU über I2C (Adresse `0x14`)
- Abonniert: `/cmd_vel` (`geometry_msgs/msg/Twist`)
- Wandelt `linear.x` (Geschwindigkeit) und `angular.z` (Drehrate) in:
  - Motor-PWM (vorwärts/rückwärts)
  - Servo-Winkel (lenken)

**Warum wichtig:** Ohne ihn kannst du den Roboter nicht bewegen.

### 3. `teleop_twist_keyboard` (Standard-ROS2-Package)
**Was er tut:**
- Liest Tastatureingaben (W/A/S/D/X)
- Publiziert: `/cmd_vel` (`geometry_msgs/msg/Twist`)

**Warum wichtig:** Du kannst den Roboter manuell fahren, während die Kamera aufzeichnet.

### 4. `rviz2` (Visualisierung, läuft auf deinem Laptop)
**Was er tut:**
- Zeigt Live-Kamerabild
- Später: Zeigt SLAM-Karte, Roboterpose, etc.

**Warum wichtig:** Du siehst, was der Roboter sieht, ohne Display am Roboter.

## Benötigte ROS2 Packages

### Im Docker-Image installieren:
# ROS2 Rolling base packages
ros-rolling-ros-base

# Kamera & Bild-Tools
ros-rolling-image-transport
ros-rolling-image-transport-plugins
ros-rolling-cv-bridge
python3-opencv
python3-picamera2

# Teleop (Tastatur-Steuerung)
ros-rolling-teleop-twist-keyboard

# rosbag2 (Aufzeichnung)
ros-rolling-rosbag2

# RViz (auf Laptop, nicht im Container)
ros-rolling-rviz2

# Python-Bibliotheken für Robot HAT
# (robot-hat, picar-x bereits auf dem Pi installiert)

### Auf dem Laptop (zum Visualisieren):
sudo apt install ros-rolling-desktop

## Docker-Setup: Ein Image, fünf Container

### Dockerfile (einmal bauen)

FROM ros:rolling

# System dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-opencv \
    python3-picamera2 \
    git \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

# ROS2 packages
RUN apt-get update && apt-get install -y \
    ros-rolling-image-transport \
    ros-rolling-image-transport-plugins \
    ros-rolling-cv-bridge \
    ros-rolling-teleop-twist-keyboard \
    ros-rolling-rosbag2 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (robot-hat wird als Volume gemountet)
RUN pip3 install --break-system-packages \
    smbus2 \
    adafruit-pca9685 \
    rpi-ws281x

# Workspace setup
RUN mkdir -p /ws/src
WORKDIR /ws

# Entry point
RUN echo 'source /opt/ros/rolling/setup.bash' >> ~/.bashrc
CMD ["bash"]

**Bauen:**
docker build -t picarx-ros:rolling .

### docker-compose.yml

services:
  camera:
    image: picarx-ros:rolling
    network_mode: host
    ipc: host
    privileged: true
    working_dir: /ws
    volumes:
      - ./ws:/ws
      - ~/robot-hat:/robot-hat:ro
      - ~/picar-x:/picar-x:ro
    environment:
      - ROS_DOMAIN_ID=0
      - PYTHONPATH=/robot-hat:/picar-x:$PYTHONPATH
    command: >
      bash -c "source /opt/ros/rolling/setup.bash &&
               cd /ws &&
               colcon build --packages-select picarx_camera &&
               source install/setup.bash &&
               ros2 run picarx_camera camera_node"

  motor:
    image: picarx-ros:rolling
    network_mode: host
    privileged: true
    working_dir: /ws
    volumes:
      - ./ws:/ws
      - ~/robot-hat:/robot-hat:ro
      - ~/picar-x:/picar-x:ro
    environment:
      - ROS_DOMAIN_ID=0
      - PYTHONPATH=/robot-hat:/picar-x:$PYTHONPATH
    command: >
      bash -c "source /opt/ros/rolling/setup.bash &&
               cd /ws &&
               colcon build --packages-select picarx_motor &&
               source install/setup.bash &&
               ros2 run picarx_motor motor_controller_node"

  teleop:
    image: picarx-ros:rolling
    network_mode: host
    stdin_open: true
    tty: true
    environment:
      - ROS_DOMAIN_ID=0
    command: >
      bash -c "source /opt/ros/rolling/setup.bash &&
               ros2 run teleop_twist_keyboard teleop_twist_keyboard"

  recorder:
    image: picarx-ros:rolling
    network_mode: host
    working_dir: /ws/bags
    volumes:
      - ./bags:/ws/bags
    environment:
      - ROS_DOMAIN_ID=0
    command: >
      bash -c "source /opt/ros/rolling/setup.bash &&
               ros2 bag record /camera/image_raw /camera/camera_info /cmd_vel"

## ROS2 Package-Struktur

Erstelle im `./ws/src/` Verzeichnis:

ws/
├── src/
│   ├── picarx_camera/
│   │   ├── package.xml
│   │   ├── setup.py
│   │   └── picarx_camera/
│   │       ├── __init__.py
│   │       └── camera_node.py
│   └── picarx_motor/
│       ├── package.xml
│       ├── setup.py
│       └── picarx_motor/
│           ├── __init__.py
│           └── motor_controller_node.py
└── bags/  # rosbag2 recordings landen hier

## Node-Implementierung (Python)

### 1. Camera Node (`ws/src/picarx_camera/picarx_camera/camera_node.py`)

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from picamera2 import Picamera2
import numpy as np

class PiCarXCameraNode(Node):
    def __init__(self):
        super().__init__('picarx_camera_node')
        
        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        
        # CV Bridge (OpenCV <-> ROS Image Konverter)
        self.bridge = CvBridge()
        
        # Picamera2 Setup (wie in SunFounder-Beispielen)
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.camera.configure(config)
        self.camera.start()
        
        # Timer: 30 FPS (alle 33ms ein Frame)
        self.timer = self.create_timer(0.033, self.publish_frame)
        
        self.get_logger().info('Camera node started')

    def publish_frame(self):
        # Capture frame
        frame = self.camera.capture_array()
        
        # Convert to ROS Image message
        msg = self.bridge.cv2_to_imgmsg(frame, encoding="rgb8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera_link"
        
        # Publish
        self.image_pub.publish(msg)
        
        # Camera Info (vereinfacht, später Kalibrierung einfügen)
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

### 2. Motor Controller Node (`ws/src/picarx_motor/picarx_motor/motor_controller_node.py`)

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
sys.path.append('/robot-hat')
sys.path.append('/picar-x')
from picarx import Picarx

class PiCarXMotorNode(Node):
    def __init__(self):
        super().__init__('picarx_motor_node')
        
        # PiCar-X initialisieren
        self.px = Picarx()
        
        # Subscriber für cmd_vel
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        self.get_logger().info('Motor controller node started')

    def cmd_vel_callback(self, msg: Twist):
        # linear.x: Geschwindigkeit (-1.0 bis 1.0)
        # angular.z: Drehrate (-1.0 bis 1.0)
        
        linear = msg.linear.x   # vorwärts/rückwärts
        angular = msg.angular.z # links/rechts
        
        # Skalierung auf PiCar-X Werte
        speed = int(linear * 50)  # max 50 PWM
        angle = int(angular * 30) # max ±30° Lenkwinkel
        
        # An PiCar-X senden
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

### Package-Metadaten (`package.xml` und `setup.py`)

Für beide Packages ähnlich:

**`picarx_camera/package.xml`:**
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>picarx_camera</name>
  <version>0.1.0</version>
  <description>PiCar-X Camera Driver for ROS2</description>
  <maintainer email="dein@email.de">Dein Name</maintainer>
  <license>MIT</license>

  <depend>rclpy</depend>
  <depend>sensor_msgs</depend>
  <depend>cv_bridge</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>

**`picarx_camera/setup.py`:**
from setuptools import setup

package_name = 'picarx_camera'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Dein Name',
    maintainer_email='dein@email.de',
    description='PiCar-X Camera Driver',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_node = picarx_camera.camera_node:main',
        ],
    },
)

(Analog für `picarx_motor`)

## Workflow: So läuft dein MVP

### Schritt 1: Workspace vorbereiten
cd ~/ros2-workspace
mkdir -p ws/src ws/bags
# Erstelle Package-Verzeichnisse und kopiere obigen Code

### Schritt 2: Docker Image bauen
docker build -t picarx-ros:rolling .

### Schritt 3: Alle Container starten
docker compose up

**Was passiert jetzt:**
1. `camera`-Container startet und streamt Bilder auf `/camera/image_raw`
2. `motor`-Container wartet auf `/cmd_vel`-Befehle
3. `teleop`-Container zeigt Tastatur-Steuerung (W=vorwärts, S=rückwärts, A=links, D=rechts, X=stop)
4. `recorder`-Container zeichnet alles in `./bags/` auf

### Schritt 4: RViz auf deinem Laptop starten
# Auf deinem Laptop (im gleichen Netzwerk wie Pi):
export ROS_DOMAIN_ID=0
ros2 run rviz2 rviz2

In RViz:
1. Add → Image → Topic: `/camera/image_raw`
2. Du siehst jetzt Live-Video vom Roboter

### Schritt 5: Roboter fahren
Im `teleop`-Container-Terminal:
- Drücke **W** → Roboter fährt vorwärts
- Drücke **A** → Roboter lenkt links
- Drücke **X** → Roboter stoppt

**Gleichzeitig:**
- Siehst du das Kamerabild in RViz
- Wird alles in `./bags/rosbag2_...` aufgezeichnet

### Schritt 6: Aufnahme stoppen und abspielen
# Stoppe alle Container
docker compose down

# Spiele Recording ab (für Offline-Tests)
docker run --rm --network host -v ./bags:/bags picarx-ros:rolling \
  bash -c "source /opt/ros/rolling/setup.bash && ros2 bag play /bags/rosbag2_DATUM"

Jetzt kannst du in RViz das aufgezeichnete Video nochmal ansehen, ohne den Roboter zu bewegen.

## Soll sich der Roboter selbst bewegen oder manuell?

**Für Schritt 1 (Kamera + ROS2 basics): Manuelle Steuerung**

**Warum:**
- Du lernst das ROS2-Topic-System kennen (`/cmd_vel`, `/camera/image_raw`)
- Du kannst interessante Szenen bewusst anfahren (z.B. Ecken, Türen, Objekte)
- Du vermeidest Kollisionen (der Roboter kennt die Umgebung noch nicht)

**Für Schritt 3-4 (SLAM): Halbautomatisch**
- Manuelle Steuerung, aber mit aufgezeichneten `rosbag2`-Daten wiederholbar
- Später: Autonome Erkundung mit Nav2

## Was du vergessen haben könntest: Troubleshooting

### Problem: Kamera wird nicht gefunden
# Im Container testen:
docker run --rm --privileged -v /dev:/dev picarx-ros:rolling \
  bash -c "libcamera-hello --list-cameras"

### Problem: I2C funktioniert nicht
# Prüfe, ob Robot HAT erreichbar ist:
docker run --rm --privileged -v /dev:/dev picarx-ros:rolling \
  bash -c "i2cdetect -y 1"
# Du solltest 0x14 sehen

### Problem: ROS2-Nodes sehen sich nicht
- Stelle sicher, dass `ROS_DOMAIN_ID=0` überall gleich ist
- Prüfe: `ros2 topic list` zeigt `/camera/image_raw` und `/cmd_vel`

## Konkrete App-Idee: "Indoor Explorer"

**Ziel:** Fahre durch 3 Räume, zeichne Kamera + Bewegung auf, zähle später, wie oft du an derselben Stelle vorbeigefahren bist.

**Erweiterung für nächste Woche:**
- Füge `picarx_odometry_node` hinzu (publiziert `/odom` aus Rad-Encodern)
- Dann kannst du in RViz auch die Roboter-Trajektorie sehen (blaue Linie)

## Zusammenfassung

| Was | Warum | Wo |
|-----|-------|-----|
| **3 Custom Nodes** (camera, motor, odometry) | Steuert PiCar-X Hardware | `ws/src/` |
| **2 Standard-Nodes** (teleop, rosbag2) | Steuerung + Aufzeichnung | Im Docker-Image |
| **1 Visualizer** (RViz) | Live-Video ansehen | Auf deinem Laptop |
| **Docker Compose** | Alle Nodes gleichzeitig starten | `docker-compose.yml` |
| **Manuelles Fahren** | Du steuerst, lernst ROS2 | Tastatur im teleop-Container |

**Nächster Schritt:** Wenn das läuft, fügst du `picarx_odometry_node` hinzu und kannst mit SLAM (RTAB-Map) anfangen.

# Schritt 1: Kamera + ROS2 Basics – MVP Implementierung

Dieser Leitfaden zeigt dir konkret, wie du den ersten Schritt (Kamera + ROS2 basics) in Docker-Containern umsetzt, mit allen nötigen Nodes, Packages und einem klaren Workflow.

## Überblick: Was baust du in diesem Schritt?

Du erstellst eine **Mini-Anwendung**, die:
1. Kamera-Bilder von der PiCar-X CSI-Kamera in ROS2 streamt
2. Die Bilder in RViz visualisiert (Live-Vorschau)
3. Gleichzeitig Kameradaten in eine `rosbag2`-Datei aufzeichnet
4. Den Roboter manuell per Tastatur steuert (während du die Kameraansicht siehst)

**Praktisches Ziel:** Du fährst mit dem PiCar-X durch einen Raum, siehst das Live-Kamerabild in RViz auf deinem Laptop, und zeichnest alles für spätere SLAM-Tests auf.

## Benötigte ROS2 Nodes (eine pro Container)

### 1. `picarx_camera_node` (Python)
**Was er tut:**
- Nutzt `Picamera2` (wie in den SunFounder-Beispielen)
- Captured Frames von der CSI-Kamera
- Publiziert:
  - `/camera/image_raw` (`sensor_msgs/msg/Image`)
  - `/camera/camera_info` (`sensor_msgs/msg/CameraInfo`)

**Warum wichtig:** Alle anderen Nodes (SLAM, Objekterkennung) brauchen diese Bilder.

### 2. `picarx_motor_controller_node` (Python)
**Was er tut:**
- Spricht mit Robot HAT MCU über I2C (Adresse `0x14`)
- Abonniert: `/cmd_vel` (`geometry_msgs/msg/Twist`)
- Wandelt `linear.x` (Geschwindigkeit) und `angular.z` (Drehrate) in:
  - Motor-PWM (vorwärts/rückwärts)
  - Servo-Winkel (lenken)

**Warum wichtig:** Ohne ihn kannst du den Roboter nicht bewegen.

### 3. `teleop_twist_keyboard` (Standard-ROS2-Package)
**Was er tut:**
- Liest Tastatureingaben (W/A/S/D/X)
- Publiziert: `/cmd_vel` (`geometry_msgs/msg/Twist`)

**Warum wichtig:** Du kannst den Roboter manuell fahren, während die Kamera aufzeichnet.

### 4. `rviz2` (Visualisierung, läuft auf deinem Laptop)
**Was er tut:**
- Zeigt Live-Kamerabild
- Später: Zeigt SLAM-Karte, Roboterpose, etc.

**Warum wichtig:** Du siehst, was der Roboter sieht, ohne Display am Roboter.

## Benötigte ROS2 Packages

### Im Docker-Image installieren:
# ROS2 Rolling base packages
ros-rolling-ros-base

# Kamera & Bild-Tools
ros-rolling-image-transport
ros-rolling-image-transport-plugins
ros-rolling-cv-bridge
python3-opencv
python3-picamera2

# Teleop (Tastatur-Steuerung)
ros-rolling-teleop-twist-keyboard

# rosbag2 (Aufzeichnung)
ros-rolling-rosbag2

# RViz (auf Laptop, nicht im Container)
ros-rolling-rviz2

# Python-Bibliotheken für Robot HAT
# (robot-hat, picar-x bereits auf dem Pi installiert)

### Auf dem Laptop (zum Visualisieren):
sudo apt install ros-rolling-desktop

## Docker-Setup: Ein Image, fünf Container

### Dockerfile (einmal bauen)

FROM ros:rolling

# System dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-opencv \
    python3-picamera2 \
    git \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

# ROS2 packages
RUN apt-get update && apt-get install -y \
    ros-rolling-image-transport \
    ros-rolling-image-transport-plugins \
    ros-rolling-cv-bridge \
    ros-rolling-teleop-twist-keyboard \
    ros-rolling-rosbag2 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (robot-hat wird als Volume gemountet)
RUN pip3 install --break-system-packages \
    smbus2 \
    adafruit-pca9685 \
    rpi-ws281x

# Workspace setup
RUN mkdir -p /ws/src
WORKDIR /ws

# Entry point
RUN echo 'source /opt/ros/rolling/setup.bash' >> ~/.bashrc
CMD ["bash"]

**Bauen:**
docker build -t picarx-ros:rolling .

### docker-compose.yml

services:
  camera:
    image: picarx-ros:rolling
    network_mode: host
    ipc: host
    privileged: true
    working_dir: /ws
    volumes:
      - ./ws:/ws
      - ~/robot-hat:/robot-hat:ro
      - ~/picar-x:/picar-x:ro
    environment:
      - ROS_DOMAIN_ID=0
      - PYTHONPATH=/robot-hat:/picar-x:$PYTHONPATH
    command: >
      bash -c "source /opt/ros/rolling/setup.bash &&
               cd /ws &&
               colcon build --packages-select picarx_camera &&
               source install/setup.bash &&
               ros2 run picarx_camera camera_node"

  motor:
    image: picarx-ros:rolling
    network_mode: host
    privileged: true
    working_dir: /ws
    volumes:
      - ./ws:/ws
      - ~/robot-hat:/robot-hat:ro
      - ~/picar-x:/picar-x:ro
    environment:
      - ROS_DOMAIN_ID=0
      - PYTHONPATH=/robot-hat:/picar-x:$PYTHONPATH
    command: >
      bash -c "source /opt/ros/rolling/setup.bash &&
               cd /ws &&
               colcon build --packages-select picarx_motor &&
               source install/setup.bash &&
               ros2 run picarx_motor motor_controller_node"

  teleop:
    image: picarx-ros:rolling
    network_mode: host
    stdin_open: true
    tty: true
    environment:
      - ROS_DOMAIN_ID=0
    command: >
      bash -c "source /opt/ros/rolling/setup.bash &&
               ros2 run teleop_twist_keyboard teleop_twist_keyboard"

  recorder:
    image: picarx-ros:rolling
    network_mode: host
    working_dir: /ws/bags
    volumes:
      - ./bags:/ws/bags
    environment:
      - ROS_DOMAIN_ID=0
    command: >
      bash -c "source /opt/ros/rolling/setup.bash &&
               ros2 bag record /camera/image_raw /camera/camera_info /cmd_vel"

## ROS2 Package-Struktur

Erstelle im `./ws/src/` Verzeichnis:

ws/
├── src/
│   ├── picarx_camera/
│   │   ├── package.xml
│   │   ├── setup.py
│   │   └── picarx_camera/
│   │       ├── __init__.py
│   │       └── camera_node.py
│   └── picarx_motor/
│       ├── package.xml
│       ├── setup.py
│       └── picarx_motor/
│           ├── __init__.py
│           └── motor_controller_node.py
└── bags/  # rosbag2 recordings landen hier

## Node-Implementierung (Python)

### 1. Camera Node (`ws/src/picarx_camera/picarx_camera/camera_node.py`)

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
from picamera2 import Picamera2
import numpy as np

class PiCarXCameraNode(Node):
    def __init__(self):
        super().__init__('picarx_camera_node')
        
        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)
        
        # CV Bridge (OpenCV <-> ROS Image Konverter)
        self.bridge = CvBridge()
        
        # Picamera2 Setup (wie in SunFounder-Beispielen)
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(
            main={"size": (640, 480), "format": "RGB888"}
        )
        self.camera.configure(config)
        self.camera.start()
        
        # Timer: 30 FPS (alle 33ms ein Frame)
        self.timer = self.create_timer(0.033, self.publish_frame)
        
        self.get_logger().info('Camera node started')

    def publish_frame(self):
        # Capture frame
        frame = self.camera.capture_array()
        
        # Convert to ROS Image message
        msg = self.bridge.cv2_to_imgmsg(frame, encoding="rgb8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera_link"
        
        # Publish
        self.image_pub.publish(msg)
        
        # Camera Info (vereinfacht, später Kalibrierung einfügen)
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

### 2. Motor Controller Node (`ws/src/picarx_motor/picarx_motor/motor_controller_node.py`)

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
sys.path.append('/robot-hat')
sys.path.append('/picar-x')
from picarx import Picarx

class PiCarXMotorNode(Node):
    def __init__(self):
        super().__init__('picarx_motor_node')
        
        # PiCar-X initialisieren
        self.px = Picarx()
        
        # Subscriber für cmd_vel
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        self.get_logger().info('Motor controller node started')

    def cmd_vel_callback(self, msg: Twist):
        # linear.x: Geschwindigkeit (-1.0 bis 1.0)
        # angular.z: Drehrate (-1.0 bis 1.0)
        
        linear = msg.linear.x   # vorwärts/rückwärts
        angular = msg.angular.z # links/rechts
        
        # Skalierung auf PiCar-X Werte
        speed = int(linear * 50)  # max 50 PWM
        angle = int(angular * 30) # max ±30° Lenkwinkel
        
        # An PiCar-X senden
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

### Package-Metadaten (`package.xml` und `setup.py`)

Für beide Packages ähnlich:

**`picarx_camera/package.xml`:**
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>picarx_camera</name>
  <version>0.1.0</version>
  <description>PiCar-X Camera Driver for ROS2</description>
  <maintainer email="dein@email.de">Dein Name</maintainer>
  <license>MIT</license>

  <depend>rclpy</depend>
  <depend>sensor_msgs</depend>
  <depend>cv_bridge</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>

**`picarx_camera/setup.py`:**
from setuptools import setup

package_name = 'picarx_camera'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Dein Name',
    maintainer_email='dein@email.de',
    description='PiCar-X Camera Driver',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_node = picarx_camera.camera_node:main',
        ],
    },
)

(Analog für `picarx_motor`)

## Workflow: So läuft dein MVP

### Schritt 1: Workspace vorbereiten
cd ~/ros2-workspace
mkdir -p ws/src ws/bags
# Erstelle Package-Verzeichnisse und kopiere obigen Code

### Schritt 2: Docker Image bauen
docker build -t picarx-ros:rolling .

### Schritt 3: Alle Container starten
docker compose up

**Was passiert jetzt:**
1. `camera`-Container startet und streamt Bilder auf `/camera/image_raw`
2. `motor`-Container wartet auf `/cmd_vel`-Befehle
3. `teleop`-Container zeigt Tastatur-Steuerung (W=vorwärts, S=rückwärts, A=links, D=rechts, X=stop)
4. `recorder`-Container zeichnet alles in `./bags/` auf

### Schritt 4: RViz auf deinem Laptop starten
# Auf deinem Laptop (im gleichen Netzwerk wie Pi):
export ROS_DOMAIN_ID=0
ros2 run rviz2 rviz2

In RViz:
1. Add → Image → Topic: `/camera/image_raw`
2. Du siehst jetzt Live-Video vom Roboter

### Schritt 5: Roboter fahren
Im `teleop`-Container-Terminal:
- Drücke **W** → Roboter fährt vorwärts
- Drücke **A** → Roboter lenkt links
- Drücke **X** → Roboter stoppt

**Gleichzeitig:**
- Siehst du das Kamerabild in RViz
- Wird alles in `./bags/rosbag2_...` aufgezeichnet

### Schritt 6: Aufnahme stoppen und abspielen
# Stoppe alle Container
docker compose down

# Spiele Recording ab (für Offline-Tests)
docker run --rm --network host -v ./bags:/bags picarx-ros:rolling \
  bash -c "source /opt/ros/rolling/setup.bash && ros2 bag play /bags/rosbag2_DATUM"

Jetzt kannst du in RViz das aufgezeichnete Video nochmal ansehen, ohne den Roboter zu bewegen.

## Soll sich der Roboter selbst bewegen oder manuell?

**Für Schritt 1 (Kamera + ROS2 basics): Manuelle Steuerung**

**Warum:**
- Du lernst das ROS2-Topic-System kennen (`/cmd_vel`, `/camera/image_raw`)
- Du kannst interessante Szenen bewusst anfahren (z.B. Ecken, Türen, Objekte)
- Du vermeidest Kollisionen (der Roboter kennt die Umgebung noch nicht)

**Für Schritt 3-4 (SLAM): Halbautomatisch**
- Manuelle Steuerung, aber mit aufgezeichneten `rosbag2`-Daten wiederholbar
- Später: Autonome Erkundung mit Nav2

## Was du vergessen haben könntest: Troubleshooting

### Problem: Kamera wird nicht gefunden
# Im Container testen:
docker run --rm --privileged -v /dev:/dev picarx-ros:rolling \
  bash -c "libcamera-hello --list-cameras"

### Problem: I2C funktioniert nicht
# Prüfe, ob Robot HAT erreichbar ist:
docker run --rm --privileged -v /dev:/dev picarx-ros:rolling \
  bash -c "i2cdetect -y 1"
# Du solltest 0x14 sehen

### Problem: ROS2-Nodes sehen sich nicht
- Stelle sicher, dass `ROS_DOMAIN_ID=0` überall gleich ist
- Prüfe: `ros2 topic list` zeigt `/camera/image_raw` und `/cmd_vel`

## Konkrete App-Idee: "Indoor Explorer"

**Ziel:** Fahre durch 3 Räume, zeichne Kamera + Bewegung auf, zähle später, wie oft du an derselben Stelle vorbeigefahren bist.

**Erweiterung für nächste Woche:**
- Füge `picarx_odometry_node` hinzu (publiziert `/odom` aus Rad-Encodern)
- Dann kannst du in RViz auch die Roboter-Trajektorie sehen (blaue Linie)

## Zusammenfassung

| Was | Warum | Wo |
|-----|-------|-----|
| **3 Custom Nodes** (camera, motor, odometry) | Steuert PiCar-X Hardware | `ws/src/` |
| **2 Standard-Nodes** (teleop, rosbag2) | Steuerung + Aufzeichnung | Im Docker-Image |
| **1 Visualizer** (RViz) | Live-Video ansehen | Auf deinem Laptop |
| **Docker Compose** | Alle Nodes gleichzeitig starten | `docker-compose.yml` |
| **Manuelles Fahren** | Du steuerst, lernst ROS2 | Tastatur im teleop-Container |

**Nächster Schritt:** Wenn das läuft, fügst du `picarx_odometry_node` hinzu und kannst mit SLAM (RTAB-Map) anfangen.