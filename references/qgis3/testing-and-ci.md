# Testing and CI

A QGIS 3 plugin imports compiled bindings. Fast tests need only Python; runtime
tests need a QGIS installation. A green static job does not prove the plugin loads.

## Test layout

```text
my_plugin/   __init__.py, metadata.txt, plugin.py
tests/       conftest.py, test_metadata.py, test_algorithm.py
pyproject.toml
```

Keep `tests/` outside `my_plugin/`; it must not enter the release ZIP.

## pytest and ruff configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
markers = ["qgis: requires QGIS Python bindings and a QGIS runtime"]
filterwarnings = [
  "error::DeprecationWarning:qgis.*",
]

[tool.ruff]
line-length = 100
target-version = "py38"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
ignore = ["E501"]
```

Set `target-version` to the oldest supported Python; Ruff checks syntax and
imports, not whether `qgis.core` exposes an API.

## DeprecationWarning gate

Fail on QGIS deprecations without failing on unrelated warnings:

```toml
[tool.pytest.ini_options]
filterwarnings = [
  "error::DeprecationWarning:qgis.*",
]
```

Caveats:

- QGIS does not officially document that deprecated PyQGIS APIs emit Python
  `DeprecationWarning`; the category was observed on QGIS 3.40.6. If a release
  changes it, the gate stops catching those warnings.
- `qgis.utils` installs a default warning filter on import. Import order can
  weaken the gate; keep the rule in pytest configuration and import QGIS early.
- `QgsMessageLog` warnings are QGIS log messages, not Python warnings, so the
  gate does not see them.
- The `qgis.*` scope matches the emitting module. Do not turn this into a
  blanket all-warnings error.

## conftest.py with a QGIS fixture

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

Use one `QgsApplication` per process; a non-GUI application cannot create
widgets. Widget tests need `QgsApplication([], True)` and a display
(`xvfb-run` in CI).

## Fallback when QGIS is unavailable

```python
# tests/test_algorithm.py
import pytest

pytest.importorskip("qgis.core", reason="QGIS bindings are not importable")
pytestmark = pytest.mark.qgis


def test_algorithm_is_registered(qgis_app):
    from my_plugin.provider import Provider
    from qgis.core import QgsApplication
    provider = Provider()
    QgsApplication.processingRegistry().addProvider(provider)
    try:
        assert QgsApplication.processingRegistry().algorithmById("my_plugin:count")
    finally:
        QgsApplication.processingRegistry().removeProvider(provider)
```

`importorskip()` skips the module at collection time; it does not hide errors
inside tests that do run. Keep metadata, ZIP-shape, and placeholder tests free
of QGIS imports; read `metadata.txt` with `pathlib` and assert 3.x, no `supportsQt6`.

## QGIS virtual environment

QGIS bindings are built for a specific Python, not installed with `pip install
qgis`. Use the external `qgis-venv-creator` to bind a venv; do not vendor it.

```bash
# After qgis-venv-creator has created and activated the environment:
python -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
pytest -q
```

On Windows, prefer the QGIS launcher (`python-qgis.bat`) over a versioned path;
on Linux, distro packages and `QGIS_PREFIX_PATH` usually suffice.

## CI outline

```yaml
name: ci
on: [push, pull_request]
jobs:
  static:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install pytest ruff
      - run: ruff check . && pytest -q

  qgis:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        qgis: ["release-3_28", "release-3_40"]
    container: qgis/qgis:${{ matrix.qgis }}
    env:
      QT_QPA_PLATFORM: offscreen
    steps:
      - uses: actions/checkout@v4
      - run: python3 -m pip install pytest
      - run: python3 -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
      - run: pytest -q
```

Pin image tags that exist in your registry; tag names differ between mirrors.
If no image exists for the release named by `qgisMinimumVersion`, test that
release locally rather than silently replacing it with a newer one. The
container must expose QGIS Python, git, and pytest. Do not copy a versioned
Windows path; select the runtime through the image or `QGIS_PREFIX_PATH`.
Keep `QT_QPA_PLATFORM: offscreen` for Processing-only jobs; if the job runs
widget tests, wrap the pytest step with `xvfb-run -a`.

## Headless split: offscreen vs Xvfb

Keep `QT_QPA_PLATFORM: offscreen` for Processing and other headless checks; it
is the documented setting for `qgis_process` on a machine without a window
manager.

Widgets, dialogs, map tools, and rendering need a real display. Use `xvfb-run`
as the fallback: QGIS CI runs its GUI test suite with `xvfb-run ctest`.

```bash
# Processing / headless.
QT_QPA_PLATFORM=offscreen pytest -q tests/test_algorithm.py

# GUI / rendering fallback.
xvfb-run -a pytest -q tests/test_dock.py
```

`offscreen` alone is not a full display for every GUI path. Do not silently
skip a widget test because it happens to pass headless; run it under Xvfb or
report the limitation.

## Headless limits

- `QgsApplication([], False)` has no widgets; GUI classes fail without a
  `QApplication`. Use `QgsApplication([], True)` under `xvfb-run` when a GUI
  test is unavoidable; do not substitute `offscreen`.
- Rendering, font metrics, and some Processing algorithms differ without a
  display or with missing system fonts.
- Network-dependent providers and browser layers need fixtures or mocks.
- Test the QGIS 3.x release named by `qgisMinimumVersion` plus one current 3.x;
  a newer-build-only test is not a compatibility test. If CI lacks an image for
  the older release, run that check locally and say so.

## What static checks cannot prove

Ruff, mypy with `PyQt5-stubs`, and the plugin validator cannot prove that
`classFactory` imports in QGIS, an enum name exists in 3.16, a provider
registers, a dock is removed, a ZIP installs, or a map tool works. Report
`runtime not tested` when only these checks ran. See
`checklist.md` and `release.md`.
