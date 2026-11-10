from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
)


class LayerProcessor:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        layer = self.iface.activeLayer()
        if not isinstance(layer, QgsVectorLayer):
            self.iface.messageBar().pushWarning(
                "{{PLUGIN_TITLE}}", "Select a vector layer first."
            )
            return

        crs_id = layer.crs().authid()
        uri = "Point?crs=" + crs_id if crs_id else "Point"
        centroids = QgsVectorLayer(uri, "Centroids", "memory")
        if not centroids.isValid():
            self.iface.messageBar().pushCritical(
                "{{PLUGIN_TITLE}}", "Could not create the output layer."
            )
            return

        provider = centroids.dataProvider()
        provider.addAttributes(
            [
                QgsField("source_id", QVariant.LongLong),
                QgsField("x", QVariant.Double),
                QgsField("y", QVariant.Double),
            ]
        )
        centroids.updateFields()

        features = []
        for feature in layer.getFeatures():
            geometry = feature.geometry()
            if geometry is None or geometry.isEmpty():
                continue
            centroid = geometry.centroid()
            if centroid.isEmpty():
                continue
            point = centroid.asPoint()
            output = QgsFeature(centroids.fields())
            output.setGeometry(
                QgsGeometry.fromPointXY(QgsPointXY(point.x(), point.y()))
            )
            output.setAttributes([feature.id(), point.x(), point.y()])
            features.append(output)

        result = provider.addFeatures(features)
        success = result[0] if isinstance(result, tuple) else result
        if not success:
            self.iface.messageBar().pushCritical(
                "{{PLUGIN_TITLE}}", "Could not write the centroid features."
            )
            return

        centroids.updateExtents()
        QgsProject.instance().addMapLayer(centroids)
        self.iface.messageBar().pushInfo(
            "{{PLUGIN_TITLE}}", "Created {} centroids.".format(len(features))
        )
