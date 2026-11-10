from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication

from .provider import {{PROVIDER_CLASS}}


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.provider = None

    def initGui(self):
        self.action = QAction(
            QIcon(str(Path(__file__).with_name("icon.png"))),
            "{{MENU_TEXT}}",
            self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&{{PLUGIN_TITLE}}", self.action)
        self.iface.addToolBarIcon(self.action)

        self.provider = {{PROVIDER_CLASS}}()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def run(self):
        import processing

        processing.execAlgorithmDialog(
            "{{PLUGIN_NAME}}:{{ALGORITHM_ID}}"
        )

    def unload(self):
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.triggered.disconnect()
            self.action.deleteLater()
            self.action = None
