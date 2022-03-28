import os
from datetime import datetime
from multiprocessing import Event

import numpy as np
import copy as copy #m required in Code1dot7for_implementation

from calibration.models.movie_saver import MovieSaver
from experimentor.drivers.digilent import AnalogDiscovery
from experimentor.drivers.digilent.dwfconst import InstrumentState, AnalogAcquisitionFilter, TriggerSource, \
    AnalogInTriggerMode, TriggerCondition
from .arduino import ArduinoModel
from experimentor import Q_
from experimentor.core.signal import Signal
from experimentor.lib.fitgaussian import fitgaussian
from experimentor.models.action import Action
from experimentor.models.devices.cameras.basler.basler import BaslerCamera as Camera
from experimentor.models.devices.cameras.exceptions import CameraTimeout
from experimentor.models.experiments import Experiment
import time

from .digilent import DigilentModel


class FluorescenceMeasurement(Experiment):
    new_image = Signal()

    def __init__(self, filename=None):
        super(FluorescenceMeasurement, self).__init__(filename=filename)

        self.background = None
        self.camera_microscope = None
        self.camera_fiber = None

        self.electronics = None

        self.daq = None

        self.fiber_center_position = None
        self.fiber_radius = 0
        self.laser_center = None
        self.saving = False
        self.saving_event = Event()
        self.finalized = False
        self.saving_process = None
        self.remove_background = False
        self.multiply_array = False #m


    @Action
    def initialize(self):
        """ Initialize both cameras and the electronics. Cameras will start with a continuous run and continuous
        acquisition, based on the initial configuration.
        """
        self.initialize_cameras()
        self.initialize_electronics()
        self.logger.info('Starting free runs and continuous reads')
        self.camera_microscope.start_free_run()
        self.camera_microscope.configure_DIO()
        self.camera_microscope.continuous_reads()
        self.camera_fiber.start_free_run()
        self.camera_fiber.continuous_reads()
        self.initialize_daq()
        self.last_daq = np.zeros((self.config['daq']['buffer']))

    def initialize_cameras(self):
        """Assume a specific setup working with baslers and initialize both cameras"""
        self.logger.info('Initializing cameras')
        config_mic = self.config['camera_microscope']
        self.camera_microscope = Camera(config_mic['init'], initial_config=config_mic['config'])

        config_fiber = self.config['camera_fiber']
        self.camera_fiber = Camera(config_fiber['init'], initial_config=config_fiber['config'])

        for cam in (self.camera_fiber, self.camera_microscope):
            self.logger.info(f'Initializing {cam}')
            cam.initialize()
            self.logger.debug(f'Configuring {cam}')

    def initialize_electronics(self):
        """ Initializes the electronics associated witht he experiment (but not the cameras).

        TODO:: We should be mindful about what happens once the program starts and what happens once the device is
            switched on.
        """

        self.electronics = ArduinoModel(**self.config['electronics']['arduino'])
        self.logger.info('Initializing electronics Arduino')
        self.electronics.initialize()

    def initialize_daq(self):
        """ Initializes the Digilent DAQ Card to acquire the signal from the APD"""
        self.logger.info('Initializing DAQ')
        self.daq = DigilentModel(config=self.config['daq'])
        self.daq.initialize()
        self.daq.reconfigure_daq()

    @Action
    def toggle_top_led(self):
        if self.electronics.top_led == 1:
            self.electronics.top_led = 0
        else:
            self.electronics.top_led = 1

    @Action
    def toggle_fiber_led(self):
        if self.electronics.fiber_led == 0:
            config = self.config['laser_focusing']['high']
            self.electronics.fiber_led = 1
        else:
            config = self.config['laser_focusing']['low']
            self.electronics.fiber_led = 0
        self.camera_fiber.config.update({
            'exposure': Q_(config['exposure_time']),
            'gain': float(config['gain']),
            })
        self.camera_fiber.config.apply_all()

    def set_laser_power_633(self, power: int):
        """ Sets the laser power, taking into account closing the shutter if the power is 0
        """
        self.logger.info(f'Setting 633 laser power to {power}')
        power = int(power)

        self.electronics.scattering_laser = power
        self.config['laser_633']['power'] = power

    def set_laser_power_488(self, power: int):
        """ Sets the laser power, taking into account closing the shutter if the power is 0
        """
        self.logger.info(f'Setting 488 laser power to {power}')
        power = int(power)

        self.electronics.fluorescence_laser = power
        self.config['laser_488']['power'] = power

    def move_piezo(self, direction: int, axis: int):
        """ Moves the mirror connected to the board

        :param direction: 0 or 1, depending on which direction to move the mirror
        :param axis: 1 or 2, to select the axis
        """
        speed = self.config['mirror']['speed']
        self.electronics.move_piezo(speed, direction, axis)

    def get_latest_image(self, camera: str):
        """ Reads the camera.

        .. todo:: This must be changed since it was inherited from the time when both cameras were stored in a dict
        """

        if camera == 'camera_microscope':
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
        else:
            return self.camera_fiber.temp_image

    def stop_free_run(self, camera: str):
        """ Stops the free run of the camera.

        :param camera: must be the same as specified in the config file, for example 'camera_microscope'

        .. todo:: This must change, since it was inherited from the time both cameras were stored in a dict
        """
        self.logger.info(f'Stopping the free run of {camera}')
        if camera == 'camera_microscope':
            self.camera_microscope.stop_free_run()
        elif camera == 'camera_fiber':
            self.camera_fiber.stop_free_run()

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

    def save_image_fiber_camera(self, filename: str) -> None:
        """ Saves the image being registered by the camera looking at the fiber-end. Does not alter the configuration
        of the camera, therefore what you see is what you get.

        :param filename: it assumes it has a placeholder for {cartridge_number} and {i} in order not to over write
                            files
        """
        self.logger.info('Acquiring image from the fiber')
        self.camera_fiber.stop_free_run()
        self.camera_fiber.config.apply_all()
        self.camera_fiber.trigger_camera()
        time.sleep(.25)
        image = self.camera_fiber.read_camera()[-1]
        self.logger.info(f'Acquired fiber image, max: {np.max(image)}, min: {np.min(image)}')

        filename = self.get_filename(filename)
        np.save(filename, image)
        self.logger.info(f'Saved fiber data to {filename}')
        self.camera_fiber.start_free_run()

    def save_image_microscope_camera(self, filename: str) -> None:
        """Saves the image shown on the microscope camera to the given filename.

        :param str filename: Must be a string containing two placeholders: {cartrdige_number}, {i}
        """
        filename = self.get_filename(filename)
        t0 = time.time()
        temp_image = self.camera_microscope.temp_image
        while temp_image is None:
            temp_image = self.camera_fiber.temp_image
            if time.time() - t0 > 10:
                raise CameraTimeout("It took too long to get a new frame from the microscope")
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
    def save_fiber_core(self):
        """Saves the image of the fiber core.

        .. TODO:: This method was designed in order to allow extra work to be done, for example, be sure
            the LED is ON, or use different exposure times.
        """
        image = self.camera_fiber.temp_image
        self.logger.info(f'Saving fiber image, max: {np.max(image)}, min: {np.min(image)}')
        filename = self.get_filename(self.config['info']['filename_fiber'])
        np.save(filename, image)
        # self.save_image_fiber_camera(self.config['info']['filename_fiber'])

    @Action
    def save_laser_position(self):
        """ Saves an image of the laser on the camera.

        .. TODO:: Having a separate method just to save the laser position is useful when wanting to automatize
            tasks, for example using several laser powers to check proper centroid extraction.
        """
        self.logger.info('Saving laser position')
        current_laser_power = self.config['laser']['power']
        camera_config = self.config['camera_fiber'].copy()
        self.config['laser']['power'] = self.config['centroid']['laser_power']
        self.config['camera_fiber']['exposure_time'] = Q_(self.config['centroid']['exposure_time'])
        self.config['camera_fiber']['gain'] = self.config['centroid']['gain']
        self.set_laser_power_633(self.config['centroid']['laser_power'])
        self.save_image_fiber_camera(self.config['info']['filename_laser'])
        self.stop_free_run('camera_fiber')
        self.set_laser_power_633(current_laser_power)
        self.config['laser']['power'] = current_laser_power
        self.config['camera_fiber'] = camera_config.copy()
        self.camera_fiber.start_free_run()

    @Action
    def save_particles_image(self):
        """ Saves the image shown on the microscope. This is only to keep as a reference. This method wraps the
        actual method `meth:save_iamge_microscope_camera` in case there is a need to set parameters before saving. Or
        if there are going to be different saving options (for example, low and high laser powers, etc.).
        """
        base_filename = self.config['info']['filename_microscope']
        self.save_image_microscope_camera(base_filename)

    def calculate_gaussian_centroid(self, image, x, y, crop_size):
        x = round(x)
        y = round(y)
        cropped_data = np.copy(image[x - crop_size:x + crop_size, y - crop_size:y + crop_size])
        cropped_data[cropped_data < np.mean(cropped_data)] = 0
        try:
            p = fitgaussian(cropped_data)
            extracted_position = p[1] + x - crop_size, p[2] + y - crop_size
            self.logger.info(f'Calculated center: {extracted_position}')
        except:
            extracted_position = None
            self.logger.exception('Exception fitting the gaussian')
        return extracted_position

    def calculate_laser_center(self):
        """ This method calculates the laser position based on the reflection from the fiber tip. It is meant to be
        used as a reference when focusing the laser on the fiber for calibrating.

        .. TODO:: Judge how precise this is. Perhaps it would be possible to use it instead of the laser reflection on
            the mirror?
        """
        image = np.copy(self.camera_fiber.temp_image)
        brightest = np.unravel_index(image.argmax(), image.shape)
        self.laser_center = self.calculate_gaussian_centroid(image, brightest[0], brightest[1], crop_size=25)

    def calculate_fiber_center(self, x, y, crop_size=15):
        """ Calculate the core center based on some initial coordinates x and y.
        It will perform a gaussian fit of a cropped region and store the data.

        Parameters
        ----------
        x: float
            x-coordinate for the initial fit of the image
        y: float
            y-coordinate for the initail fit of the image
        crop_size: int, optional
            Size of the square crop around x, y in order to minimize errors
        """
        self.logger.info(f'Calculating fiber center using ({x}, {y})')
        image = np.copy(self.camera_fiber.temp_image)
        self.fiber_center_position = self.calculate_gaussian_centroid(image, x, y, crop_size)
        return [x,y] #m

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
        self.logger.info('Finalizing fluorescence experiment')
        if self.saving:
            self.logger.debug('Finalizing the saving images')
            self.stop_saving_images()
        self.saving_event.set()
        if self.camera_fiber is not None:
            self.camera_fiber.finalize()
        if self.camera_microscope is not None:
            self.camera_microscope.finalize()
        self.set_laser_power_633(0)
        self.set_laser_power_488(0)
        self.electronics.finalize()
        self.daq.close()

        super(FluorescenceMeasurement, self).finalize()
        self.finalized = True
