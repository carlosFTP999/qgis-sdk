from qgis.gui import QgsDockWidget
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QAction

from .panel import Panel


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dock = None
        self.panel = None

    def initGui(self):
        self.action = QAction("{{MENU_TEXT}}", self.iface.mainWindow())
        self.action.triggered.connect(self.toggle)
        self.iface.addPluginToMenu("&{{PLUGIN_TITLE}}", self.action)

        self.panel = Panel(self.iface, self.iface.mainWindow())
        self.dock = QgsDockWidget("{{PLUGIN_TITLE}}", self.iface.mainWindow())
        self.dock.setWidget(self.panel)
        self.iface.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.dock
        )
        self.dock.hide()

    def toggle(self):
        if self.dock is not None:
            self.dock.setVisible(not self.dock.isVisible())

    def unload(self):
        if self.dock is not None:
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
        if self.panel is not None:
            self.panel.deleteLater()
            self.panel = None
        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.action.deleteLater()
            self.action = None
