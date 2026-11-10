from qgis.core import (
    Qgis,
    QgsFeature,
    QgsFeatureSink,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
)


class BufferAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    DISTANCE = "DISTANCE"
    OUTPUT = "OUTPUT"

    def name(self):
        return "{{PLUGIN_NAME}}_buffer"

    def displayName(self):
        return "Buffer features"

    def group(self):
        return "{{PLUGIN_TITLE}}"

    def groupId(self):
        return "{{PLUGIN_NAME}}"

    def shortHelpString(self):
        return "Create a polygon buffer around every input feature."

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.INPUT, "Input layer")
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.DISTANCE,
                "Buffer distance",
                defaultValue=10.0,
                parentParameterName=self.INPUT,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, "Buffered layer")
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException("A vector input layer is required.")

        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
        sink, destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            Qgis.GeometryType.Polygon,
            source.sourceCrs(),
        )
        if sink is None:
            raise QgsProcessingException("Could not create the output layer.")

        total = max(source.featureCount(), 1)
        for index, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break

            geometry = feature.geometry()
            if geometry.isNull() or geometry.isEmpty():
                continue

            buffered = QgsFeature(feature)
            buffered.setGeometry(geometry.buffer(distance, 8))
            sink.addFeature(buffered, QgsFeatureSink.Flag.FastInsert)
            feedback.setProgress(int((index + 1) * 100 / total))

        return {self.OUTPUT: destination_id}
