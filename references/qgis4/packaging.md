# Packaging and Distribution

A QGIS plugin ZIP must contain one plugin root directory with `metadata.txt` at
its top level. QGIS installs from **Plugins -> Manage and Install Plugins ->
Install from ZIP**.

## Package contents

```text
my_plugin/
├── __init__.py
├── metadata.txt
├── plugin.py
├── icon.png
├── README.md
├── LICENSE
└── ...
```

Do not include:

- `__pycache__/`
- `.pyc`
- `.git/`
- local virtual environments
- editor files
- secrets, tokens, or private data
- test scratch directories

## Versioning

`metadata.txt` version must match the release. `qgisMinimumVersion` must be a
version the plugin actually supports. A QGIS 4-only plugin uses
`qgisMinimumVersion=4.0`. `qgisMaximumVersion` is optional and not required for
QGIS 4; omit it unless you deliberately cap the range. `supportsQt6` was removed
from QGIS 4 and must not be present. Do not claim QGIS 4 support if the code
still imports PyQt5 or uses unscoped enums.

## Plugin dependencies

`plugin_dependencies` is optional. Its comma-separated values are QGIS plugin
metadata `name` values, not pip distribution names. The official metadata table
describes it as a "PIP-like comma separated list of other plugins to install,
use plugin names coming from their metadata’s name field" and shows
`MyOtherPlugin==1.12,YetAnotherPlugin`. The `==version` part appears only in
that example; the documentation does not require that operator. The key exists
since QGIS 3.8.

## Licensing

A publishable plugin needs the full canonical text of a GPLv2-or-later
compatible license in a `LICENSE` file at the plugin root. Do not scaffold
truncated, summarized, or placeholder license text, and do not bundle license
texts for the user to choose from: the license is a project decision. If
`metadata.txt` declares license fields, they must match the chosen license.

## Icon

Declare `icon=icon.png` only when the file exists inside the plugin directory.
An icon outside the plugin root will not be included in the ZIP.

## ZIP root

The ZIP must not contain a wrapper directory above the plugin folder unless the
installation instructions explicitly require it. The plugin folder name is the
package name used by `classFactory`.

## Build

```bash
python3 ../../scripts/qgis4/validator/build_zip.py <plugin-dir>
```

The builder validates first unless `--skip-validation` is passed, writes the ZIP
next to the plugin directory, and returns:

- `0`: ZIP created.
- `1`: validation errors.
- `2`: plugin directory missing.

`--skip-validation` is for debugging only; do not ship an unvalidated ZIP
without saying so.

## Release checklist

- [ ] `metadata.txt` version updated.
- [ ] `category` is a documented value or omitted; `supportsQt6` is absent.
- [ ] `experimental` is optional. If declared, it must match the exact version: `False` for a stable release, `True` only for a pre-release; the key is per-version.
- [ ] `LICENSE` contains the full canonical license text and any metadata license fields match.
- [ ] Icon exists and is declared.
- [ ] No caches, secrets, or local paths are included.
- [ ] ZIP contains one plugin root.
- [ ] Plugin installs from ZIP in a clean QGIS profile.
- [ ] Processing algorithms appear in the toolbox.
- [ ] Menu actions appear in the expected location.
- [ ] Unload/reload does not duplicate UI or providers.
- [ ] Runtime testing status is reported honestly.

## GitHub release

The plugin must live in a GitHub repository. Push the release commit and tag,
create the GitHub release for that tag, then attach the validated ZIP:

```bash
git tag -a v1.2.0 -m "v1.2.0"
git push origin main --tags
gh release create v1.2.0 --title "v1.2.0" --notes-from-tag
gh release upload v1.2.0 my_plugin.1.2.0.zip
```

A GitHub Actions workflow needs `permissions: contents: write` to create and
upload release assets with `GITHUB_TOKEN`. Do not use `qgis-plugin-ci` for a
QGIS 4 / Qt6 plugin: it compiles `.qrc` with PyQt5 and does not produce Qt6
resources; compile Qt 6 resources with the standalone Qt `rcc` tool instead. Use
the QGIS 3 skill for that external tool.

## Official repository

The official QGIS plugin repository has licensing and metadata requirements.
Verify them before publishing. It requires GPLv2-or-later-compatible licensing
and a `LICENSE` file in the plugin package; a plugin that is MIT-licensed in
source may still be rejected for that reason. Follow the current repository
policy.

## Sources

- QGIS 3.40 PyQGIS cookbook, releasing plugins:
  https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/plugins/releasing.html
- Migrate to QGIS 4 (official QGIS plugin repository):
  https://plugins.qgis.org/docs/migrate-qgis4
