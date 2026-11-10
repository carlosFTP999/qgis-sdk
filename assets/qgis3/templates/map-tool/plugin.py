from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis, QgsMessageLog

from .point_tool import PointTool


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.tool = None

    def initGui(self):
        self.action = QAction(
            QIcon(str(Path(__file__).with_name("icon.png"))),
            "{{MENU_TEXT}}",
            self.iface.mainWindow(),
        )
        self.action.setCheckable(True)
        self.action.triggered.connect(self.toggle)
        self.iface.addPluginToMenu("&{{PLUGIN_TITLE}}", self.action)
        self.iface.addToolBarIcon(self.action)
        self.iface.mapCanvas().mapToolSet.connect(self.on_map_tool_changed)

    def toggle(self, checked):
        if checked:
            self.activate()
        else:
            self.deactivate()

    def activate(self):
        if self.tool is None:
            self.tool = PointTool(self.iface.mapCanvas(), self.on_click)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.action.setChecked(True)

    def deactivate(self):
        canvas = self.iface.mapCanvas()
        if self.tool is not None and canvas.mapTool() is self.tool:
            canvas.unsetMapTool(self.tool)
        self.action.setChecked(False)

    def on_map_tool_changed(self, new_tool, old_tool):
        self.action.setChecked(self.tool is not None and new_tool is self.tool)

    def on_click(self, point):
        QgsMessageLog.logMessage(
            "Clicked at {:.3f}, {:.3f}".format(point.x(), point.y()),
            "{{PLUGIN_TITLE}}",
            Qgis.Info,
        )
        self.iface.messageBar().pushInfo(
            "{{PLUGIN_TITLE}}",
            "Clicked at {:.3f}, {:.3f}".format(point.x(), point.y()),
        )

    def unload(self):
        canvas = self.iface.mapCanvas()
        canvas.mapToolSet.disconnect(self.on_map_tool_changed)
        if self.tool is not None and canvas.mapTool() is self.tool:
            canvas.unsetMapTool(self.tool)
        self.tool = None
        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.triggered.disconnect()
            self.action.deleteLater()
            self.action = None
