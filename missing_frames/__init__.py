import time

import yaml

from experimentor import Q_
from experimentor.lib.log import get_logger,log_to_screen
from experimentor.models.devices.cameras.basler.basler import BaslerCamera


logger = get_logger()
handler = log_to_screen(logger=logger)

with open('../dispertech.yml', 'r') as f:
    camera_config = yaml.load(f, yaml.UnsafeLoader)['camera_microscope']['config']

cam = BaslerCamera('a2', initial_config=camera_config)
future = cam.initialize()
while future.running():
    time.sleep(.1)
cam.exposure = Q_('1ms')
cam.start_free_run()
time.sleep(2)
data = cam.read_camera()
time.sleep(2)
data = cam.read_camera()
time.sleep(5)
data = cam.read_camera()
# cam.continuous_reads()
# time.sleep(5)

# cam.finalize()
