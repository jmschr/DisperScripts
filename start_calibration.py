import logging
import os
import sys
from time import sleep

#
# if __name__ == "__main__":
#     os.environ.setdefault("EXPERIMENTOR_SETTINGS_MODULE", "calibration_settings")
#
#     this_dir = os.path.abspath(os.path.dirname(__file__))
#     sys.path.append(this_dir)
#
#     from experimentor.core.app import ExperimentApp
#
#     app = ExperimentApp(gui=True, logger=logging.INFO)
#
#     while app.is_running:
#         sleep(1)
#     app.finalize()
import yaml
from PyQt5.QtWidgets import QApplication

from calibration.models.experiment import CalibrationSetup
from calibration.view.fiber_window import FiberWindow
from calibration.view.microscope_window import MicroscopeWindow

if __name__ == "__main__":
    experiment = CalibrationSetup()
    experiment.load_configuration('dispertech.yml', yaml.UnsafeLoader)
    experiment.initialize()
    app = QApplication([])
    microscope_window = MicroscopeWindow(experiment)
    microscope_window.show()
    fiber_window = FiberWindow(experiment)
    fiber_window.show()
    app.exec()
    experiment.finalize()
