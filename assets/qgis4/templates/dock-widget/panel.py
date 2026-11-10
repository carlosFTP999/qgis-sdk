from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class Panel(QWidget):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.label = QLabel("Layers: 0", self)
        self.button = QPushButton("Refresh", self)
        self.button.clicked.connect(self.refresh)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addStretch(1)

        self.refresh()

    def refresh(self):
        count = len(QgsProject.instance().mapLayers())
        self.label.setText(f"Layers: {count}")
