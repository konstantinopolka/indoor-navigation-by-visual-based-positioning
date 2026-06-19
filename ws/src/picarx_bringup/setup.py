import os
from glob import glob
from setuptools import setup

_orig_getlogin = os.getlogin
def _safe_getlogin():
    try:
        return _orig_getlogin()
    except OSError:
        return os.environ.get('USER', os.environ.get('LOGNAME', 'root'))
os.getlogin = _safe_getlogin

package_name = 'picarx_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=[
        'picarx_bringup',           
        'picarx_bringup.scripts',  
    ],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
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
        'console_scripts': [
            # These become shell commands after building
            'run_teleop = picarx_bringup.scripts.run_teleop:main',
            'run_recorder = picarx_bringup.scripts.run_recorder:main',
        ],
    },
)