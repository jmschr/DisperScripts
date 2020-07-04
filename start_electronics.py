import sys

from PyQt5.QtWidgets import QApplication

from electronics.view.electronics_window import ElectronicsWindow
from electronics.models.experiment import ControlArduino

if __name__ == "__main__":
    experiment = ControlArduino('dispertech.yml')
    experiment.initialize()
    app = QApplication([])
    electronics_window = ElectronicsWindow(experiment)
    electronics_window.show()
    app.exec()
    experiment.finalize()
    sys.exit()
