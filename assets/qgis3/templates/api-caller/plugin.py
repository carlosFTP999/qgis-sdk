from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication

from .api_task import ApiTask


class {{PLUGIN_CLASS}}:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.task = None

    def initGui(self):
        self.action = QAction(
            QIcon(str(Path(__file__).with_name("icon.png"))),
            "{{MENU_TEXT}}",
            self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.start_fetch)
        self.iface.addPluginToMenu("&{{PLUGIN_TITLE}}", self.action)
        self.iface.addToolBarIcon(self.action)

    def start_fetch(self):
        if self.task is not None:
            self.iface.messageBar().pushWarning(
                "{{PLUGIN_TITLE}}", "A request is already running."
            )
            return

        task = ApiTask("{{API_URL}}")
        task.taskCompleted.connect(lambda: self.on_completed(task))
        task.taskTerminated.connect(lambda: self.on_terminated(task))
        self.task = task
        QgsApplication.taskManager().addTask(task)
        self.iface.messageBar().pushInfo(
            "{{PLUGIN_TITLE}}", "Request started."
        )

    def on_completed(self, task):
        if task is not self.task:
            return
        self.task = None
        payload = task.result
        if isinstance(payload, dict):
            detail = "{} keys".format(len(payload))
        elif isinstance(payload, list):
            detail = "{} items".format(len(payload))
        else:
            detail = type(payload).__name__
        self.iface.messageBar().pushInfo(
            "{{PLUGIN_TITLE}}", "Response received: " + detail
        )

    def on_terminated(self, task):
        if task is not self.task:
            return
        self.task = None
        detail = task.error or "The request was cancelled or failed."
        self.iface.messageBar().pushWarning("{{PLUGIN_TITLE}}", detail)

    def unload(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None
        if self.action is not None:
            self.iface.removePluginMenu("&{{PLUGIN_TITLE}}", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.triggered.disconnect()
            self.action.deleteLater()
            self.action = None
