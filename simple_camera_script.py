import logging
from time import time, sleep

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from dispertech.models.cameras.basler import Camera
from dispertech.util.log import get_logger, log_to_screen
from experimentor import Q_
from experimentor.core import Publisher
from experimentor.views.camera import CameraViewerWidget


logger = get_logger()
handler = log_to_screen(level=logging.INFO)

ace = Camera('ac')
ace.initialize()
ace.set_acquisition_mode(ace.MODE_CONTINUOUS)
ace.set_exposure(Q_('.1s'))

ace.start_free_run()

app = QApplication([])
window = CameraViewerWidget.connect_to_camera(ace)
window.show()
app.exec()

ace.finalize()
