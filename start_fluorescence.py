import logging
# import os
# import sys
# from time import sleep

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
import time

import yaml
from PyQt5.QtWidgets import QApplication

from fluorescence.models.experiment import FluorescenceMeasurement
from fluorescence.view.digilent_window import DAQWindow
from fluorescence.view.fiber_window import FiberWindow
from fluorescence.view.microscope_window import MicroscopeWindow
from experimentor.lib.log import log_to_screen, get_logger

if __name__ == "__main__":
    logger = get_logger()
    handler = log_to_screen(logger=logger)
    experiment = FluorescenceMeasurement()
    experiment.load_configuration('fluorescence.yml', yaml.UnsafeLoader)
    executor = experiment.initialize()
    while executor.running():
        time.sleep(.1)

    app = QApplication([])
    microscope_window = MicroscopeWindow(experiment)
    microscope_window.show()
    fiber_window = FiberWindow(experiment)
    fiber_window.show()
    daq_window = DAQWindow(experiment)
    daq_window.show()
    app.exec()
    experiment.finalize()
