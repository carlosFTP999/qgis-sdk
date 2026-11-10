# UI, Actions, Dialogs, and Dock Widgets

QGIS 3 uses Qt 5 through `qgis.PyQt`. Build the UI on the GUI thread, parent
every dialog and dock to the QGIS main window, and remove every object in `unload()`.

## Actions, menus, and toolbars

```python
from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


def initGui(self):
    self.action = QAction(
        QIcon(str(Path(__file__).parent / "icon.png")),
        "Run",
        self.iface.mainWindow(),
    )
    self.action.triggered.connect(self.run)
    self.iface.addPluginToMenu("&My Plugin", self.action)
    self.iface.addToolBarIcon(self.action)
```

In Qt 5, `QAction` lives in `qgis.PyQt.QtWidgets`. Qt 6 moved it to `QtGui`;
that QGIS 4 import is not available on the 3.16 baseline.

```python
def unload(self):
    if self.action is not None:
        self.iface.removePluginMenu("&My Plugin", self.action)
        self.iface.removeToolBarIcon(self.action)
        self.action.deleteLater()
        self.action = None
```

Keep the action on `self`; a local-only action can be garbage-collected.

## Dialogs and parent widgets

```python
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout


class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("My Plugin options")
        layout = QVBoxLayout(self)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
```

Create it with the QGIS window as parent and use `exec_()` in PyQt5:

```python
dialog = OptionsDialog(self.iface.mainWindow())
if dialog.exec_() == QDialog.Accepted:
    self.apply_options(dialog)
```

`exec_()` is the PyQt5 spelling used by QGIS 3; `exec()` also exists in PyQt5,
but keeping `exec_()` avoids mixing QGIS 4 snippets into a 3.x plugin. A
modeless dialog must stay referenced (`self.dialog = ...`) and close in `unload()`.

## Layer and field combo boxes

```python
from qgis.core import QgsFieldProxyModel, QgsMapLayerProxyModel, QgsVectorLayer
from qgis.gui import QgsFieldComboBox, QgsMapLayerComboBox


self.layer_combo = QgsMapLayerComboBox(self)
self.layer_combo.setFilters(QgsMapLayerProxyModel.VectorLayer)
self.layer_combo.setAllowEmptyLayer(True)
self.field_combo = QgsFieldComboBox(self)
self.field_combo.setFilters(QgsFieldProxyModel.Numeric)
self.layer_combo.layerChanged.connect(self.sync_fields)
self.sync_fields(self.layer_combo.currentLayer())
```

```python
def sync_fields(self, layer):
    self.field_combo.setLayer(layer if isinstance(layer, QgsVectorLayer) else None)
```

`QgsMapLayerProxyModel.VectorLayer` is the 3.16 filter constant. Do not pass
`QgsMapLayer.VectorLayer`: it is a layer-type enum whose value is `0` here,
which means no filter.

## Dock widgets

```python
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QLabel, QVBoxLayout, QWidget
from qgis.gui import QgsDockWidget


self.dock = QgsDockWidget("My Panel", self.iface.mainWindow())
self.dock.setObjectName("MyPluginDock")
panel = QWidget(self.dock)
layout = QVBoxLayout(panel)
layout.addWidget(QLabel("Choose a layer, then run.", panel))
self.dock.setWidget(panel)
self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
```

Set `objectName` before adding the dock so QGIS can restore its position.
Remove and destroy it symmetrically:

```python
if self.dock is not None:
    self.iface.removeDockWidget(self.dock)
    self.dock.deleteLater()
    self.dock = None
```

Keep the dock on `self`; QGIS owns the panel once set. Clean signals in the same path.

## Other native widgets

Use `QgsFileWidget` (`GetDirectory` for folders, `SaveFile` for outputs),
`QgsColorButton`, and `QgsUnitSelectionWidget` for units. Show message-bar
feedback with `Qgis.Info` on the GUI thread only, with an explicit duration.

## Avoid UI work in callbacks

Widget signals already run on the GUI thread, but a long callback freezes QGIS.
Do the work in a `QgsTask` and update the widget from `finished()`; see
`signals-and-tasks.md`. For a modal dialog triggered from a map-tool
callback, defer it with `QTimer.singleShot(0, self.show_dialog)`.

## Internationalization

Wrap visible strings in `self.tr()` or `QCoreApplication.translate()`. Translation
is a build pipeline, not an empty scaffold:

```text
i18n/*.pro --pylupdate5--> *.ts --lrelease--> *.qm
```

List sources and forms in the `.pro` file, run `pylupdate5`, translate the `.ts`
files in Qt Linguist, then run `lrelease` to produce the `.qm` file that ships.
See `pyqt5-tooling.md` for the commands and a complete `.pro` example.

QGIS core does not install plugin translators. The recommended plugin-side
pattern is to create a `QTranslator`, load the matching `.qm`, install it, and
remove it in `unload()`:

```python
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, QTranslator
from qgis.core import QgsSettings


def initGui(self):
    self.translator = None
    locale = QgsSettings().value("locale/userLocale", "en")[:2]
    qm_path = Path(__file__).parent / "i18n" / f"contour_helper_{locale}.qm"
    if qm_path.exists():
        translator = QTranslator()
        if translator.load(str(qm_path)):
            QCoreApplication.installTranslator(translator)
            self.translator = translator


def unload(self):
    if getattr(self, "translator", None) is not None:
        QCoreApplication.removeTranslator(self.translator)
        self.translator = None
```

An empty or untranslated `.ts` file is not a completed translation setup. Keep
the `.ts` sources in the repository and ship the compiled `.qm` files.

## UI cleanup checklist

- [ ] Actions are on `self`, removed from menu and toolbar, then deleted.
- [ ] Docks are removed, deleted, and dereferenced.
- [ ] Dialogs have `iface.mainWindow()` as parent.
- [ ] Layer combos use `QgsMapLayerProxyModel` filters.
- [ ] The field combo follows the selected layer.
- [ ] No widget is touched from `QgsTask.run()`.
- [ ] Visible strings use `self.tr()` or `QCoreApplication.translate()`.
- [ ] `.qm` files are built from translated `.ts` files, not empty scaffolding.
- [ ] The installed `QTranslator` is removed in `unload()`.
- [ ] `unload()` is safe after a partial `initGui()`.

See `plugin-structure.md` for `initGui`/`unload` symmetry and
`pyqt5-tooling.md` for `.ui` files and the `.pro`/`pylupdate5`/
`lrelease` pipeline.
