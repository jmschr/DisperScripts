import os

import numpy as np
import pyqtgraph as pg

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow

from experimentor.views.base_view import BaseView
from fluorescence.view import BASE_DIR_VIEW


class DAQWindow(QMainWindow, BaseView):

    def __init__(self, experiment):
        super().__init__()

        filename = os.path.join(BASE_DIR_VIEW, 'GUI', 'digilent_window.ui')
        self.logger.info(f'Loading {filename} to Digilent Window')
        uic.loadUi(filename, self)

        self.experiment = experiment

        self.plot_widget = pg.PlotWidget()
        self.data_vis.layout().addWidget(self.plot_widget)
        self.plot = self.plot_widget.getPlotItem().plot(np.zeros(100))

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)

        self.button_start.clicked.connect(self.start_acquisition)
        self.button_stop.clicked.connect(self.stop_acquisition)

    def start_acquisition(self):
        self.logger.info('Starting acquisition')
        self.update_parameters()
        self.experiment.daq.continuous_reads()

    def stop_acquisition(self):
        self.experiment.daq.stop_continuous_reads()

    def update(self):
        self.plot.setData(self.experiment.daq.last_daq)

    def update_parameters(self):
        self.experiment.daq.config.update(
            {
                'channel_in': self.combo_input.currentIndex(),
                'channel_trigger': self.combo_trigger.currentIndex(),
                'frequency': int(self.line_frequency.text()),
                'buffer': int(self.line_buffer.text()),
                'trigger': str(self.combo_trigger_mode.currentText()),
                'trigger_level': float(self.line_trigger_level.text()),
                }
            )
        self.experiment.daq.reconfigure_daq()

    def closeEvent(self, a0):
        self.logger.info('DAQ Window Closed')
        # self.update_timer.stop()
        # self.experiment.daq.stop_continuous_reads()
        super().closeEvent(a0)
