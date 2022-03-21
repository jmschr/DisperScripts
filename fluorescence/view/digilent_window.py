import os

import numpy as np
import pyqtgraph as pg

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow

from experimentor.views.base_view import BaseView
from fluorescence.view import BASE_DIR_VIEW


class DAQWindow(BaseView, QMainWindow):
    def __init__(self, experiment):
        super(DAQWindow, self).__init__()
        uic.loadUi(os.path.join(BASE_DIR_VIEW, 'GUI', 'digilent_window.ui'), self)

        self.experiment = experiment

        self.plot_widget = pg.PlotWidget()
        self.data_vis.layout().addWidget(self.plot_widget)
        self.plot = self.plot_widget.getPlotItem().plot(np.zeros(100))

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)

    def update(self):
        self.experiment.read_daq()
        self.plot.setData(self.experiment.last_daq)

    def update_parameters(self):
        self.experiment.config['daq'].update(
            {'channel_in': self.combo_input.currentIndex(),
            'channel_trigger': self.combo_trigger.currentIndex(),
            'frequency': int(self.line_frequency.value()),
            'buffer': int(self.line_buffer.value()),
            'trigger': str(self.combo_trigger_mode.currentText()),
            'trigger_level': float(self.line_trigger_level.value()),
        }
        )
