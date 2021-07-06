# ##############################################################################
#  Copyright (c) 2021 Aquiles Carattino, Dispertech B.V.                       #
#  experiment.py is part of disperscripts                                      #
#  This file is released under an MIT license.                                 #
#  See LICENSE.md.MD for more information.                                        #
# ##############################################################################


from multiprocessing import Event

import numpy as np
import os
import time
from datetime import datetime
from experimentor.core.signal import Signal
from experimentor.models.action import Action
from experimentor.models.devices.cameras.basler.basler import BaslerCamera as Camera
from experimentor.models.experiments import Experiment

from dispertech.models.electronics.arduino import ArduinoModel
from LightSheet.models.movie_saver import MovieSaver


class LightSheetExperiment(Experiment):
    new_image = Signal()

    def __init__(self, filename=None):
        super(LightSheetExperiment, self).__init__(filename=filename)

        self.background = None
        self.camera_microscope = None
        self.electronics = None

        self.finalized = False
        self.remove_background = False

        self.saving = False
        self.saving_event = Event()
        self.saving_process=None

    @Action
    def initialize(self):
        """ Initialize both cameras and the electronics. Cameras will start with a continuous run and continuous
        acquisition, based on the initial configuration.
        """
        self.initialize_camera()
        self.initialize_electronics()
        self.logger.info('Starting free runs and continuous reads')
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    def initialize_camera(self):
        """Assume a specific setup working with baslers and initialize both cameras"""
        self.logger.info('Initializing camera')
        config_mic = self.config['camera_microscope']
        self.camera_microscope = Camera(config_mic['init'], initial_config=config_mic['config'])
        self.camera_microscope.initialize()

    def initialize_electronics(self):
        """Assumes there are two arduinos connected, one to control a Servo and another to control the rest.
        TODO:: This will change in the future, when electronics are made on a single board.
        """
        self.electronics = ArduinoModel(**self.config['electronics']['arduino'])
        self.logger.info('Initializing electronics arduino')
        self.electronics.initialize()

    def move_mirror(self, direction: int, axis: int):
        """ Moves the mirror connected to the board

        :param direction: 0 or 1, depending on which direction to move the mirror
        :param axis: 1 or 2, to select the axis
        """
        speed = self.config['mirror']['speed']
        self.electronics.move_piezo(speed, direction, axis)

    def get_latest_image(self):
        """ Reads the camera.

        .. todo:: This must be changed since it was inherited from the time when both cameras were stored in a dict
        """
        tmp_image = self.camera_microscope.temp_image
        if self.remove_background:
            if self.background is None:
                self.background = np.empty((tmp_image.shape[0], tmp_image.shape[1], 10), dtype=np.uint16)
            self.background = np.roll(self.background, -1, 2)
            self.background[:, :, -1] = tmp_image
            bkg = np.mean(self.background, 2, dtype=np.uint16)
            # tmp_image = (tmp_image.astype(np.int16) - bkg).clip(0, 2**16-1).astype(np.uint16)
            ttmp_image = tmp_image - bkg
            ttmp_image[bkg>tmp_image] = 0
            tmp_image = ttmp_image
        else:
            self.background = None
        # return (tmp_image/2**4).astype(np.uint8)
        return tmp_image

    def stop_free_run(self):
        """ Stops the free run of the camera.

        :param camera: must be the same as specified in the config file, for example 'camera_microscope'

        .. todo:: This must change, since it was inherited from the time both cameras were stored in a dict
        """
        self.logger.info(f'Stopping the free run')
        self.camera_microscope.stop_free_run()

    def prepare_folder(self) -> str:
        """Creates the folder with the proper date, using the base directory given in the config file"""
        base_folder = self.config['info']['folder']
        today_folder = f'{datetime.today():%Y-%m-%d}'
        folder = os.path.join(base_folder, today_folder)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        return folder

    def get_filename(self, base_filename: str) -> str:
        """Checks if the given filename exists in the given folder and increments a counter until the first non-used
        filename is available.

        :param base_filename: must have two placeholders {cartridge_number} and {i}
        :returns: full path to the file where to save the data
        """
        folder = self.prepare_folder()
        i = 0
        cartridge_number = self.config['info']['cartridge_number']
        while os.path.isfile(os.path.join(folder, base_filename.format(
                cartridge_number=cartridge_number,
                i=i))):
            i += 1

        return os.path.join(folder, base_filename.format(cartridge_number=cartridge_number, i=i))

    def save_image_microscope_camera(self, filename: str) -> None:
        """Saves the image shown on the microscope camera to the given filename.

        :param str filename: Must be a string containing two placeholders: {cartrdige_number}, {i}
        """
        filename = self.get_filename(filename)
        temp_image = self.camera_microscope.temp_image
        np.save(filename, temp_image)
        self.logger.info(f"Saved microscope data to {filename}")

    @Action
    def start_binning(self):
        self.camera_microscope.stop_continuous_reads()
        self.camera_microscope.stop_free_run()
        self.background = None  # This is to prevent shape mismatch between before and after
        self.camera_microscope.binning_y = 4
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    @Action
    def stop_binning(self):
        self.camera_microscope.stop_continuous_reads()
        self.camera_microscope.stop_free_run()
        self.background = None  # This is to prevent shape mismatch between before and after
        self.camera_microscope.binning_y = 1
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    @Action
    def save_particles_image(self):
        """ Saves the image shown on the microscope. This is only to keep as a reference. This method wraps the
        actual method `meth:save_iamge_microscope_camera` in case there is a need to set parameters before saving. Or
        if there are going to be different saving options (for example, low and high laser powers, etc.).
        """
        base_filename = self.config['info']['filename_microscope']
        self.save_image_microscope_camera(base_filename)

    def set_roi(self, y_min, height):
        """ Sets up the ROI of the microscope camera. It assumes the user only crops the vertical direction, since the
        fiber goes all across the image.

        Parameters
        ----------
        y_min : int
            The minimum height in pixels
        height : int
            The total height in pixels
        """
        self.camera_microscope.stop_free_run()
        self.camera_microscope.stop_continuous_reads()
        self.background = None  # This is to prevent shape mismatch between before and after
        current_roi = self.camera_microscope.ROI
        new_roi = (current_roi[0], (y_min, height))
        self.camera_microscope.ROI = new_roi
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    def clear_roi(self):
        self.camera_microscope.stop_continuous_reads()
        self.camera_microscope.stop_free_run()
        self.background = None  # This is to prevent shape mismatch between before and after
        full_roi = (
            (0, self.camera_microscope.ccd_width),
            (0, self.camera_microscope.ccd_height)
        )
        self.camera_microscope.ROI = full_roi
        self.camera_microscope.start_free_run()
        self.camera_microscope.continuous_reads()

    def start_saving_images(self):
        if self.saving:
            self.logger.warning('Saving process still running: self.saving is true')
        if self.saving_process is not None and self.saving_process.is_alive():
            self.logger.warning('Saving process is alive, stop the saving process first')
            return

        self.saving = True
        base_filename = self.config['info']['filename_movie']
        file = self.get_filename(base_filename)
        self.saving_event.clear()
        self.saving_process = MovieSaver(
            file,
            self.config['saving']['max_memory'],
            self.camera_microscope.frame_rate,
            self.saving_event,
            self.camera_microscope.new_image.url,
            topic='new_image',
            metadata=self.camera_microscope.config.all(),
        )

    def stop_saving_images(self):
        self.camera_microscope.new_image.emit('stop')
        # self.emit('new_image', 'stop')

        # self.saving_event.set()
        time.sleep(.05)

        if self.saving_process is not None and self.saving_process.is_alive():
            self.logger.warning('Saving process still alive')
            time.sleep(.1)
        self.saving = False

    def finalize(self):
        if self.finalized:
           return
        self.logger.info('Finalizing calibration experiment')
        if self.saving:
            self.logger.debug('Finalizing the saving images')
            self.stop_saving_images()
        self.saving_event.set()
        self.camera_microscope.keep_reading = False
        if self.camera_microscope is not None:
            self.camera_microscope.finalize()
        super(LightSheetExperiment, self).finalize()
        self.finalized = True
