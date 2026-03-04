import os
# os.getlogin() fails in Docker (no TTY) — patch it to use env var instead
_orig_getlogin = os.getlogin
def _safe_getlogin():
    try:
        return _orig_getlogin()
    except OSError:
        return os.environ.get('USER', os.environ.get('LOGNAME', 'root'))
os.getlogin = _safe_getlogin


from setuptools import setup

package_name = 'picarx_motor'

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
    description='PiCar-X Motor Controller for ROS2',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_controller_node = picarx_motor.motor_controller_node:main',
        ],
    },
)
