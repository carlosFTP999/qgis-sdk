# UI, Dialogs, and Dock Widgets

QGIS plugins should use native QGIS widgets where possible and must remove
every UI object they add during `unload()`.

## Actions

```python
from qgis.PyQt.QtGui import QAction

self.action = QAction("Run", self.iface.mainWindow())
self.action.triggered.connect(self.run)
self.iface.addPluginToMenu("&My Plugin", self.action)
```

In `unload()`:

```python
self.iface.removePluginMenu("&My Plugin", self.action)
self.action.deleteLater()
self.action = None
```

## Dialogs

Use code-defined dialogs or `.ui` files consistently. For code-defined UI, set
the parent so the dialog is owned by the QGIS window.

```python
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
```

Prefer `exec()` in PyQt6. `exec_()` is legacy.

## QGIS widgets

- `QgsMapLayerComboBox` for layer selection.
- `QgsFieldComboBox` for fields.
- `QgsFileWidget` for files and directories.
- `QgsColorButton` for colors.
- `QgsUnitSelectionWidget` for units.
- `QgsMessageBar` for short feedback.

Filter layer combos to the accepted types:

```python
from qgis.core import Qgis

self.layer_combo.setFilters(Qgis.LayerFilter.VectorLayer)
```

## Dock widgets

```python
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsDockWidget

self.dock = QgsDockWidget("My Panel", self.iface.mainWindow())
self.dock.setWidget(MyPanel(self.iface))
self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
```

Remove it in `unload()`:

```python
self.iface.removeDockWidget(self.dock)
self.dock.deleteLater()
self.dock = None
```

Keep a reference to the dock and panel; a local variable can be garbage
collected and disappear.

## UI thread

Do not run network calls, large loops, or layer edits from a widget callback.
Start a `QgsTask` and update the UI from its `finished` signal.

## Internationalization

Wrap visible strings in `self.tr()` or `QCoreApplication.translate()`. Keep the
source language consistent with the project. Do not hardcode a language that
the project did not request.

Translation is a build pipeline, not an empty scaffold:

1. List sources and forms in an `i18n/*.pro` file.
2. Run `pylupdate6` on the `.pro` file to generate or update the `.ts` files.
3. Translate the `.ts` files in Qt Linguist.
4. Run `lrelease` on each `.ts` file to produce the `.qm` file that ships.

The update and release binaries come from the Qt toolchain; use the names that
match the Qt version QGIS provides.

QGIS core does not install plugin translators. The recommended plugin-side
pattern is to create a `QTranslator`, load the matching `.qm`, install it, and
remove it in `unload()`:

```python
import os

from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.core import QgsSettings

def initGui(self):
    self.translator = None
    locale = QgsSettings().value("locale/userLocale", "en")[:2]
    qm_path = os.path.join(
        os.path.dirname(__file__), "i18n", f"my_plugin_{locale}.qm"
    )
    if os.path.exists(qm_path):
        translator = QTranslator()
        if translator.load(qm_path):
            QCoreApplication.installTranslator(translator)
            self.translator = translator

def unload(self):
    if getattr(self, "translator", None) is not None:
        QCoreApplication.removeTranslator(self.translator)
        self.translator = None
```

An empty or untranslated `.ts` file is not a completed translation setup. Keep
the `.ts` sources in the repository and ship the compiled `.qm` files.

## UI checklist

- [ ] Every action is removed in `unload()`.
- [ ] Every dock is removed in `unload()`.
- [ ] Dialogs have a parent.
- [ ] Layer and field widgets are filtered correctly.
- [ ] No long work runs in the GUI thread.
- [ ] Visible strings use the project translation path.
- [ ] `.qm` files are built from translated `.ts` files, not empty scaffolding.
- [ ] The installed `QTranslator` is removed in `unload()`.
- [ ] No widget is touched from a background task.

## Sources

- PyQGIS master API, `Qgis` (`LayerFilter`):
  https://qgis.org/pyqgis/master/core/Qgis.html
