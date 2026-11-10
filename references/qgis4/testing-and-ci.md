# Testing and CI (QGIS 4 / PyQt6)

QGIS 4 plugins run on PyQt6. Fast static tests need only Python; runtime tests
need the QGIS 4 Python bindings. A green static job does not prove the plugin
imports, registers a provider, or opens a dialog.

## Quick path

1. Keep metadata, ZIP-shape, and placeholder tests free of QGIS imports.
2. Run Processing tests through `qgis_process` with `QT_QPA_PLATFORM=offscreen`.
3. Run widget, dock, map-tool, and rendering tests under `xvfb-run`.
4. Enable the scoped `DeprecationWarning` gate in pytest.

## QgsApplication lifecycle

QGIS 4 keeps the same `QgsApplication` lifecycle as QGIS 3; only the Qt binding
changes (PyQt6 through `qgis.PyQt`).

```python
import os
import pytest


@pytest.fixture(scope="session")
def qgis_app():
    pytest.importorskip("qgis.core", reason="QGIS bindings are not importable")
    from qgis.core import QgsApplication

    prefix = os.environ.get("QGIS_PREFIX_PATH")
    if prefix:
        QgsApplication.setPrefixPath(prefix, True)
    app = QgsApplication([], False)  # no GUI: widgets are unavailable
    app.initQgis()
    try:
        yield app
    finally:
        app.exitQgis()
```

- Use one `QgsApplication` per process; do not re-initialize in every test.
- `QgsApplication([], False)` is headless and cannot create widgets. Widget
  tests need `QgsApplication([], True)` and a display.
- Run with the Python that ships with QGIS, or a venv bound by
  `qgis-venv-creator`. Do not `pip install qgis`; the bindings are compiled
  against a specific Python and Qt.
- On Windows use the QGIS launcher (`python-qgis.bat`); on Linux set
  `QGIS_PREFIX_PATH` or use the distro package.

## Headless split

| Test type | Entry point | Display |
|---|---|---|
| Processing / algorithms | `qgis_process` or in-process `QgsApplication` | `QT_QPA_PLATFORM=offscreen` |
| Dock widgets, dialogs, map tools, rendering | `pytest` with `QgsApplication([], True)` | `xvfb-run` virtual display |

```bash
# Processing only: no display needed.
QT_QPA_PLATFORM=offscreen pytest -q tests/test_algorithm.py

# Widgets and rendering: run under a virtual display.
xvfb-run -a pytest -q tests/test_dock.py
```

QGIS CI runs its GUI test suite with `xvfb-run ctest`; follow that practice for
any test that constructs widgets. `offscreen` is enough for `qgis_process`, but
it is not a full display for every GUI path, so do not assume a widget test
passes under it.

## Prefer qgis_process for Processing tests

`qgis_process` is the supported headless entry point for Processing. It runs
algorithms and models without starting QGIS Desktop, so it exercises provider
registration and execution through the public interface.

```bash
QT_QPA_PLATFORM=offscreen qgis_process run my_plugin:count -- INPUT=points.gpkg --json
```

- Only plugins that set `hasProcessingProvider=yes` in `metadata.txt` are
  recognized by `qgis_process`.
- Use `qgis_process list` to confirm the algorithm id, and `qgis_process help`
  for parameters.
- Prefer this over importing private modules or calling `processAlgorithm`
  directly.

## DeprecationWarning gate

Fail the suite when QGIS emits a deprecation warning, without failing on
unrelated third-party deprecations:

```toml
[tool.pytest.ini_options]
filterwarnings = [
  "error::DeprecationWarning:qgis.*",
]
```

Caveats:

- QGIS does not officially document that deprecated PyQGIS APIs emit Python
  `DeprecationWarning`. The category was observed on QGIS 3.40.6; if a future
  release changes it, the gate stops catching those warnings without error.
- `qgis.utils` installs a default warning filter when it is imported. Import
  order can weaken the gate, so import QGIS modules early and keep the rule in
  pytest configuration.
- `QgsMessageLog` entries are QGIS log messages, not Python warnings. The gate
  does not see them; assert on Processing feedback or log output instead.
- The `qgis.*` scope matches the module that emits the warning, not your plugin
  module. It is intentionally narrow; do not replace it with a blanket
  all-warnings error.

## Qt 6 resources

Qt 6 ships its resource compiler as the standalone `rcc` tool; there is no
PyQt-level `pyrcc`/`pyrcc6` entry point. Compile a `.qrc` file with Qt's `rcc`
instead:

```bash
rcc -g python -o resources.py resources.qrc
```

- On Windows, use the Qt 6 `rcc.exe` shipped with the QGIS install (typically
  under `apps/Qt6/bin`); the system `PATH` may not provide it.
- Prefer `QIcon` loaded from a plugin-relative path for a simple icon; a
  compiled resource is only needed when you must bundle many files.

```python
import os
from qgis.PyQt.QtGui import QIcon

icon = QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))
```

Keep the icon inside the plugin directory and declare it in `metadata.txt` when
the plugin uses one. See `qgis4-migration.md`.

## Optional: run inside QGIS manually

`qgis --nologo --code <script>` starts QGIS and runs a Python script, which is
useful for a manual smoke test on a desktop. Do not present it as the default
CI path: its display requirement is not documented, so it is unreliable on a
headless runner. Use `qgis_process` for Processing and `xvfb-run` for GUI tests.

## What static checks cannot prove

Ruff, type stubs, and the plugin validator cannot prove that `classFactory`
imports in QGIS 4, a scoped enum exists, a provider registers, a dock is
removed, a ZIP installs, or a map tool works. Report `runtime not tested` when
only static checks ran. See `checklist.md`.
