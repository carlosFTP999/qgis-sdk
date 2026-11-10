# Common Errors

## Direct Qt imports

Wrong:

```python
from PyQt6.QtWidgets import QAction
```

Correct:

```python
from qgis.PyQt.QtGui import QAction
```

## Unscoped enums

Wrong:

```python
Qgis.Info
Qt.Checked
QgsWkbTypes.Point
QgsFeatureSink.FastInsert
```

Correct:

```python
Qgis.MessageLevel.Info
Qt.CheckState.Checked
QgsWkbTypes.Type.Point
QgsFeatureSink.Flag.FastInsert
```

`QgsGeometry.type()` returns a geometry-group value; compare it with
`Qgis.GeometryType.Point`. WKB values such as `QgsWkbTypes.Point` use
`QgsWkbTypes.Type.*`; the older `QgsWkbTypes.PolygonGeometry` alias maps to
`Qgis.GeometryType.Polygon`. Scoped `GeometryType` members are `Point`, `Line`,
`Polygon`, `Unknown`, and `Null`; `*Geometry` names are old unscoped
compatibility aliases, not scoped members.

## `QVariant` field types

Wrong:

```python
QgsField("area", QVariant.Double)
```

Correct:

```python
from qgis.PyQt.QtCore import QMetaType

QgsField("area", QMetaType.Type.Double)
```

## Missing `classFactory`

QGIS cannot load the plugin if `__init__.py` does not expose `classFactory`.
Keep the plugin import inside the factory to avoid eager optional imports.

## Asymmetric lifecycle

A plugin that adds a menu action but does not remove it duplicates the action
after reload. The same applies to docks, map tools, providers, timers, signals,
and tasks.

## GUI access from a task

`QgsTask.run()` is not the GUI thread. Do not touch widgets, the canvas, the
message bar, or vector layers from it. Return a result and update the UI in
`finished()`.

## CRS mismatch

Distance and area values are meaningless when layers use different CRS. Check
validity and transform before measuring.

## Missing icon

`metadata.txt` declares `icon=icon.png` but the file is missing, outside the
plugin root, or excluded from the ZIP. The plugin may install but show a broken
icon.

## Unreplaced placeholders

Template output still contains `{{PLUGIN_NAME}}` or another marker. Replace all
placeholders before validation.

## ZIP with the wrong root

A ZIP that contains a wrapper directory above the plugin root may install the
wrong folder structure. Keep one plugin root with `metadata.txt` at its top.

## `print()` in a plugin

`print()` output is not visible to normal QGIS users and can pollute logs. Use
`QgsMessageLog` or `iface.messageBar()`.

## Stale provider

A Processing provider that is added but never removed remains registered after
the plugin unloads. Remove it in `unload()` and clear the reference.

## QAction garbage collection

A `QAction` created as a local variable can disappear. Keep it on `self` and
remove it in `unload()`.

## `exec_()` and legacy Qt APIs

Use `exec()` and current Qt APIs. Verify removed APIs against the target QGIS
version.

## Static validation is not runtime proof

The validator checks structure, syntax, and heuristics. It does not load the
plugin in QGIS. Report the difference explicitly.

## Sources

- PyQGIS master API, `Qgis`:
  https://qgis.org/pyqgis/master/core/Qgis.html
- PyQGIS master API, `QgsWkbTypes`:
  https://qgis.org/pyqgis/master/core/QgsWkbTypes.html
- QGIS 3.44 API, `QgsGeometry`:
  https://qgis.org/pyqgis/3.44/core/QgsGeometry.html
