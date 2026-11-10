from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.gui import QgsDockWidget

from .panel import Panel


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dock = None
        self.panel = None

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

    def create_dock(self):
        self.dock = QgsDockWidget("{{PLUGIN_TITLE}}", self.iface.mainWindow())
        self.panel = Panel()
        self.dock.setWidget(self.panel)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        self.panel.run_requested.connect(self.run)
        self.dock.visibilityChanged.connect(self.action.setChecked)

    def toggle(self, checked):
        if self.dock is None:
            self.create_dock()
        self.dock.setVisible(checked)

    def run(self):
        self.iface.messageBar().pushInfo(
            "{{PLUGIN_TITLE}}", "The dock action ran."
        )

    def unload(self):
        if self.dock is not None:
            self.dock.visibilityChanged.disconnect()
            if self.panel is not None:
                self.panel.run_requested.disconnect()
            self.iface.removeDockWidget(self.dock)
            self.dock.deleteLater()
            self.dock = None
            self.panel = None
        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.triggered.disconnect()
            self.action.deleteLater()
            self.action = None
