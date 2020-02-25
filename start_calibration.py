import logging

from multiprocessing.spawn import freeze_support

import sys

from PyQt5.QtWidgets import QApplication

from calibration.models.experiment import CalibrationSetup
from calibration.view.fiber_window import FiberWindow
from calibration.view.microscope_window import MicroscopeWindow
from experimentor.lib.log import get_logger, log_to_screen

if __name__ == "__main__":
    freeze_support()

    logger = get_logger(level=logging.INFO)
    handler = log_to_screen(level=logging.INFO)

    experiment = CalibrationSetup('dispertech.yml')
    experiment.initialize_cameras()
    experiment.initialize_electronics()
    experiment.servo_off()
    experiment.start_free_run('camera_microscope')
    experiment.start_free_run('camera_fiber')

    app = QApplication([])
    microscope_window = MicroscopeWindow(experiment)
    microscope_window.show()
    fiber_window = FiberWindow(experiment)
    fiber_window.show()
    app.exec()
    experiment.finalize()
    sys.exit()
