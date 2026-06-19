import os
from glob import glob
from setuptools import setup

package_name = 'picarx_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name] if os.path.isdir(package_name) else [],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Register launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        # Register config/params files
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='todo',
    maintainer_email='todo@todo.com',
    description='PiCarX Bringup package',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [],
    },
)