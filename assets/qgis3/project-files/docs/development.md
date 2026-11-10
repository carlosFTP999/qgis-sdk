# Development

## Environment

Use the Python interpreter that ships with QGIS 3, or create a virtual
environment from it. On Windows, the OSGeo4W shell exposes the QGIS Python
launcher. On Linux and macOS, use the interpreter that can import `qgis.core`.

`qgis-venv-creator` is an external tool. Follow its own instructions and use the
interpreter it produces. Verify the binding before running tests:

```bash
python -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
```

Do not add `PyQt5`, `qgis`, or `osgeo` to the project dependencies.

## Tests

```bash
python -m pytest -q
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

Tests that need QGIS use `pytest.importorskip` and are skipped by a plain Python
interpreter. Static metadata tests still run.

## Linting and type checks

```bash
ruff check .
ruff format --check .
mypy my_plugin
```

These checks do not load the plugin in QGIS.

## Validation and packaging

Use the skill validator and project checker when the skill is installed. Run
these from the repository root that contains the `qgis-sdk` skill:

```bash
python3 scripts/qgis3/validator/run_all.py my_plugin
python3 scripts/qgis3/check_project.py .
python3 scripts/qgis3/validator/build_zip.py my_plugin
```

The ZIP contains one top-level `my_plugin/` folder with `metadata.txt` inside.

## Release

The plugin must live in a source code repository that supports releases;
GitHub is the primary documented host. `.qgis-plugin-ci` is a starting
configuration; review its slugs before the first release.

Release from a clean, pushed commit:

```bash
git status --short
git push origin main
git tag -a v1.2.0 -m "v1.2.0"
git push origin v1.2.0
gh release create v1.2.0 --title "v1.2.0" --notes-from-tag
```

Then run `qgis-plugin-ci` from a separate Python 3.10+ environment:

```bash
qgis-plugin-ci release 1.2.0 --release-tag v1.2.0 --github-token "$GITHUB_TOKEN"
```

`qgis-plugin-ci release` uploads the ZIP to an existing GitHub release; it does
not create the tag or the release. The `--release-tag` must match the GitHub
release tag. Do not install `qgis-plugin-ci` into the QGIS interpreter: it pulls
`PyQt5` and `pyqt5ac`, and its `.qrc` compilation is Qt5-only.

Verify the release asset URL and install the downloaded ZIP in a clean QGIS 3
profile before publishing.

## Runtime check

Record the QGIS version, operating system, steps, and result. If the plugin was
not loaded in QGIS, report `runtime not tested`.
