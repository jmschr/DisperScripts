import sys


from PyQt5.QtWidgets import QApplication

from PiezoMove.arduino import ArduinoModel
from PiezoMove.main_window import PiezoMoveWindow

device = 5

arduino = ArduinoModel(device=device)
arduino.initialize()

app = QApplication([])
win = PiezoMoveWindow(arduino)
win.show()
sys.exit(app.exec())
