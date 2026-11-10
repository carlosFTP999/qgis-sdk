# Common QGIS 3 Plugin Errors

Most failures are QGIS 2 APIs, QGIS 4 spellings, a missing factory, or cleanup
that does not mirror setup. The "Wrong" lines are deliberate counterexamples;
do not copy them into a QGIS 3 plugin.

## QGIS 2 leftovers
```python
# Wrong: QgsMapLayerRegistry was removed in QGIS 3.
from qgis.core import QgsMapLayerRegistry
QgsMapLayerRegistry.instance().addMapLayer(layer)
qgis.open_raster("/data/dem.tif")  # not a QGIS 3 API
# Correct
from qgis.core import QgsProject, QgsRasterLayer
raster = QgsRasterLayer("/data/dem.tif", "DEM")
if raster.isValid():
    QgsProject.instance().addMapLayer(raster)
```

Use `QgsProject.instance()` for layers, and check `isValid()` before adding.

## Direct Qt imports
```python
# Wrong: QGIS 4 / Qt 6, then a direct PyQt5 import
from PyQt6.QtWidgets import QAction
from PyQt5.QtWidgets import QAction
# Correct: QGIS 3 / Qt 5 location
from qgis.PyQt.QtWidgets import QAction
```

In Qt 5, `QAction` is in `QtWidgets`; the `QtGui` location belongs to Qt 6.
## QGIS 4 enum spellings
```python
# Wrong for the 3.16 baseline
level = Qgis.MessageLevel.Warning
area = Qt.DockWidgetArea.RightDockWidgetArea
# Correct
level = Qgis.Warning
area = Qt.RightDockWidgetArea
```

QGIS 3.16 exposes bare enum constants through SIP; later 3.x builds may accept
both spellings, but do not rely on that.
## `QMetaType` in a field definition
```python
# Wrong: QGIS 4
from qgis.PyQt.QtCore import QMetaType
field = QgsField("area", QMetaType.Type.Double)
# Correct
from qgis.PyQt.QtCore import QVariant
field = QgsField("area", QVariant.Double, "double", 10, 2)
```

QGIS 3 field types are `QVariant` types. `QMetaType.Type.*` is QGIS 4 advice.
## `supportsQt6` in QGIS 3 metadata
```ini
# Wrong
[general]
qgisMinimumVersion=3.16
supportsQt6=True
# Correct: omit the key
[general]
qgisMinimumVersion=3.16
```

A QGIS 3 plugin must not claim Qt 6 support. QGIS 4 removed `supportsQt6`
entirely, so it is not current guidance for either version.
## Missing `classFactory`

An empty `__init__.py` is not loadable. Correct:

```python
def classFactory(iface):
    from .plugin import MyPlugin
    return MyPlugin(iface)
```

Keep the import inside the function so a broken optional dependency fails with
a readable traceback.
## Asymmetric unload
Setup that adds a menu action but `unload()` returns `pass` duplicates the
action after a reload. Correct:

```python
def unload(self):
    if self.action is not None:
        self.iface.removePluginMenu("&My Plugin", self.action)
        self.iface.removeToolBarIcon(self.action)
        self.action.deleteLater()
        self.action = None
```

Apply the same rule to docks, map tools, providers, timers, tasks, and signals.
See `plugin-structure.md`.
## CRS not checked
```python
# Wrong: degrees when the layer is EPSG:4326
length = feature.geometry().length()
# Correct
from qgis.core import QgsDistanceArea, QgsProject
measure = QgsDistanceArea()
measure.setSourceCrs(layer.crs(), QgsProject.instance().transformContext())
measure.setEllipsoid("WGS84")
length_m = measure.measureLength(feature.geometry())
```

A length in degrees is not a length in metres. Transform first, or measure with
`QgsDistanceArea` and state the units.
## UI work from a worker thread
```python
# Wrong: run() is not the GUI thread
class MyTask(QgsTask):
    def run(self):
        self.iface.messageBar().pushMessage("Done")
        return True
# Correct
class MyTask(QgsTask):
    def run(self):
        self.result = "result"
        return True

    def finished(self, result):
        if result:
            self.iface.messageBar().pushMessage("My Plugin", "Done", Qgis.Info, 5)
```

`finished()` is in the GUI thread; `run()` is not. See
`signals-and-tasks.md`.
## Logging and packaging residue
```python
# Wrong: invisible to QGIS users
print("loaded")
# Correct
from qgis.core import QgsMessageLog, Qgis
QgsMessageLog.logMessage("loaded", "MyPlugin", Qgis.Info)
```

Wrong: `PLUGIN_NAME = "{{PLUGIN_NAME}}"`. Correct: replace every marker before
validation, for example `PLUGIN_NAME = "My Plugin"`.

Wrong: `icon=icons/icon.png` when that file is not in the ZIP. Correct: keep
`icon.png` at the plugin root and declare `icon=icon.png`; confirm with
`unzip -l`. A plugin can install and still show a broken image.

## Static validation is not runtime proof

The validator checks structure, syntax, and QGIS 3 rules. It does not import
the plugin in QGIS. Report `runtime not tested` if you did not load it in a
QGIS 3 profile; see `checklist.md` and `testing-and-ci.md`.

## Sources

- PyQGIS master API, `Qgis`:
  https://qgis.org/pyqgis/master/core/Qgis.html
- PyQGIS master API, `QgsWkbTypes`:
  https://qgis.org/pyqgis/master/core/QgsWkbTypes.html
