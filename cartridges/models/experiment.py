from dispertech.models.electronics.arduino import ArduinoModel
from experimentor.models.devices.cameras.basler.basler import BaslerCamera
from experimentor.models.experiments import Experiment


class Cartridges(Experiment):
    def __init__(self, filename=None):
        super().__init__(filename)
        self.dart = BaslerCamera('da')
        self.ace = BaslerCamera('ac')

        self.servo = ArduinoModel(**self.config['electronics']['servo'])
        self.arduino = ArduinoModel(**self.config['electronics']['arduino'])

    def initialize(self):
        self.logger.info('Initializing Cameras and arduinos')
        self.dart.initialize()
        self.ace.initialize()
        self.dart.config.update(self.config['dart'])
        self.dart.config.apply_all()
        self.ace.config.update(self.config['ace'])
        self.dart.config.apply_all()

        self.servo.initialize()
        self.arduino.initialize()

    def move_mirror(self, speed: int, direction: int, axis: int):
        self.logger.info(f'Moving mirror: speed:{speed}, direction:{direction}, axis:{axis}')
        self.arduino.move_mirror(speed, direction, axis)

    def set_servo(self, position: int):
        self.logger.info(f'Moving servo to {position}')
        self.servo.move_servo(position=position)


