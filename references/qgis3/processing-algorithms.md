# Processing Algorithms

Processing is the preferred pattern for input -> calculation -> output work. It
provides a standard dialog, batch execution, history, Model Designer support,
and `qgis_process` integration without a custom UI.

## Purpose

Use this reference to register a QGIS 3.16+ provider, declare parameters, write
features to a sink, report progress, handle cancellation, and clean up on unload.

## Provider

```python
from qgis.core import QgsProcessingProvider

from .algorithms.buffer import BufferAlgorithm


class ContourProvider(QgsProcessingProvider):
    def id(self):
        return "contour_helper"

    def name(self):
        return "Contour Helper"

    def loadAlgorithms(self):
        self.addAlgorithm(BufferAlgorithm())
```

The provider `id()` is permanent and unique. It is half of the algorithm
identifier, for example `contour_helper:buffer_polygons`. `loadAlgorithms()` runs
whenever the provider is added, so create fresh algorithms there.

## Algorithm

```python
from qgis.core import (
    QgsFeature, QgsFeatureSink, QgsProcessing, QgsProcessingAlgorithm,
    QgsProcessingException, QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource, QgsProcessingParameterNumber,
)


class BufferAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    DISTANCE = "DISTANCE"
    OUTPUT = "OUTPUT"

    def name(self):
        return "buffer_polygons"

    def displayName(self):
        return "Buffer polygons"

    def group(self):
        return "Examples"

    def groupId(self):
        return "examples"

    def createInstance(self):
        return BufferAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.INPUT, "Input polygons", [QgsProcessing.TypeVectorPolygon]
        ))
        self.addParameter(QgsProcessingParameterNumber(
            self.DISTANCE, "Distance (layer units)",
            QgsProcessingParameterNumber.Double,
            defaultValue=100.0, minValue=0.0,
        ))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT, "Buffered polygons"
        ))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT))
        distance = self.parameterAsDouble(parameters, self.DISTANCE, context)
        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context,
            source.fields(), source.wkbType(), source.sourceCrs())
        if sink is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.OUTPUT))
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
        return {self.OUTPUT: dest_id}
```

`createInstance()` is required in QGIS 3 so batch and model execution can build
the algorithm. The result key must match the declared output name. The source is
read-only; write through the sink. For bulk output use
`sink.addFeatures(features, QgsFeatureSink.FastInsert)`.

## Parameters

`QgsProcessingParameterField("FIELD", "Field", "INPUT")` links a field to its
parent layer. Other common types are `QgsProcessingParameterNumber` (`.Double`
or `.Integer`), `QgsProcessingParameterDistance`,
`QgsProcessingParameterBoolean`, `QgsProcessingParameterEnum`, and
`QgsProcessingParameterString`. Advanced or hidden parameters use
`QgsProcessingParameterDefinition.FlagAdvanced` and `FlagHidden` before
`addParameter()`.

## Registration and cleanup

```python
from qgis.core import QgsApplication

self.provider = ContourProvider()
QgsApplication.processingRegistry().addProvider(self.provider)

if getattr(self, "provider", None) is not None:
    QgsApplication.processingRegistry().removeProvider(self.provider)
    self.provider = None
```

Set `hasProcessingProvider=yes` in `metadata.txt`. Removing the provider
prevents duplicate entries after a plugin reload.

## Cancellation and progress

- Call `feedback.isCanceled()` inside every long loop.
- Call `feedback.setProgress()` with an integer percentage.
- Use `feedback.pushInfo()`, `pushWarning()`, and `reportError()` instead of
  touching the message bar or a widget from `processAlgorithm()`.
- Return `{}` on cancellation; QGIS discards the partial result.
- Wrap expected failures in `QgsProcessingException` with a useful message.

If the algorithm must touch Qt objects on the main thread, return
`super().flags() | QgsProcessingAlgorithm.FlagNoThreading` from `flags()`.

## Pitfalls

- Calling `addFeatures()` on a `QgsProcessingFeatureSource`; it is read-only.
- Forgetting `createInstance()`, so batch or model execution cannot build it.
- Adding the provider twice, producing duplicate entries.
- Omitting `hasProcessingProvider=yes` from `metadata.txt`.
- Never checking `feedback.isCanceled()` in a long feature loop.
- Returning the wrong output key or omitting the output from the result dict.
- Declaring a sink geometry type or field schema that rejects the features.
- Touching widgets or the message bar from a background thread.
- Leaving the provider registered after plugin unload.
- Letting a generic exception escape without a Processing message.

Related: `plugin-structure.md`, `pyqgis-core.md`, `geometry-ops.md`.
