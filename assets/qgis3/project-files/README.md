# My QGIS Plugin

A QGIS 3 plugin project targeting QGIS 3.16+ and PyQt5.

## Layout

```text
my_plugin/              Plugin package and metadata
tests/                  Tests that stay outside the plugin ZIP
docs/development.md     Setup, test, and release notes
```

## Setup

Use the Python interpreter bundled with QGIS, or a virtual environment created
from it. Do not install `PyQt5` or PyQGIS from PyPI into the project.

```bash
python -c "from qgis.core import Qgis; print(Qgis.QGIS_VERSION)"
python -m pytest -q
```

## Validate and package

Run these from the repository root that contains the `qgis-sdk` skill:

```bash
python3 scripts/qgis3/validator/run_all.py my_plugin
python3 scripts/qgis3/validator/build_zip.py my_plugin
```

The validator is static. It does not prove that QGIS loaded the plugin, that the
dock appears, or that a Processing algorithm ran.

## Release

This project is released from a source code repository that supports releases;
GitHub is the primary documented host. Push the release commit and tag, create
the GitHub release, then upload the ZIP with `qgis-plugin-ci`:

```bash
git tag -a v1.2.0 -m "v1.2.0"
git push origin main --tags
gh release create v1.2.0 --title "v1.2.0" --notes-from-tag
qgis-plugin-ci release 1.2.0 --release-tag v1.2.0 --github-token "$GITHUB_TOKEN"
```

`qgis-plugin-ci release` uploads to an existing GitHub release; it does not
create the release. See `docs/development.md` for the full flow.

## License

Choose a license compatible with the QGIS plugin repository and add the
corresponding `LICENSE` file. Do not copy a license from a template.
