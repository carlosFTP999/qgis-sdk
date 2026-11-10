from qgis.core import Qgis, QgsApplication
from qgis.PyQt.QtGui import QAction

from .task import FetchTask


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.task = None

    def initGui(self):
        self.action = QAction("{{MENU_TEXT}}", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&{{PLUGIN_TITLE}}", self.action)

    def run(self):
        if self.task is not None:
            self.iface.messageBar().pushInfo(
                "{{PLUGIN_TITLE}}", "A request is already running."
            )
            return

        self.task = FetchTask("https://example.com/data.json")
        self.task.taskCompleted.connect(self.on_completed)
        self.task.taskTerminated.connect(self.on_terminated)
        QgsApplication.taskManager().addTask(self.task)

    def on_completed(self):
        if self.task is None:
            return
        length = len(self.task.result) if self.task.result else 0
        self.iface.messageBar().pushMessage(
            "{{PLUGIN_TITLE}}",
            f"Received {length} characters.",
            level=Qgis.MessageLevel.Success,
        )
        self.task = None

    def on_terminated(self):
        if self.task is None:
            return
        detail = self.task.error or "Request cancelled or failed."
        self.iface.messageBar().pushWarning("{{PLUGIN_TITLE}}", detail)
        self.task = None

    def unload(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None
        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.action.deleteLater()
            self.action = None
