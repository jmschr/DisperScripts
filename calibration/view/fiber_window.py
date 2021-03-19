import os
import time
import numpy as np
import pyqtgraph as pg

from PyQt5 import uic, QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QStatusBar

from calibration.view import BASE_DIR_VIEW
from experimentor import Q_
from experimentor.lib.log import get_logger
from experimentor.views.base_view import BaseView
from experimentor.views.camera.camera_viewer_widget import CameraViewerWidget

logger = get_logger(__name__)




class FiberWindow(BaseView, QMainWindow):
    def __init__(self, experiment):
        # m lines of code upto next #m will be removed since the new code in the mouse_clicked make this variable Unnecessary
        # multiply_array_imported is a variable that ensures that the multiply array is only imported once
        # (from the file where it is saved)
        multiply_array_imported = 0
        # After being imported (see mouse_clicked), the value is changed to 1.
        #m


        super(FiberWindow, self).__init__()
        uic.loadUi(os.path.join(BASE_DIR_VIEW, 'GUI', 'Fiber_End_Window.ui'), self)

        self.experiment = experiment

        self.draw_center = False  # Used to decide whether to calculate and draw the center of the fiber (in real-time)

        self.camera_viewer = CameraViewerWidget(parent=self)
        self.camera_widget.layout().addWidget(self.camera_viewer)
        self.camera_viewer.clicked_on_image.connect(self.mouse_clicked)

        self.fiber_center_marker = pg.PlotDataItem(pen=None)
        self.fiber_center_marker.setBrush(255, 0, 0, 255)

        self.camera_viewer.view.addItem(self.fiber_center_marker)

        self.connect_to_action(self.button_fiber_led.clicked, self.experiment.toggle_fiber_led)
        self.connect_to_action(self.save_core_button.clicked, self.experiment.save_fiber_core)
        self.connect_to_action(self.save_laser_button.clicked, self.experiment.save_laser_position)

        self.button_fiber_led.clicked.connect(self.update_ui)

        self.apply_button.clicked.connect(self.update_camera)

        self.update_image_timer = QTimer()
        self.update_image_timer.timeout.connect(self.update_image)
        self.update_centers_timer = QTimer()
        self.update_centers_timer.timeout.connect(self.update_centers)

        # For debugging purposes
        self.status_bar = self.statusBar()
        self.setStatusBar(self.status_bar)
        self.last_update = time.time()

        self.update_ui()
        self.update_image_timer.start(50)
        self.update_centers_timer.start(150)

        self.updating_times = np.zeros(10)

    def update_centers(self):
        if self.laser_track.isChecked():
            self.experiment.calculate_laser_center()

        if self.experiment.laser_center:
            self.laser_center_position.setText(
                f"{self.experiment.laser_center[0]:4.2f}, "
                f"{self.experiment.laser_center[1]:4.2f}")

        if self.experiment.fiber_center_position:
            self.fiber_core_position.setText(
                f"{self.experiment.fiber_center_position[0]:4.2f}, "
                f"{self.experiment.fiber_center_position[1]:4.2f}")

    def add_fiber_center_mark(self):
        brush = pg.mkBrush(color=(255, 0, 0))
        pos = self.experiment.fiber_center_position
        #The 0 and 1 are switched places in the line of code below at 16/3, yet to bechecked if correct
        self.fiber_center_marker.setData([pos[1], ], [pos[0], ], symbolSize=50, symbol='x', symbolBrush=brush)

    def update_ui(self):
        self.camera_exposure_line.setText("{:~}".format(Q_(self.experiment.camera_fiber.exposure)))
        self.camera_gain_line.setText(str(self.experiment.camera_fiber.gain))
        if self.experiment.electronics.fiber_led:
            self.button_fiber_led.setText('Switch LED OFF')
        else:
            self.button_fiber_led.setText('Switch LED ON')

    def update_camera(self):
        """ Updates the properties of the camera. """

        logger.info('Updating parameters of the camera')
        self.experiment.camera_fiber.config.update({
            'exposure': Q_(self.camera_exposure_line.text()),
            'gain': float(self.camera_gain_line.text()),
        })
        self.experiment.camera_fiber.config.apply_all()

    def update_image(self):
        t0 = time.perf_counter()
        img = self.experiment.get_latest_image('camera_fiber')
        self.camera_viewer.update_image(img)
        t1 = time.perf_counter() - t0
        self.updating_times = np.roll(self.updating_times, 1)
        self.updating_times[0] = t1
        self.status_bar.showMessage(f'{np.mean(self.updating_times)*1000}ms')
        self.last_update = time.time()

    def mouse_clicked(self, x, y):
        """ Slot which gets the mouse clicked on the image. The signal associated is an overwrite of the PyQtgraph
        default signal to get directly the coordinates of the mouse clicked in pixels of the image.
        """
        logger.info('Calculating center of the fiber')

        #m
        self.experiment.Code1dot7for_implementation(self.experiment.get_latest_image('camera_fiber'), \
                                                    self.experiment.multiply_array)

        #The red X is shown in the figure at the fiber core location
        self.add_fiber_center_mark()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        logger.info('Fiber Window Closed')
        self.update_image_timer.stop()
        self.update_centers_timer.stop()
        super().closeEvent(a0)
