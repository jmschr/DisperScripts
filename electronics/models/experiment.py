import yaml

from dispertech.models.electronics.arduino import ArduinoModel
from experimentor.models.experiments import Experiment


class ControlArduino(Experiment):
    def __init__(self, filename=None):
        super().__init__()
        self.load_configuration(filename, loader=yaml.UnsafeLoader)
        self.electronics = None
        self.servo = 0

    def initialize(self):
        self.electronics = ArduinoModel(self.config['electronics']['arduino']['device'])
        self.electronics.initialize()

    def toggle_side_led(self):
        self.electronics.side_led = 0 if self.electronics.side_led else 1

    def toggle_top_led(self):
        self.electronics.top_led = 0 if self.electronics.top_led else 1

    def toggle_fiber_led(self):
        self.electronics.fiber_led = 0 if self.electronics.fiber_led else 1

    def toggle_power_led(self):
        self.electronics.power_led = 0 if self.electronics.power_led else 1

    def toggle_laser_led(self):
        self.electronics.laser_led = 0 if self.electronics.laser_led else 1

    def toggle_measure_led(self):
        self.electronics.measure_led = 0 if self.electronics.measure_led else 1

    def laser_power(self, power):
        self.electronics.laser_power = power

    def toggle_servo(self):
        if self.servo:
            self.electronics.move_servo(0)
            self.servo = 0
        else:
            self.electronics.move_servo(1)
            self.servo = 1

    def move_mirror(self, speed, direction, axis):
        self.electronics.move_mirror(speed, direction, axis)
