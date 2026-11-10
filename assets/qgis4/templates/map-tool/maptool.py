from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtCore import Qt


class PointTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.setCursor(Qt.CursorShape.CrossCursor)
