"""
    Arduino Model
    =============
    This is an ad-hoc model for controlling an Arduino Due board, which will in turn control a piezo-mirror, a laser,
    and some LED's.
"""
from multiprocessing import Event

import pyvisa
from pyvisa import VisaIOError
from threading import RLock
from time import sleep

from dispertech.controller.devices.arduino.arduino import Arduino
from experimentor.lib.log import get_logger
from experimentor.models import Feature
from experimentor.models.decorators import make_async_thread
from experimentor.models.devices.base_device import ModelDevice


rm = pyvisa.ResourceManager('@py')


class ArduinoModel(ModelDevice):
    def __init__(self, port=None, device=0):
        """ Use the port if you know where the Arduino is connected, or use the device number in the order shown by
        pyvisa.
        """
        super().__init__()
        self._threads = []
        self._stop_temperature = Event()
        self.temp_electronics = 0
        self.temp_sample = 0
        self.query_lock = RLock()
        self.driver = None
        self.port = port
        self.device = device

        self.logger = get_logger()

        self._laser_power = 0
        self._laser_led = 0
        self._fiber_led = 0
        self._top_led = 0
        self._side_led = 0
        self._power_led = 0
        self._measure_led = 0
        self._servo_position = 0

    @make_async_thread
    def initialize(self):
        """ This is a highly opinionated initialize method, in which the power of the laser is set to a minimum, the
        servo shutter is closed, and LEDs are switched off.
        """
        with self.query_lock:
            if not self.port:
                self.port = Arduino.list_devices()[self.device]
            self.driver = rm.open_resource(self.port)

            sleep(1)
            self.driver.baud_rate = 115200
            self.driver.timeout = 2500
            # This is very silly, but clears the buffer so that next messages are not broken
            try:
                self.driver.query("IDN")
            except VisaIOError:
                try:
                    self.driver.read()
                except VisaIOError:
                    pass

    # @make_async_thread
    def move_piezo(self, speed: int, direction: int, axis: int):
        """ Moves the mirror connected to the board

        :param int speed: Speed, from 0 to 2^6-1.
        :param direction: 0 or 1, depending on which direction to move the mirror
        :param axis: 1 or 2, to select the axis
        """

        with self.query_lock:
            print('Speed: ', speed)
            print('Direction: ', direction)
            print('Axis: ', axis)
            binary_speed = '{0:06b}'.format(speed)
            binary_speed = str(direction) + str(1) + binary_speed
            print('Binary speed: ', binary_speed)
            number = int(binary_speed, 2)
            bytestring = number.to_bytes(1, 'big')
            print('{0:b}'.format(number))
            print(self.driver.query(f"mot{axis}"))
            self.driver.write_raw(bytestring)
            ans = self.driver.read()
            print("{0:b}".format(int(ans)))
        print('Finished moving')
        self.logger.info('Finished moving')


    def finalize(self):
        super().finalize()
        self.clean_up_threads()
        if len(self._threads):
            self.logger.warning(f'There are {len(self._threads)} still alive in Arduino')


if __name__ == "__main__":
    dev = Arduino.list_devices()[0]
    ard = ArduinoModel(dev)
    ard.laser_power = 50
    ard.move_mirror(60, 1, 1)
    sleep(2)
    ard.move_mirror(60,0,1)
    ard.laser_power = 100
    sleep(2)
    ard.laser_power = 1

