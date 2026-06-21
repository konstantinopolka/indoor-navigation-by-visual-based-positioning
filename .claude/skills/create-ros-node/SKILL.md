# Create a new ROS node in the picarx project

Use this skill when adding a new ROS 2 Python node to the PiCar-X project. It covers every
file you need to create or modify — the package scaffolding, the node implementation, the
shared interface constants, the launch file, and the Makefile.

## Placeholder conventions

Throughout this skill, use these placeholders and replace them consistently:

| Placeholder | Meaning | Example |
|---|---|---|
| `<PackageName>` | Package/directory name (snake_case) | `picarx_lidar` |
| `<node_name>` | Node name (snake_case) — **must match `<PackageName>`** | `picarx_lidar` |
| `<NodeName>` | Python class name (PascalCase) | `PiCarXLidarNode` |
| `<NODE_CONSTANT>` | UPPER_SNAKE_CASE constant in `nodes.py` | `LIDAR_NODE` |
| `<executable_name>` | CLI entry-point name (snake_case) | `lidar_node` |
| `<TopicName>` | Topic constant names in `topics.py` | `LIDAR_SCAN` |

**Naming rules:**
- `<PackageName>` **must** equal `<node_name>` — the package directory and the Python
  package inside it share the same snake_case name (e.g. `picarx_camera` /
  `picarx_camera/camera_node.py`).
- `<executable_name>` is usually `<node_name>` with `picarx_` stripped and `_node`
  appended (e.g. `picarx_camera` → `camera_node`).
- `<NODE_CONSTANT>` is the executable name in UPPER_SNAKE_CASE (e.g. `camera_node` →
  `CAMERA_NODE`).

---

## Step 1 — Create the package directory tree

Create the following structure under `ws/src/<node_name>/`:

```
<node_name>/
├── <node_name>/
│   ├── __init__.py          # empty
│   └── <node_name>.py       # the node implementation
├── resource/
│   └── <node_name>          # empty marker file for ament_index
├── test/
│   └── test_<node_name>.py  # pytest tests
├── setup.py
├── setup.cfg
├── package.xml
└── README.md
```

- `__init__.py` and `resource/<node_name>` are **empty files** (0 bytes).
- Create them with `touch`.

---

## Step 2 — Write `package.xml`

Use `package format="3"`. Include the XML model declaration. Depend on `rclpy` and
`picarx_interfaces`, plus any ROS 2 message packages your node needs (e.g.
`sensor_msgs`, `geometry_msgs`, `std_msgs`). Always include the standard four test
depends:

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd"
            schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name><node_name></name>
  <version>0.1.0</version>
  <description>TODO: brief description of what this node does</description>
  <maintainer email="todo@todo.com">todo</maintainer>
  <license>MIT</license>

  <depend>rclpy</depend>
  <!-- Add other ROS message packages your node needs, e.g.: -->
  <!-- <depend>sensor_msgs</depend> -->
  <!-- <depend>geometry_msgs</depend> -->
  <exec_depend>picarx_interfaces</exec_depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

---

## Step 3 — Write `setup.cfg`

```ini
[develop]
script_dir=$base/lib/<node_name>
[install]
install_scripts=$base/lib/<node_name>
```

---

## Step 4 — Write `setup.py`

Follow the standard four-part formula used by all project packages:

```python
from setuptools import setup

package_name = '<node_name>'

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
    maintainer='todo',
    maintainer_email='todo@todo.com',
    description='TODO: brief description',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            '<executable_name> = <node_name>.<node_name>:main',
        ],
    },
)
```

**Important:** the entry-point maps `<executable_name>` (what you type after `ros2 run
<node_name> ...`) to `package.module:function`. The module file and the function name
must match what you write in the node implementation (Step 5).

---

## Step 5 — Write the node implementation (`<node_name>/<node_name>.py`)

Every node in this project follows a consistent pattern. Use this template:

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node

# Import topic and node name constants from the shared interfaces package
from picarx_interfaces.topics import TOPIC_ONE, TOPIC_TWO
# If your node publishes/subscribes to ROS message types, import them:
# from sensor_msgs.msg import Image
# from geometry_msgs.msg import Twist

class <NodeName>(Node):
    """TODO: docstring describing what this node does."""

    def __init__(self):
        super().__init__('<NODE_CONSTANT>')

        # --- Publishers ---
        # self.publisher = self.create_publisher(MsgType, TOPIC_NAME, 10)

        # --- Subscribers ---
        # self.subscription = self.create_subscription(
        #     MsgType, TOPIC_NAME, self.callback, 10)

        # --- Timers ---
        # self.timer = self.create_timer(0.033, self.timer_callback)

        self.get_logger().info('<NodeName> started')

    # --- Callbacks ---
    # def callback(self, msg):
    #     ...

    # --- Timer handlers ---
    # def timer_callback(self):
    #     ...

    def destroy_node(self):
        """Clean up resources before shutdown."""
        # Release hardware, stop timers, etc.
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = <NodeName>()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**Rules to follow:**
- The ROS node name passed to `super().__init__()` must match the constant defined in
  `picarx_interfaces/nodes.py` (Step 6).
- All topic strings must come from `picarx_interfaces/topics.py` — never hardcode a
  topic name as a string literal.
- Override `destroy_node()` for any cleanup (stopping hardware, closing files, etc.).
  Always call `super().destroy_node()` at the end.
- Use `self.get_logger().info()` (or `.warn()` / `.error()`) for logging — never
  `print()`.

---

## Step 6 — Register node and topic constants in `picarx_interfaces`

### 6a. `ws/src/picarx_interfaces/picarx_interfaces/nodes.py`

Add a constant for the new node's ROS node name:

```python
<NODE_CONSTANT> = "<node_name>_node"
```

The value is the string passed to `super().__init__()` inside the node class. By
convention it is `<node_name>_node` (e.g. `picarx_camera_node`, `picarx_motor_node`).

### 6b. `ws/src/picarx_interfaces/picarx_interfaces/topics.py`

Add constants for every topic the node publishes or subscribes to. Group them under a
comment header:

```python
# <NodeName> topics
<TOPIC_NAME_1> = "/<topic_path_1>"
<TOPIC_NAME_2> = "/<topic_path_2>"
```

---

## Step 7 — Update the launch file

Edit `ws/src/picarx_bringup/launch/mvp_launch.py`:

### 7a. Import the new constants

Add imports at the top of the file alongside the existing ones:

```python
from picarx_interfaces.nodes import <NODE_CONSTANT>
from picarx_interfaces.topics import <TOPIC_NAME_1>, <TOPIC_NAME_2>
```

### 7b. Add a `Node` action

Inside `generate_launch_description()`, define the node:

```python
    <node_name>_node = Node(
        package='<node_name>',
        executable='<executable_name>',
        name=<NODE_CONSTANT>,
        output='screen',
        # Uncomment to load parameters:
        # parameters=[params_file],
    )
```

The `executable` field must match the console_scripts entry-point key from `setup.py`
(Step 4).

### 7c. Add a shutdown event handler

Register a handler so the whole launch system shuts down if this node exits:

```python
    shutdown_on_<node_name>_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=<node_name>_node,
            on_exit=[
                LogInfo(msg='<NodeName> exited. Shutting down launch.'),
                EmitEvent(event=Shutdown(reason='<node_name> exited')),
            ],
        )
    )
```

### 7d. Add both to the `LaunchDescription` return list

```python
    return LaunchDescription([
        # ... existing items ...
        <node_name>_node,
        shutdown_on_<node_name>_exit,
    ])
```

### 7e. If the node publishes new topics, add them to the recorder

In the `recorder_node` definition, add the new topic constant(s) to the `cmd` list so
rosbag2 captures them:

```python
    recorder_node = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '-o', bag_output,
            # ... existing topics ...
            <NEW_TOPIC_NAME>,
        ],
        # ...
    )
```

---

## Step 8 — Add parameters (optional)

If your node needs configurable parameters, add them to
`ws/src/picarx_bringup/config/params.yaml` under the node's ROS name:

```yaml
# Parameters for the <NodeName>
<node_name>_node:
  ros__parameters:
    param_one: 42
    param_two: "default_value"
```

Then read them in the node's `__init__` with:

```python
self.declare_parameter('param_one', 42)
value = self.get_parameter('param_one').get_parameter_value().integer_value
```

Uncomment `parameters=[params_file]` in the `Node(...)` action (Step 7b) to wire it in.

---

## Step 9 — Update the Makefile

Add a new section to the root `Makefile` following the existing 4-target pattern
(`.build`, `.run`, `.stop`, `.clean`):

```makefile
###############################################################################
# <NODE_NAME> SECTION
###############################################################################

<node_name>.build:
	@echo "[<NODE_NAME_UPPER>] Building <node_name>..."
	cd $(WS_DIR) && \
		source $(HOME)/ros2_jazzy/install/setup.bash && \
		colcon build --symlink-install --packages-select <node_name>

<node_name>.run:
	@echo "[<NODE_NAME_UPPER>] Starting <executable_name>..."
	@mkdir -p $(PID_DIR)
	@$(SHELL) -c "$(SETUP) && ros2 run <node_name> <executable_name> & echo $$! > $(<NODE_NAME_UPPER>_PID)"
	@echo "[<NODE_NAME_UPPER>] PID stored in $(<NODE_NAME_UPPER>_PID)"

<node_name>.stop:
	@echo "[<NODE_NAME_UPPER>] Stopping <executable_name> (if running)..."
	@if [ -f $(<NODE_NAME_UPPER>_PID) ]; then \
		PID=$$(cat $(<NODE_NAME_UPPER>_PID)); \
		echo "[<NODE_NAME_UPPER>] Killing PID $$PID"; \
		kill $$PID 2>/dev/null || true; \
		rm -f $(<NODE_NAME_UPPER>_PID); \
	else \
		echo "[<NODE_NAME_UPPER>] No PID file, nothing to stop."; \
	fi

<node_name>.clean:
	@echo "[<NODE_NAME_UPPER>] Cleaning <node_name> from build/install..."
	rm -rf build/<node_name> install/<node_name>
```

Also:

1. Add `<NODE_NAME_UPPER>_PID := $(PID_DIR)/<node_name>.pid` in the PID variables
   block at the top of the Makefile.
2. Add `<node_name>.build <node_name>.run <node_name>.stop <node_name>.clean` to the
   `.PHONY` declaration.
3. Add `--packages-select <node_name>` to the `all.build` target's `colcon build`
   command so it builds alongside the rest.
4. Add `$(MAKE) <node_name>.stop` to the `all.stop` target.

**Important:** `<NODE_NAME_UPPER>` is the snake_case name converted to UPPER_SNAKE_CASE
(e.g. `picarx_lidar` → `PICARX_LIDAR`).

---

## Step 10 — Build and verify

After creating all files and editing all existing files, build and test:

```bash
# 1. Build the interfaces first (the new node depends on them)
make all.build

# 2. Run just the new node to verify it starts cleanly
source ~/ros2_jazzy/install/setup.bash && source ws/install/setup.bash
ros2 run <node_name> <executable_name>

# 3. Run the full system to verify launch integration
make all.run
```

---

## Quick reference: files you touch

| Action | File |
|---|---|
| **Create** | `ws/src/<node_name>/setup.py` |
| **Create** | `ws/src/<node_name>/setup.cfg` |
| **Create** | `ws/src/<node_name>/package.xml` |
| **Create** | `ws/src/<node_name>/resource/<node_name>` (empty) |
| **Create** | `ws/src/<node_name>/<node_name>/__init__.py` (empty) |
| **Create** | `ws/src/<node_name>/<node_name>/<node_name>.py` |
| **Create** | `ws/src/<node_name>/test/test_<node_name>.py` |
| **Create** | `ws/src/<node_name>/README.md` |
| **Edit** | `ws/src/picarx_interfaces/picarx_interfaces/nodes.py` |
| **Edit** | `ws/src/picarx_interfaces/picarx_interfaces/topics.py` |
| **Edit** | `ws/src/picarx_bringup/launch/mvp_launch.py` |
| **Edit** | `ws/src/picarx_bringup/config/params.yaml` (if using params) |
| **Edit** | `Makefile` (root) |
