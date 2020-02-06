import numpy as np
import os
import time

from datetime import datetime

from dispertech.models.cameras.basler import Camera
from dispertech.models.electronics.arduino import ArduinoModel
from experimentor.models.cameras.exceptions import CameraTimeout
from experimentor.models.decorators import make_async_thread
from experimentor.models.experiments.base_experiment import Experiment


class CalibrationSetup(Experiment):
    def __init__(self, filename=None):
        super(CalibrationSetup, self).__init__(filename=filename)

        self.cameras = {
            'camera_microscope': None,
            'camera_fiber': None,
        }

        self.electronics = {
            'arduino': None,
            'servo': None,
        }

    def initialize_cameras(self):
        """Assume a specific setup working with baslers and initialize both cameras"""
        self.logger.info('Initializing cameras')
        config_mic = self.config['camera_microscope']
        self.cameras['camera_microscope'] = Camera(config_mic['init'])

        config_fiber = self.config['camera_fiber']
        self.cameras['camera_fiber'] = Camera(config_fiber['init'])

        for cam in self.cameras:
            self.logger.info(f'Initializing {cam}')
            self.cameras[cam].initialize()
            self.logger.debug(f'Configuring {cam} with {self.config[cam]}')
            self.cameras[cam].config(self.config[cam])

    def initialize_electronics(self):
        """Assumes there are two arduinos connected, one to control a Servo and another to control the rest.
        TODO:: This will change in the future, when electronics are made on a single board.
        """

        self.electronics['arduino'] = ArduinoModel(**self.config['arduino'])
        self.electronics['servo'] = ArduinoModel(**self.config['servo'])

        self.logger.info('Initializing electronics arduino')
        self.electronics['arduino'].initialize()
        self.logger.info('Initializing electronics servo')
        self.electronics['servo'].initialize()

    def servo_on(self):
        """Moves the servo to the ON position."""
        self.logger.info('Setting servo ON')
        self.electronics['servo'].move_servo(1)
        self.config['servo']['status'] = 1

    def servo_off(self):
        """Moves the servo to the OFF position."""
        self.logger.info('Setting servo OFF')
        self.electronics['servo'].move_servo(0)
        self.config['servo']['status'] = 0

    def set_laser_power(self, power: int):
        """ Sets the laser power, taking into account closing the shutter if the power is 0
        """
        self.logger.info(f'Setting laser power to {power}')
        power = int(power)
        if power == 0:
            self.servo_off()
        else:
            self.servo_on()

        self.electronics['arduino'].laser_power(power)
        self.config['laser']['power'] = power

    @make_async_thread
    def move_mirror(self, direction: int, axis: int):
        """ Moves the mirror connected to the board

        :param int speed: Speed, from 0 to 2^6.
        :param direction: 0 or 1, depending on which direction to move the mirror
        :param axis: 1 or 2, to select the axis
        """
        speed = self.config['mirror']['speed']
        self.electronics['arduino'].move_mirror(direction, speed, axis)

    def start_free_run(self, camera: str):
        """Starts the free run of the given camera, this has nothing to do with data acquisition or saving.

        :param str camera: must be the same as specified in the config file, for instance 'camera_microscope'
        """
        self.logger.info(f'Starting free run of {camera}')
        self.cameras[camera].config(self.config[camera])
        self.cameras[camera].start_free_run()
        self.logger.debug(f'Started free run of {camera} with {self.config[camera]}')

    def stop_free_run(self, camera: str):
        """ Stops the free run of the camera.

        :param str camera: must be the same as specified in the config file, for example 'camera_microscope'
        """
        self.logger.info(f'Stopping the free run of {camera}')
        self.cameras[camera].stop_free_run()

    def save_fiber_data(self):
        """Saves the fiber core data using the information available in the config (filename, folder, cartridge).
        """
        base_folder = self.config['info']['folder']
        today_folder = f'{datetime.today():%Y-%m-%d}'
        folder = os.path.join(base_folder, today_folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)

        i = 0
        cartridge_number = self.config['info']['cartridge_number']
        base_filename = self.config['info']['filename_fiber']
        while os.path.isfile(os.path.join(folder, base_filename.format(
                cartrdige_number=cartridge_number,
                i=i))):
            i += 1

        filename = os.path.join(folder, base_filename.format(cartridge_number=cartridge_number, i=i))

        t0 = time.time()
        temp_image = self.cameras['camera_fiber'].temp_image
        while temp_image is None:
            temp_image = self.cameras['camera_fiber'].temp_image
            if time.time() - t0 > 10:
                raise CameraTimeout("It took too long to get a new frame for saving the fiber data")
        np.save(filename, temp_image)
        self.logger.info(f'Saved fiber data to {filename}')

    def save
