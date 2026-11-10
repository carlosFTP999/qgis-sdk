# PyQt5 Tooling

QGIS 3 ships a Qt binding and a Python runtime. The plugin must use the binding
that QGIS provides, not one installed separately into the virtual environment.

## Purpose

Use this reference to import Qt through `qgis.PyQt`, run tests with the QGIS
interpreter or a QGIS-derived virtual environment, and configure ruff, mypy,
pytest, and pre-commit without adding a runtime Qt dependency.

## Import rule and dialogs

```python
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtWidgets import QAction, QDialog
from qgis.core import Qgis, QgsMessageLog

dialog = QDialog(iface.mainWindow())
dialog.setWindowTitle("Contour Helper")
if dialog.exec_() == QDialog.Accepted:
    QgsMessageLog.logMessage("Confirmed", "Contour Helper", Qgis.Info)
```

In QGIS 3/PyQt5, `QAction` lives in `QtWidgets`, not `QtGui`. `QVariant` lives in
`QtCore`. Enum members are unscoped: `Qt.RightDockWidgetArea`,
`QDialog.Accepted`, and `QMessageBox.Yes`. Use `exec_()` for modal dialogs.

Never import the Qt binding directly. A plugin that does so breaks when QGIS
loads it where the binding is not a top-level package, and it can mix two
bindings in one process.

## Environment

Use the Python interpreter bundled with the target QGIS, or a virtual
environment created from it. On Windows, use the OSGeo4W shell and its
`python-qgis` launcher; on Linux, use the distribution Python that can import
`qgis.core`; on macOS, use the interpreter inside the QGIS application bundle.
Paths differ between QGIS 3.x releases and installers.

`qgis-venv-creator` is an external tool. Install it by its own documented
method, follow its README for the current invocation, and use the interpreter it
produces. It is not vendored here, is not a plugin dependency, and its flags may
change. Verify the result:

```bash
python -c "from qgis.core import Qgis; assert Qgis.QGIS_VERSION.startswith('3.')"
```

Do not install the Qt binding or PyQGIS from PyPI into the project environment.
A second binding on `sys.path` causes import errors, missing platform plugins,
and crashes that only appear inside QGIS.

## pyproject.toml

```toml
[project]
name = "contour-helper"
version = "0.1.0"
requires-python = ">=3.8"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7", "ruff>=0.6", "mypy>=1.10", "pre-commit>=3.7"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py38"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B"]

[tool.mypy]
python_version = "3.8"
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = ["qgis.*", "osgeo.*", "processing"]
ignore_missing_imports = true
```

The file configures tools and development metadata; it does not add runtime
dependencies to the plugin. Keep runtime dependencies empty and do not add
`PyQt5`, `qgis`, or `osgeo` there. Set
`python_version` and `target-version` to the oldest interpreter the plugin
supports. QGIS 3.16-era installations may run Python 3.8 or 3.9 depending on the
platform, so confirm the target.

## Type checking notes

`qgis.*` and `osgeo.*` do not ship PEP 561 type information, so mypy reports
missing imports unless they are excluded per module, as above. Keep plugin logic
in typed functions and isolate calls into those packages behind small adapters;
the untyped objects become `Any` at the boundary.

`osgeo` is only needed for GDAL/OGR work. Import it inside the function that
needs it, so a normal plugin start does not depend on GDAL Python bindings. Do
not add editor-only stubs that bring the Qt binding into runtime dependencies;
if stubs are used, keep them in the development group and verify imports still
resolve to `qgis.PyQt`.

## Tests

```python
import pytest


@pytest.fixture(scope="session")
def qgis_app():
    pytest.importorskip("qgis.core", reason="QGIS bindings are not importable")
    from qgis.core import QgsApplication

    app = QgsApplication([], False)
    app.initQgis()
    yield app
    app.exitQgis()
```

Run headless tests with the offscreen platform:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest
```

Tests that import `qgis.core` cannot run under a plain Python interpreter
without PyQGIS. Mark QGIS-dependent tests and state in CI which QGIS version
supplied the runtime. Static checks and QGIS execution are different evidence.

## Internationalization

Translation is a build pipeline, not an empty scaffold:

```text
i18n/*.pro --pylupdate5--> *.ts --lrelease--> *.qm
```

1. List the plugin sources and `.ui` forms in an `i18n/*.pro` file.
2. Run `pylupdate5` on the `.pro` file to generate or update the `.ts` files.
3. Translate the `.ts` files in Qt Linguist.
4. Run `lrelease` on each `.ts` file to produce the `.qm` file that ships.

```pro
# i18n/contour_helper.pro
FORMS = ../ui/dialog.ui
SOURCES = ../plugin.py ../ui/dialog.py
TRANSLATIONS = contour_helper_es.ts
```

```bash
pylupdate5 i18n/contour_helper.pro
lrelease i18n/contour_helper_es.ts
```

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

## Pre-commit

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
      - id: ruff-format
```

Pin every hook revision and update it deliberately. Pre-commit runs in an
isolated environment; it must not need QGIS or the Qt binding.

## Pitfalls

- Installing the Qt binding from PyPI and shadowing the one QGIS uses.
- Running pytest with an interpreter that cannot import `qgis.core`.
- Forgetting `QT_QPA_PLATFORM=offscreen`, so tests fail without a display.
- Importing `QAction` from `QtGui` because a Qt 6 example was copied.
- Using scoped enum spellings and `exec()` where PyQt5 expects unscoped members
  and `exec_()`.
- Adding `qgis`, `osgeo`, or the Qt binding to runtime dependencies.
- Treating a ruff or mypy pass as runtime verification.

Related: `plugin-structure.md`, `pyqgis-core.md`, `ui-dockwidgets.md`.
