# Processing Algorithms

Processing is the preferred pattern for input -> calculation -> output work.
It provides history, batch execution, the Model Designer, and `qgis_process`
without a custom UI.

## Provider and algorithm

A plugin registers a `QgsProcessingProvider`; the provider exposes one or more
`QgsProcessingAlgorithm` subclasses.

```python
from qgis.core import QgsProcessingProvider

class MyProvider(QgsProcessingProvider):
    def id(self):
        return "my_plugin"

    def name(self):
        return "My Plugin"

    def loadAlgorithms(self):
        self.addAlgorithm(MyAlgorithm())
```

Register the provider in `initGui()` and remove it in `unload()`:

```python
from qgis.core import QgsApplication

QgsApplication.processingRegistry().addProvider(self.provider)
QgsApplication.processingRegistry().removeProvider(self.provider)
```

## Algorithm contract

Implement at least:

- `name()`: stable lowercase identifier.
- `displayName()`: user-visible name.
- `group()` and `groupId()`.
- `initAlgorithm()`: declare parameters and outputs.
- `processAlgorithm()`: read inputs, write outputs, return result map.
- `shortHelpString()`: explain inputs, outputs, and limitations.

```python
from qgis.core import (
    QgsFeatureSink,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
)

class MyAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self):
        return "my_algorithm"

    def displayName(self):
        return "My algorithm"

    def group(self):
        return "My Plugin"

    def groupId(self):
        return "my_plugin"

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        sink, dest_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs(),
        )
        for feature in source.getFeatures():
            if feedback.isCanceled():
                break
            sink.addFeature(feature, QgsFeatureSink.Flag.FastInsert)
        return {self.OUTPUT: dest_id}
```

The exact sink signature depends on the QGIS version. Verify it against the
target API.

## Parameters

Common parameter types:

- `QgsProcessingParameterFeatureSource`
- `QgsProcessingParameterFeatureSink`
- `QgsProcessingParameterField`
- `QgsProcessingParameterDistance`
- `QgsProcessingParameterNumber`
- `QgsProcessingParameterBoolean`
- `QgsProcessingParameterEnum`
- `QgsProcessingParameterString`

Use `QgsProcessingParameterDefinition.Flag` for advanced or hidden parameters.

## Feedback and cancellation

- Call `feedback.isCanceled()` in every long loop.
- Call `feedback.setProgress(value)` for long operations.
- Do not touch widgets, the canvas, or the message bar from a background
  Processing thread. Use `feedback.pushInfo()` and `feedback.pushWarning()`.

## Flags

Use scoped flags:

```python
def flags(self):
    return super().flags() | QgsProcessingAlgorithm.Flag.FlagNoThreading
```

Only disable threading when the algorithm truly requires the main thread.

## Testing

Static validation is not enough. Test the algorithm with the QGIS Python
interpreter:

```python
from qgis.core import QgsApplication
from qgis.analysis import QgsNativeAlgorithms
import processing

app = QgsApplication([], False)
app.initQgis()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
# Register the plugin provider, then run processing.run(...)
```

For headless checks, use `qgis_process` when available. Record whether the
algorithm was actually executed or only statically validated.
