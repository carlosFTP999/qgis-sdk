from qgis.core import Qgis
from qgis.PyQt.QtGui import QAction

from .maptool import PointTool


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.tool = None

    def initGui(self):
        self.action = QAction("{{MENU_TEXT}}", self.iface.mainWindow())
        self.action.triggered.connect(self.activate)
        self.iface.addPluginToMenu("&{{PLUGIN_TITLE}}", self.action)

    def activate(self):
        if self.tool is None:
            self.tool = PointTool(self.iface.mapCanvas())
            self.tool.canvasClicked.connect(self.on_click)
        self.iface.mapCanvas().setMapTool(self.tool)

    def on_click(self, point, button):
        self.iface.messageBar().pushMessage(
            "{{PLUGIN_TITLE}}",
            f"Clicked at {point.x():.6f}, {point.y():.6f}",
            level=Qgis.MessageLevel.Info,
        )

    def unload(self):
        if self.tool is not None:
            if self.iface.mapCanvas().mapTool() is self.tool:
                self.iface.mapCanvas().unsetMapTool(self.tool)
            try:
                self.tool.canvasClicked.disconnect(self.on_click)
            except TypeError:
                pass
            self.tool.deleteLater()
            self.tool = None

        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.action.deleteLater()
            self.action = None
