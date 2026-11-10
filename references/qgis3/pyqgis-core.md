# PyQGIS Core for QGIS 3

Most plugins read a project, inspect a vector layer, evaluate attributes, and
write a result. Use the QGIS 3 object model directly; the QGIS 2 layer registry
is gone.

## Purpose

Use this reference for the QGIS 3 APIs that appear in almost every plugin:
project and layer access, feature and field handling, editing, expressions,
selection, and CRS transforms.

## Project and layers

```python
from qgis.core import QgsProject, QgsVectorLayer

project = QgsProject.instance()
layers = project.mapLayers().values()
vector_layers = [layer for layer in layers if isinstance(layer, QgsVectorLayer)]
matches = project.mapLayersByName("Roads")
roads = matches[0] if matches else None
```

`QgsProject.instance()` is the live project. Do not cache a layer after the
project closes; listen to `project.layerWillBeRemoved` and drop references.
`QgsMapLayer.VectorLayer` is the QGIS 3 enum value, but `isinstance()` is clearer
when the next call needs a `QgsVectorLayer` API. For the active layer, check
`isinstance(self.iface.activeLayer(), QgsVectorLayer)` and `isValid()` before
reading it; the active layer can also be a raster or a broken provider.

## Features and fields

```python
from qgis.core import QgsFeatureRequest

layer = roads
fields = layer.fields()
name_index = fields.indexOf("name")
if name_index < 0:
    raise ValueError("Layer has no 'name' field")
request = QgsFeatureRequest().setSubsetOfAttributes(["name"], fields)
for feature in layer.getFeatures(request):
    label = feature.attribute(name_index)
```

Resolve field indexes once. `feature["name"]` is convenient, but a missing field
becomes a runtime surprise in a loop. `setSubsetOfAttributes()` reduces provider
work when only a few columns matter.

## Creating a memory layer

```python
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsProject, QgsVectorLayer,
)

layer = QgsVectorLayer("Point?crs=EPSG:4326", "Samples", "memory")
provider = layer.dataProvider()
provider.addAttributes([QgsField("name", QVariant.String), QgsField("value", QVariant.Double)])
layer.updateFields()
feature = QgsFeature(layer.fields())
feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(2.35, 48.85)))
feature.setAttribute(layer.fields().indexOf("name"), "Paris")
provider.addFeature(feature)
layer.updateExtents()
QgsProject.instance().addMapLayer(layer)
```

QGIS 3 field types come from `QVariant` in `qgis.PyQt.QtCore`. Use
`QVariant.Int`, `QVariant.String`, `QVariant.Double`, `QVariant.Date`,
`QVariant.DateTime`, `QVariant.Bool`, and `QVariant.LongLong` as needed. The
newer QGIS 4 field-type spelling does not exist here.

The Python binding for `QgsVectorDataProvider.addFeatures()` has changed across
3.x releases: older builds return a boolean, some newer builds return
`(success, features)`. Normalize the result when the plugin supports both:

```python
result = provider.addFeatures(features)
success = result[0] if isinstance(result, tuple) else result
if not success:
    raise RuntimeError("Could not add features")
```

## Editing features

```python
from qgis.core import edit

value_index = layer.fields().indexOf("value")
if value_index < 0:
    raise ValueError("Layer has no 'value' field")
with edit(layer):
    for feature in layer.getFeatures():
        current = feature.attribute(value_index)
        if current is None:
            continue
        if not layer.changeAttributeValue(feature.id(), value_index, current * 2):
            raise RuntimeError(f"Could not update feature {feature.id()}")
```

`edit()` rolls back on an exception and commits otherwise. If a provider rejects
the commit, inspect `layer.commitErrors()` instead of assuming data changed.

## Expressions

```python
from qgis.core import QgsExpression, QgsExpressionContext, QgsExpressionContextUtils

expression = QgsExpression('"population" / "area_km2"')
if expression.hasParserError():
    raise ValueError(expression.parserErrorString())
context = QgsExpressionContext()
context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
if not expression.prepare(context):
    raise ValueError(expression.evalErrorString())
for feature in layer.getFeatures():
    context.setFeature(feature)
    density = expression.evaluate(context)
    if expression.hasEvalError():
        raise ValueError(expression.evalErrorString())
```

Field names in expression strings use double quotes. Call `prepare()` once, then
set the feature on the context for each row. `$area` and `$length` follow project
measurement settings; use `QgsDistanceArea` when units must be explicit.

## Selection

```python
from qgis.core import QgsVectorLayer

layer.selectByExpression('"population" > 1000', QgsVectorLayer.SetSelection)
selected = layer.selectedFeatures()
layer.removeSelection()
self.iface.mapCanvas().refresh()
```

Selection lives on the layer, not on a copy of the features. Refresh the canvas
after changing it from a plugin action.

## CRS-aware operations

```python
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

source_crs = layer.crs()
target_crs = QgsCoordinateReferenceSystem("EPSG:3857")
if not source_crs.isValid() or not target_crs.isValid():
    raise ValueError("Cannot build a transform from an invalid CRS")
transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())
```

Build the transform once and reuse it. Transform geometries before measuring
distance, buffering, or overlaying layers with different CRSs. See
`geometry-ops.md` for geometry-level details.

## Logging

```python
from qgis.core import Qgis, QgsMessageLog

QgsMessageLog.logMessage("Started", "Contour Helper", Qgis.Info)
QgsMessageLog.logMessage("Layer is invalid", "Contour Helper", Qgis.Critical)
```

Use the unscoped QGIS 3 levels; `Qgis.Warning` is also available. Use
`iface.messageBar()` for short feedback and the log for diagnostics.

## Pitfalls

- Using the removed QGIS 2 layer registry; use `QgsProject.instance()`.
- Importing `QVariant` from `qgis.core` instead of `qgis.PyQt.QtCore`.
- Reading a field by name without checking `indexOf()` for `-1`.
- Editing without `with edit()` and leaving a session open after an error.
- Measuring or buffering in a geographic CRS and treating degrees as meters.
- Forgetting that expression field names need double quotes.
- Calling QGIS editing APIs from a background thread.

## Sources

- QGIS 3.40 PyQGIS cookbook, geometry handling:
  https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/geometry.html
- QGIS 3.44 API, `QgsGeometry`:
  https://qgis.org/pyqgis/3.44/core/QgsGeometry.html
- PyQGIS master API, `Qgis`:
  https://qgis.org/pyqgis/master/core/Qgis.html

Related: `geometry-ops.md`, `processing-algorithms.md`.
