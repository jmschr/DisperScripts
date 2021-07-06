import os
from PyQt5 import uic

from PyQt5.QtWidgets import QMainWindow

from dispertech.models.electronics.arduino import ArduinoModel
from PiezoMove import BASE_DIR_VIEW


class PiezoMoveWindow(QMainWindow):
    def __init__(self, arduino: ArduinoModel):
        super().__init__()
        self.arduino = arduino
        self.button_laser_status = 0

        filename = os.path.join(BASE_DIR_VIEW, 'mainwindow.ui')
        uic.loadUi(filename, self)

        self.button_down.clicked.connect(self.move_down)
        self.button_up.clicked.connect(self.move_up)
        self.button_left.clicked.connect(self.move_left)
        self.button_right.clicked.connect(self.move_right)
        self.button_plus.clicked.connect(self.move_plus)
        self.button_minus.clicked.connect(self.move_minus)

    def move_up(self):
        speed = int(self.line_speed.text())
        self.arduino.move_piezo(speed, 0, 1)

    def move_down(self):
        speed = int(self.line_speed.text())
        self.arduino.move_piezo(speed, 1, 1)

    def move_left(self):
        speed = int(self.line_speed.text())
        self.arduino.move_piezo(speed, 0, 2)

    def move_right(self):
        speed = int(self.line_speed.text())
        self.arduino.move_piezo(speed, 1, 2)

    def move_plus(self):
        speed = int(self.line_speed.text())
        self.arduino.move_piezo(speed, 0, 3)

    def move_minus(self):
        speed = int(self.line_speed.text())
        self.arduino.move_piezo(speed, 1, 3)
