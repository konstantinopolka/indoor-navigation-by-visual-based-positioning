from setuptools import setup

package_name = 'hailo_object_detection'

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
    maintainer='picarx',
    maintainer_email='sotnik2804@gmail.com',
    description='Hailo-8 YOLOv8 Object Detection node for PiCar-X',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'detector_node = hailo_object_detection.detector_node:main',
        ],
    },
)
