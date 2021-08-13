import os

import qdarkstyle
import sys


from PyQt5.QtWidgets import QApplication

from PiezoMove.arduino import ArduinoModel
from PiezoMove.main_window import PiezoMoveWindow

os.environ['QT_API'] = 'pyqt5'

device = 0
if len(sys.argv) > 1:
    device = int(sys.argv[1])

print(f'Using piezo device {device}')

arduino = ArduinoModel(device=device)
arduino.initialize()

app = QApplication([])
win = PiezoMoveWindow(arduino)

app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

win.show()
sys.exit(app.exec())
