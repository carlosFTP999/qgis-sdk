# Plugin Structure and Lifecycle

QGIS loads a plugin through `classFactory(iface)`, creates the returned plugin
object, calls `initGui()`, and later calls `unload()`. That lifecycle can repeat
without restarting QGIS, so every resource created in `initGui()` must be
released in `unload()`.

## Purpose

Use this reference to shape the plugin package, write a safe `classFactory`, and
keep menu actions, toolbars, dock widgets, map tools, and Processing providers
symmetric across reloads.

## Package layout

```text
contour_helper/
├── __init__.py          # classFactory only
├── metadata.txt
├── plugin.py            # plugin object and lifecycle
├── icon.png
├── algorithms/
│   ├── __init__.py
│   └── buffer.py
└── ui/
    ├── __init__.py
    └── dialog.py
```

The package name is the importable name and the folder QGIS installs. Keep
`__init__.py` small: QGIS imports it before it knows whether the rest of the
plugin can load.

## classFactory

```python
# contour_helper/__init__.py
def classFactory(iface):
    from .plugin import ContourHelperPlugin

    return ContourHelperPlugin(iface)
```

Keep the import inside the function. A syntax error in `plugin.py` then produces
a plugin load error that names the plugin, instead of breaking package import
before QGIS can report which plugin failed.

## Minimal complete example

```python
# contour_helper/plugin.py
from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import Qgis, QgsMessageLog


class ContourHelperPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        self.action = QAction("Contour Helper", self.iface.mainWindow())
        self.action.setIcon(QIcon(str(Path(__file__).with_name("icon.png"))))
        self.action.setStatusTip("Run the contour helper")
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&Contour Helper", self.action)
        self.iface.addToolBarIcon(self.action)

    def run(self):
        QgsMessageLog.logMessage("Contour Helper started", "Contour Helper", Qgis.Info)

    def unload(self):
        if self.action is not None:
            self.iface.removePluginMenu("&Contour Helper", self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action.triggered.disconnect()
            self.action.deleteLater()
            self.action = None
```

The menu label passed to `addPluginToMenu()` and `removePluginMenu()` must be
identical. Keep action creation and registration in one place so a reload cannot
create a second entry.

## What unload must release

| Created in initGui | Released in unload |
|---|---|
| `QAction` | Remove from menu/toolbar, disconnect, `deleteLater()` |
| Dock widget | `removeDockWidget()`, disconnect, `deleteLater()` |
| Map tool | Unset from canvas if active, disconnect, drop reference |
| Processing provider | `processingRegistry().removeProvider(provider)` |
| Project or layer signals | `disconnect()` from the same signal |
| `QgsTask` | Cancel, disconnect callbacks, then drop the reference |
| Timer or network reply | Stop/abort, disconnect, drop reference |

`unload()` may run after a partially failed `initGui()`. Guard every optional
attribute with `None` checks and keep cleanup idempotent.

## Optional Processing provider

Register a provider only when the plugin owns algorithms:

```python
from qgis.core import QgsApplication

from .provider import ContourProvider


class ContourHelperPlugin:
    # ... existing __init__ and other methods ...

    def initGui(self):
        self.provider = ContourProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        if getattr(self, "provider", None) is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
```

Add these provider calls to the existing `initGui()` and `unload()`; keep the
action cleanup from the minimal example. Add `hasProcessingProvider=yes` to
`metadata.txt`. Removing the provider in `unload()` prevents duplicate algorithm
entries when QGIS reloads the plugin. See `processing-algorithms.md` for the
provider and algorithm contract.

## Reload safety

QGIS can disable and re-enable a plugin, and development tools can reload Python
modules. Treat the plugin object as the owner of all runtime state:

- Store actions, docks, tools, and providers on `self`, not in module globals.
- Do not connect a signal twice. Connect in `initGui()` and disconnect in
  `unload()`.
- Do not leave a dialog, message bar item, or task holding a reference to the
  plugin after `unload()`.
- Do not assume `initGui()` runs only once for the lifetime of the process.
- Avoid doing work in `__init__()`. Create expensive objects in `initGui()` and
  release them in `unload()`.

## Pitfalls

- Duplicate menu or toolbar entries after a reload: the old action was not
  removed or disconnected.
- `removePluginMenu()` with a different label than `addPluginToMenu()`.
- Deleting the action before removing it from the interface.
- Creating a Processing provider in `__init__()` and never removing it.
- Leaving a map tool active after unload.
- Connecting a project signal in a helper but disconnecting only the plugin
  object's signal, so the helper stays alive.
- Showing a modal dialog from `initGui()` and blocking QGIS startup.

## Sources

- QGIS 3.40 PyQGIS cookbook, plugins:
  https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/plugins/plugins.html
- QGIS 3.44 PyQGIS cookbook, plugin metadata table:
  https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#metadata-txt

Related: `metadata-qgis3.md`, `processing-algorithms.md`, `pyqgis-core.md`.
