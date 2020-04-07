import os

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow

from calibration.view import BASE_DIR_VIEW
from experimentor import Q_
from experimentor.lib.log import get_logger
from experimentor.views.camera.camera_viewer_widget import CameraViewerWidget

logger = get_logger(__name__)


class FiberWindow(QMainWindow):
    def __init__(self, experiment):
        super(FiberWindow, self).__init__()
        uic.loadUi(os.path.join(BASE_DIR_VIEW, 'GUI', 'Fiber_End_Window.ui'), self)

        self.experiment = experiment

        self.camera_viewer = CameraViewerWidget()
        self.camera_widget.layout().addWidget(self.camera_viewer)
        self.camera_viewer.clicked_on_image.connect(self.mouse_clicked)

        self.button_fiber_led.clicked.connect(self.experiment.toggle_fiber_led)
        self.button_fiber_led.clicked.connect(self.update_ui)

        self.save_core_button.clicked.connect(self.experiment.save_fiber_core)
        self.save_laser_button.clicked.connect(self.experiment.save_laser_position)

        self.camera_exposure_line.editingFinished.connect(self.update_camera)
        self.camera_gain_line.editingFinished.connect(self.update_camera)

        self.update_image_timer = QTimer()
        self.update_image_timer.timeout.connect(self.update_image)
        self.update_centers_timer = QTimer()
        self.update_centers_timer.timeout.connect(self.update_centers)

        self.update_ui()
        self.update_image_timer.start(50)
        self.update_centers_timer.start(50)

    def update_centers(self):
        if self.laser_track.isChecked():
            self.experiment.calculate_laser_center()

        if self.experiment.laser_center:
            self.laser_center_position.setText(f"{self.experiment.laser_center[0]:4.2f}, {self.experiment.laser_center[1]:4.2f}")

        if self.experiment.extracted_position:
            self.fiber_core_position.setText(f"{self.experiment.extracted_position[0]:4.2f}, {self.experiment.extracted_position[1]:4.2f}")


    def update_ui(self):
        self.camera_exposure_line.setText("{:~}".format(Q_(self.experiment.config['camera_fiber']['exposure_time'])))
        self.camera_gain_line.setText(str(self.experiment.config['camera_fiber']['gain']))
        if self.experiment.electronics['arduino'].fiber_led:
            self.button_fiber_led.setText('Switch LED OFF')
        else:
            self.button_fiber_led.setText('Switch LED ON')

    def update_camera(self):
        """ Updates the properties of the camera. """

        logger.info('Updating parameters of the camera')
        self.experiment.config['camera_fiber'].update({
            'exposure_time': Q_(self.camera_exposure_line.text()),
            'gain': float(self.camera_gain_line.text()),
        })
        self.experiment.cameras['camera_fiber'].set_exposure(Q_(self.camera_exposure_line.text()))
        self.experiment.cameras['camera_fiber'].set_gain(float(self.camera_gain_line.text()))
        self.experiment.cameras['camera_fiber'].stop_free_run()
        self.experiment.cameras['camera_fiber'].start_free_run()

    def update_experiment(self):
        logger.info('Updating the properties of the experiment')
        self.experiment.cameras['camera_fiber'].set_exposure(Q_(self.camera_exposure_line.text()))
        self.experiment.cameras['camera_fiber'].set_gain(float(self.camera_gain_line.text()))
        self.update_ui()

    def update_image(self):
        self.camera_viewer.update_image(self.experiment.cameras['camera_fiber'].temp_image)

    def mouse_clicked(self, x, y):
        """ Slot which gets the mouse clicked on the image. The signal associated is an overwrite of the PyQtgraph
        default signal to get directly the coordinates of the mouse clicked in pixels of the image.
        """
        logger.info('Calculating center of the fiber')
        self.experiment.calculate_fiber_center(x, y)
