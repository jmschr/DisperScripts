from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow

import pathlib


class ElectronicsWindow(QMainWindow):
    def __init__(self, experiment):
        super().__init__(parent=None)
        curr_path = pathlib.Path(__file__).parent
        uic.loadUi(curr_path/'GUI'/'electronics_window.ui', self)
        self.experiment = experiment

        self.side_led_button.clicked.connect(self.experiment.toggle_side_led)
        self.top_led_button.clicked.connect(self.experiment.toggle_top_led)
        self.fiber_led_button.clicked.connect(self.experiment.toggle_fiber_led)

        self.servo_button.clicked.connect(self.experiment.toggle_servo)

        self.laser_power_slider.valueChanged.connect(self.update_power)

        self.button_up.clicked.connect(self.move_up)
        self.button_down.clicked.connect(self.move_down)
        self.button_left.clicked.connect(self.move_left)
        self.button_right.clicked.connect(self.move_right)

    def update_power(self, power):
        power = int(power)
        self.laser_power_lcd.display(power)
        self.experiment.laser_power(power)

    def move_right(self):
        speed = int(self.mirror_speed.text())
        self.experiment.move_piezo(speed=speed, direction=1, axis=1)

    def move_left(self):
        speed = int(self.mirror_speed.text())
        self.experiment.move_piezo(speed=speed, direction=0, axis=1)

    def move_up(self):
        speed = int(self.mirror_speed.text())
        self.experiment.move_piezo(speed=speed, direction=1, axis=2)

    def move_down(self):
        speed = int(self.mirror_speed.text())
        self.experiment.move_piezo(speed=speed, direction=0, axis=2)
