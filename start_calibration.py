# import os
# import sys
# from time import sleep
#
#
# if __name__ == "__main__":
#     os.environ.setdefault("EXPERIMENTOR_SETTINGS_MODULE", "calibration_settings")
#
#     this_dir = os.path.abspath(os.path.dirname(__file__))
#     sys.path.append(this_dir)
#
#     from experimentor.core.app import ExperimentApp
#
#     app = ExperimentApp(gui=True)
#     while app.gui_thread.is_alive():
#         sleep(1)


import logging
from multiprocessing.spawn import freeze_support

from PyQt5.QtWidgets import QApplication
from experimentor.lib.log import get_logger, log_to_screen
from experimentor.models.models import BaseModel

from calibration.models.experiment import CalibrationSetup
from calibration.view.fiber_window import FiberWindow
from calibration.view.microscope_window import MicroscopeWindow

if __name__ == "__main__":
    freeze_support()



    logger = get_logger(level=logging.INFO)
    handler = log_to_screen(logger, level=logging.INFO)

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
    for inst in BaseModel.get_instances(recursive=True):
        inst.finalize()
