# Metadata for QGIS 3 Plugins

`metadata.txt` is the contract between the plugin and QGIS. It sits inside the
plugin package and is read before the plugin's Python code runs. A malformed or
incomplete file can make a working plugin invisible to QGIS.

## Purpose

Use this reference to write a QGIS 3.16+ `metadata.txt`, choose version bounds
that keep the plugin on PyQt5, and avoid metadata copied from a QGIS 4 project.

## Complete example

```ini
[general]
name=Contour Helper
qgisMinimumVersion=3.16
description=Buffer polygon features and write the result to a new layer.
about=Buffers polygon features into a new layer with Processing progress feedback.
version=0.1.0
author=Example Team
email=dev@example.com
repository=https://github.com/example/contour-helper
tracker=https://github.com/example/contour-helper/issues
homepage=https://example.com/contour-helper
category=Vector
icon=icon.png
experimental=False
deprecated=False
hasProcessingProvider=yes
server=False
tags=buffer, polygon, analysis
changelog=0.1.0: Initial release.
```

Keep the keys exactly as shown. `[general]` is the only section a QGIS 3 plugin
needs unless the plugin uses a documented extra section.

## Required fields

| Field | Guidance |
|---|---|
| `name` | Human-readable plugin name, stable across releases |
| `qgisMinimumVersion` | `3.16` or another 3.x floor; `major.minor` form |
| `description` | Shown in the plugin manager |
| `about` | Longer plain-text description and limitations |
| `version` | Plugin version, bumped for every upload |
| `author` | Person or team responsible for the plugin |
| `email` | Contact address for the plugin |
| `repository` | Source repository URL |

`tracker` (issue tracker URL) and `category` (menu category) are optional; omit
`category` to leave the plugin in the default Plugins menu.

`homepage` is optional but useful when the source repository is not the user
documentation. `icon` is required for a polished published plugin. `license` is
a project decision: use a value that matches the `LICENSE` file and the policy
of the repository where the plugin will be published.

## Version policy

Start at `qgisMinimumVersion=3.16` only when the code is actually compatible
with 3.16. Do not claim 3.16 because a template said so. If the plugin uses an
API added in a later 3.x release, raise the minimum to that release.

Do not set `qgisMaximumVersion` unless there is a concrete reason to cap the
plugin. A maximum that is too low hides the plugin from newer 3.x patch
releases. If a maximum is required, keep it inside the 3.x line; do not use a
4.x value for a PyQt5 plugin.

The QGIS 4 transition uses a different Qt binding. `supportsQt6` was removed in
QGIS 4, so it is not current guidance for either version. A QGIS 3 plugin must
not advertise Qt 6 compatibility: leave `supportsQt6` out of the file entirely.
If the key was copied from a newer template, delete it rather than setting it to
a false-looking value.

## Publishing fields

- `experimental` is optional; do not add it just because a template shows it. If
  declared, use `False` for a stable release and `True` only for a pre-release of
  that exact version; the key is per-version, and experimental versions stay
  hidden unless the user enables "Show also Experimental Plugins".
- `deprecated=False` unless the plugin is retired and should be replaced.
- `hasProcessingProvider=yes` when the plugin registers a Processing provider;
  omit the key otherwise.
- `server=False` for a desktop-only plugin. Change it only when the code is
  actually safe on QGIS Server.
- `category` is one of `Raster`, `Vector`, `Database`, `Mesh`, or `Web`; omit it
  to leave the plugin in the default Plugins menu. `Plugins` and `Analysis` are
  not documented values, even though older examples still show them.
- `icon` is a path relative to `metadata.txt`, normally `icon.png`. Use a PNG
  icon; do not use an absolute path or a remote URL.
- `repository` is the source code URL, not the plugin repository page.
  `tracker` is the issue URL. `homepage` is user documentation.

## Plugin dependencies

`plugin_dependencies` is optional. Its comma-separated values are QGIS plugin
metadata `name` values, not pip distribution names. The official metadata table
describes it as a "PIP-like comma separated list of other plugins to install,
use plugin names coming from their metadata’s name field" and shows
`MyOtherPlugin==1.12,YetAnotherPlugin`. The `==version` part appears only in
that example; the documentation does not require that operator. The key exists
since QGIS 3.8.

## Version and changelog

Use a plain version such as `0.1.0` or `1.4.2`. Do not prefix it with `v`, and
do not reuse a version that was already uploaded: the plugin repository treats
versions as immutable. `changelog` is shown to users, so describe behavior
changes rather than commits.

```ini
version=1.2.0
changelog=
    1.2.0: Add a distance parameter and cancel long runs cleanly.
    1.1.1: Fix a crash when the input layer has no features.
    1.1.0: Support polygon and multipolygon inputs.
```

The plugin repository accepts indented continuation lines for a readable
changelog. Verify how your target QGIS release displays `about` and `changelog`;
older INI readers may expose only the first line of a multiline value.

## Validation

```bash
python3 ../../scripts/qgis3/check_project.py .
```

The project checker verifies that `metadata.txt` exists, that the minimum
version is 3.x in `major.minor` form, and that Qt 6 metadata keys are absent. It
cannot know whether a 3.x API exists in the release you claim, so test that claim
against a real QGIS installation when possible.

## Pitfalls

- Adding spaces around `=`. Keep the `key=value` form.
- Using `qgisMinimumVersion=3.16.0`; QGIS expects `major.minor`.
- Setting a maximum version lower than the minimum, or lower than a 3.x release
  you actually support.
- Copying a QGIS 4/Qt 6 metadata block into a QGIS 3 plugin.
- Forgetting to bump `version` after changing behavior.
- Pointing `icon` at a file outside the plugin package.
- Declaring a license in metadata that does not match `LICENSE`.

## Sources

- QGIS 3.44 PyQGIS cookbook, plugin metadata table:
  https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#metadata-txt
- QGIS 3.40 PyQGIS cookbook, plugins:
  https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/plugins/plugins.html

Related: `project-scaffold.md`, `plugin-structure.md`, `processing-algorithms.md`.
