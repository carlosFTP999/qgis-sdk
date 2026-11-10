from qgis.core import (
    QgsFeature,
    QgsFeatureSink,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
)


class {{ALGORITHM_CLASS}}(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    DISTANCE = "DISTANCE"
    OUTPUT = "OUTPUT"

    def name(self):
        return "{{ALGORITHM_ID}}"

    def displayName(self):
        return "{{PLUGIN_TITLE}} buffer"

    def group(self):
        return "Examples"

    def groupId(self):
        return "examples"

    def createInstance(self):
        return {{ALGORITHM_CLASS}}()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Input polygons",
                [QgsProcessing.TypeVectorPolygon],
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DISTANCE,
                "Distance in layer units",
                QgsProcessingParameterNumber.Double,
                defaultValue=100.0,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.OUTPUT, "Buffered polygons")
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT)
            )

        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
        sink, destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs(),
        )
        if sink is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.OUTPUT)
            )

        total = source.featureCount()
        for current, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                return {}

            geometry = feature.geometry()
            if geometry is None or geometry.isNull() or geometry.isEmpty():
                continue

            buffered = geometry.buffer(distance, 8)
            if buffered.isNull() or buffered.isEmpty():
                continue

            output = QgsFeature(source.fields())
            output.setGeometry(buffered)
            output.setAttributes(feature.attributes())
            if not sink.addFeature(output, QgsFeatureSink.FastInsert):
                raise QgsProcessingException("Could not write a feature.")

            if total > 0:
                feedback.setProgress(int(100 * (current + 1) / total))

        return {self.OUTPUT: destination_id}
