# PyQGIS Core

This reference covers the QGIS objects used by most plugins. It is not a full
API manual. Verify exact signatures against the target QGIS version.

## Project and layers

```python
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer

project = QgsProject.instance()
layers = project.mapLayers().values()
active = project.layerTreeRoot().findLayers()

vector_layers = [
    layer for layer in layers
    if layer.type() == QgsMapLayer.LayerType.VectorLayer
]
```

Prefer the project model over legacy layer registries. Do not keep stale layer
references after a project closes.

## Active layer

```python
layer = self.iface.activeLayer()
if layer is None or layer.type() != QgsMapLayer.LayerType.VectorLayer:
    self.iface.messageBar().pushWarning("My Plugin", "Select a vector layer.")
    return
```

Check `None` and layer type before casting to `QgsVectorLayer`.

## Features and fields

```python
from qgis.core import QgsFeatureRequest

for feature in layer.getFeatures(QgsFeatureRequest()):
    geometry = feature.geometry()
    value = feature["name"]
```

Field access by name is convenient but can hide schema mistakes. For repeated
access, resolve field indexes with `layer.fields().indexOf("name")` and handle
`-1`.

## Editing

```python
layer.startEditing()
try:
    for feature in layer.getFeatures():
        layer.changeAttributeValue(feature.id(), field_index, value)
    if not layer.commitChanges():
        raise RuntimeError(layer.commitErrors())
except Exception:
    layer.rollBack()
    raise
```

Use `with edit(layer):` when the project uses the QGIS editing context manager.
Never leave an edit session open after an error.

## CRS

```python
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

source = layer.crs()
target = QgsCoordinateReferenceSystem("EPSG:3857")
transform = QgsCoordinateTransform(source, target, QgsProject.instance())
```

Check `source.isValid()` and `target.isValid()`. Transform geometries before
measuring distance or area in target units.

## Message logging

```python
from qgis.core import Qgis, QgsMessageLog

QgsMessageLog.logMessage("Started", "My Plugin", Qgis.MessageLevel.Info)
self.iface.messageBar().pushMessage(
    "My Plugin",
    "Finished",
    level=Qgis.MessageLevel.Success,
)
```

Use the log for diagnostics and the message bar for short user feedback. Do not
use `print()` in a plugin.

## Settings

```python
from qgis.core import QgsSettings

settings = QgsSettings()
settings.setValue("my_plugin/last_input", layer.id())
value = settings.value("my_plugin/last_input", "")
```

Namespace settings with the plugin name and provide defaults for missing keys.

## Tasks

Move long loops and network calls to a `QgsTask`. Read
`signals-and-tasks.md` before using threads.

## Common pitfalls

- Holding a layer reference after the project changes.
- Editing a layer from a background thread.
- Measuring in a source CRS with degrees.
- Assuming a field exists because it exists in the source dataset.
- Forgetting `feedback.isCanceled()` in a long Processing loop.
- Using `QVariant` for new fields.

## Sources

- PyQGIS master API, `Qgis`:
  https://qgis.org/pyqgis/master/core/Qgis.html
