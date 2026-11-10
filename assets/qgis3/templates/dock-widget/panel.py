from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class Panel(QWidget):
    run_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("{{PLUGIN_TITLE}} is ready."))
        button = QPushButton("Run")
        button.clicked.connect(self.run_requested)
        layout.addWidget(button)
        layout.addStretch(1)
