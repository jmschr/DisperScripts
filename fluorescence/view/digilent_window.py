import os
import pyqtgraph as pg

from PyQt5 import uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow

from experimentor.views.base_view import BaseView
from fluorescence.view import BASE_DIR_VIEW


class FiberWindow(BaseView, QMainWindow):
    def __init__(self, experiment):
        super(FiberWindow, self).__init__()
        uic.loadUi(os.path.join(BASE_DIR_VIEW, 'GUI', 'digilent_window.ui'), self)

        self.experiment = experiment

        self.plot_widget = pg.PlotWidget()
        self.data_vis.layou().addWidget(self.plot_widget)
        self.plot = self.plot_widget.getPlotItem().plot([0, ], [0,])

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)

    def update(self):
        self.plot.setData(self.experiment.last_daq)
