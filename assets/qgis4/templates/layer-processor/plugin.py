from qgis.core import Qgis
from qgis.PyQt.QtGui import QAction

from .dialog import LayerDialog


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None

    def initGui(self):
        self.action = QAction("{{MENU_TEXT}}", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&{{PLUGIN_TITLE}}", self.action)

    def unload(self):
        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.action.deleteLater()
            self.action = None
        if self.dialog is not None:
            self.dialog.deleteLater()
            self.dialog = None

    def run(self):
        if self.dialog is None:
            self.dialog = LayerDialog(self.iface.mainWindow())

        if not self.dialog.exec():
            return

        layer = self.dialog.selected_layer()
        if layer is None:
            self.iface.messageBar().pushWarning(
                "{{PLUGIN_TITLE}}", "Select a vector layer."
            )
            return

        self.iface.messageBar().pushMessage(
            "{{PLUGIN_TITLE}}",
            f"{layer.featureCount()} features in {layer.name()}",
            level=Qgis.MessageLevel.Info,
        )
