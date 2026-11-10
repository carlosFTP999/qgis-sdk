from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .layer_processor import LayerProcessor


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.processor = LayerProcessor(iface)

    def initGui(self):
        self.action = QAction(
            QIcon(str(Path(__file__).with_name("icon.png"))),
            "{{MENU_TEXT}}",
            self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&{{PLUGIN_TITLE}}", self.action)
        self.iface.addToolBarIcon(self.action)

    def run(self):
        self.processor.run()

    def unload(self):
        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.triggered.disconnect()
            self.action.deleteLater()
            self.action = None
        self.processor = None
