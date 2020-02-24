import numpy as np
import os

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow

from calibration.view import BASE_DIR_VIEW
from experimentor import Q_
from experimentor.lib.log import get_logger

import calibration.view.GUI.resources
from experimentor.views.camera.camera_viewer_widget import CameraViewerWidget

logger = get_logger(__name__)


class MicroscopeWindow(QMainWindow):
    def __init__(self, experiment=None):
        super().__init__()
        self.experiment = experiment
        self.button_laser_status = 0

        filename = os.path.join(BASE_DIR_VIEW, 'GUI', 'Microscope_Focusing.ui')
        uic.loadUi(filename, self)

        self.camera_viewer = CameraViewerWidget()
        self.camera_widget.layout().addWidget(self.camera_viewer)

        self.cartridge_line.editingFinished.connect(self.update_experiment)
        self.motor_speed_line.editingFinished.connect(self.update_experiment)
        self.apply_button.clicked.connect(self.update_camera)

        # self.camera_exposure_line.editingFinished.connect(self.update_camera)
        # self.camera_gain_line.editingFinished.connect(self.update_camera)

        self.save_button.clicked.connect(self.experiment.save_particles_image)
        self.button_laser.clicked.connect(self.toggle_servo)
        self.power_slider.valueChanged.connect(self.update_laser)

        self.button_left.clicked.connect(self.move_left)
        self.button_right.clicked.connect(self.move_right)
        self.button_up.clicked.connect(self.move_up)
        self.button_down.clicked.connect(self.move_down)

        self.update_image_timer = QTimer()
        self.update_image_timer.timeout.connect(self.update_image)

        self.update_ui()
        self.update_experiment()

        self.update_image_timer.start(50)

    def update_ui(self):
        """ Method to update the UI with the values given by the experiment. This does not include the camera view """
        self.cartridge_line.setText(str(self.experiment.config['info']['cartridge_number']))
        self.motor_speed_line.setText(str(self.experiment.config['mirror']['speed']))
        self.power_slider.setValue(self.experiment.config['laser']['power'])
        self.lcd_laser_power.display(self.experiment.config['laser']['power'])
        self.camera_exposure_line.setText(
            "{:~}".format(Q_(self.experiment.config['camera_microscope']['exposure_time'])))
        self.camera_gain_line.setText(str(self.experiment.config['camera_microscope']['gain']))

    def update_camera(self):
        """ Updates the properties of the camera. """

        logger.info('Updating parameters of the camera')
        self.experiment.config['camera_microscope'].update({
            'exposure_time': Q_(self.camera_exposure_line.text()),
            'gain': float(self.camera_gain_line.text()),
        })
        self.experiment.start_free_run('camera_microscope')

    def update_experiment(self):
        """ Update the parameters of the experiment, from the UI to the model. Can be triggered by the click on an
        apply button or by another signal, such as finished editing a line """

        logger.info('Updating experiment parameters')
        self.experiment.cameras['camera_microscope'].set_exposure(Q_(self.camera_exposure_line.text()))
        self.experiment.cameras['camera_microscope'].set_gain(float(self.camera_gain_line.text()))

        self.experiment.config['info'].update({
            'cartridge_number': str(self.cartridge_line.text()),
        })
        self.experiment.config['mirror'].update({
            'speed': int(self.motor_speed_line.text()),
        })

        self.update_ui()  # Forces to refresh the parameters

    def update_laser(self, power):
        power = int(power)
        # Open the servo if increasing the power
        if power > 0:
            self.experiment.servo_on()
            self.button_laser.setText('Switch OFF')
            self.button_laser_status = 1
        else:
            self.experiment.servo_off()
            self.button_laser.setText('Switch ON')
            self.button_laser_status = 0

        self.lcd_laser_power.display(power)
        self.experiment.set_laser_power(power)

    def toggle_servo(self):
        if self.button_laser_status:
            self.experiment.servo_off()
            self.button_laser.setText("Switch ON")
            self.button_laser_status = 0
        else:
            self.experiment.servo_on()
            self.button_laser.setText("Switch OFF")
            self.button_laser_status = 1

    def move_right(self):
        self.experiment.move_mirror(direction=1, axis=2)

    def move_left(self):
        self.experiment.move_mirror(direction=0, axis=2)

    def move_up(self):
        self.experiment.move_mirror(direction=1, axis=1)

    def move_down(self):
        self.experiment.move_mirror(direction=0, axis=1)

    def update_image(self):
        if self.background_box.isChecked() and self.experiment.background is not None:
            t_image = self.experiment.cameras['camera_microscope'].temp_image
            if t_image is not None:
                img = t_image.astype(np.int16) - self.experiment.background
                img[img < 0] = 0
                img = img.astype(np.uint16)
            else:
                img = None
        else:
            img = self.experiment.cameras['camera_microscope'].temp_image
        self.camera_viewer.update_image(img)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    win = MicroscopeWindow()
    win.show()
    app.exec()
