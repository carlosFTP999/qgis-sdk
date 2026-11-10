from qgis.core import Qgis
from qgis.gui import QgsMapLayerComboBox
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class LayerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("{{PLUGIN_TITLE}}")
        self.setMinimumWidth(360)

        self.label = QLabel("Vector layer", self)
        self.layer_combo = QgsMapLayerComboBox(self)
        self.layer_combo.setFilters(Qgis.LayerFilter.VectorLayer)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.layer_combo)
        layout.addWidget(self.buttons)

    def selected_layer(self):
        return self.layer_combo.currentLayer()
