import os

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow

from calibration_setup.view import BASE_DIR_VIEW


class MicroscopeWindow(QMainWindow):
    def __init__(self, experiment=None):
        super().__init__()
        self.experiment = experiment

        filename = os.path.join(BASE_DIR_VIEW, 'GUI', 'Microscope_Focusing.ui')
        uic.loadUi(filename, self)

    def update_ui(self):
        """ Method to update the UI with the values given by the experiment. This does not include the camera view """
        self.cartridge_line.setText(self.experiment.config['info']['cartridge_number'])
        self.motor_speed_line.setText(self.experiment.config['mirror']['speed'])
        self.power_slider.setValue(self.experiment.config['laser']['power'])
        self.lcd_laser_power.display(self.experiment.config['laser']['power'])
        self.camera_exposure_line.setText(self.experiment.config['camera_microscope']['exposure_time'])
        self.camera_gain_line.setText(self.experiment.config['camera_microscope']['gain'])




if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    win = MicroscopeWindow()
    win.show()
    app.exec()
