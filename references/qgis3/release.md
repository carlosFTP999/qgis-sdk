# Release and Packaging

Publishing a QGIS 3 plugin means shipping a ZIP whose top-level folder is the
plugin package, bumping `metadata.txt`, and publishing that ZIP from a source
code repository. The release flow assumes the plugin lives in a Git repository
and uses its release assets as the primary distribution path; GitHub is the
primary documented host.

The harness ZIP builder and `qgis-plugin-ci` are different tools: one produces a
deterministic archive locally, the other uploads a release asset.

## ZIP shape

```text
my_plugin.1.2.0.zip
`-- my_plugin/
    |-- __init__.py
    |-- metadata.txt
    |-- plugin.py
    |-- icon.png
    `-- resources/
```

The local `build_zip.py` helper emits `<plugin-dir>.zip`; `qgis-plugin-ci`
emits the versioned release-asset name above. Both archives must have the same
internal layout.

The archive has one top-level directory named exactly like the Python package,
with `metadata.txt` at its root. QGIS installs that directory. A ZIP with
`metadata.txt` at the archive root, or with a second wrapper directory, can
install under the wrong name or fail to load.

Exclude `tests/`, `.git/`, `.github/`, `.venv/`, `__pycache__/`, `*.pyc`,
`dist/`, local settings, and development requirements. Keep runtime
dependencies only if they are bundled inside the plugin folder.

```bash
python3 ../../scripts/qgis3/validator/build_zip.py <plugin-dir>
unzip -l <plugin-dir>.zip
```

## metadata.txt version and changelog

```ini
[general]
name=My Plugin
qgisMinimumVersion=3.16
version=1.2.0
description=Short description for the plugin manager
about=Longer description shown in the plugin details
author=Your Name
email=you@example.com
category=Vector
repository=https://github.com/my-org/my-plugin
tracker=https://github.com/my-org/my-plugin/issues
homepage=https://github.com/my-org/my-plugin
icon=icon.png
experimental=False
deprecated=False
changelog=
    1.2.0
    - Added the dock widget.
    - Fixed cancellation in the processing task.
```

Bump `version` for every published build and never reuse a version. Keep
`qgisMinimumVersion` in the 3.x range and do not add `supportsQt6`. Omit
`qgisMaximumVersion` unless a newer 3.x is known broken. `experimental=True` is
for a pre-release of that exact version and is per-version; `deprecated=True`
marks an obsolete but installable plugin.

`plugin_dependencies` is optional. Its comma-separated values are QGIS plugin
metadata `name` values, not pip distribution names. The official example shows
an optional `==version`, and the key exists since QGIS 3.8; do not require a
specific operator.

`icon` is a path relative to the plugin root. A declared icon that is absent
from the ZIP shows as a broken image in the plugin manager.

## Changelog discipline

Keep entries newest first and describe user-visible behavior. If the repository
keeps `CHANGELOG.md`, let `qgis-plugin-ci` copy the matching section into
`metadata.txt`. The tag, ZIP name, `metadata.txt`, and `plugins.xml` versions must
agree. See `metadata-qgis3.md`.

## GitHub repository prerequisite

Before the first release, the plugin must live in a source code repository that
supports releases; GitHub is the primary documented host:

- the repository has an `origin` remote that hosts the release;
- `metadata.txt` `repository`, `tracker`, and `homepage` point at that repository;
- the release commit is pushed before the tag is created;
- `LICENSE` is present and compatible with the QGIS plugin repository.

A local folder or a ZIP with no repository is not a release-ready project. The
release asset is the source of truth; any custom `plugins.xml` index points back
to it.

## qgis-plugin-ci as an external tool

`qgis-plugin-ci` is not vendored. Install a pinned version in a separate Python
3.10+ environment and read its current documentation. It is GPL-3.0; invoke it
as a process, do not import its modules. It packages with `git archive`, so the
release must be committed and submodules handled. `--allow-uncommitted-changes`
stashes and hard-resets tracked changes; prefer a clean tree instead.

It also installs `PyQt5` and `pyqt5ac`, even when the plugin has no `.qrc` file.
Do not install it into the QGIS interpreter. Its `.qrc` compilation is Qt5-only;
it does not understand `supportsQt6` or produce Qt6 resources.

`.qgis-plugin-ci` (YAML, top of the repository):

```yaml
plugin_path: my_plugin
github_organization_slug: my-org
project_slug: my-plugin
```

`plugin_path` must be a directory name without dashes. The slugs identify the
GitHub repository that hosts the release assets and links.

### GitHub release flow

`qgis-plugin-ci release` does **not** create a tag or a GitHub release. It
uploads the ZIP to a GitHub release that already exists for the tag.

```bash
# 1. Commit and push the release state.
git status --short          # must be empty
git push origin main

# 2. Tag the release commit and push the tag.
git tag -a v1.2.0 -m "v1.2.0"
git push origin v1.2.0

# 3. Create the GitHub release first.
gh release create v1.2.0 --title "v1.2.0" --notes-from-tag

# 4. Upload the plugin asset with qgis-plugin-ci.
#    --release-tag must match the GitHub release tag.
qgis-plugin-ci release 1.2.0 --release-tag v1.2.0 --github-token "$GITHUB_TOKEN"
```

In GitHub Actions, grant `permissions: contents: write` so `GITHUB_TOKEN` can
create the release and upload the asset. Add `--create-plugin-repo` to the last
command to also upload a `plugins.xml` asset for a custom repository. For a
pre-release, create the GitHub release with `--prerelease` and use a tag such as
`v1.2.0-rc1`; `qgis-plugin-ci` treats that suffix as experimental. Always pass
the matching `--release-tag` when the tag differs from the version.

`package` builds the ZIP without uploading:

```bash
qgis-plugin-ci package 1.2.0
```

`package --plugin-repo-url` additionally writes a `plugins.xml` entry locally.
Uploading to the official QGIS repository with `--osgeo-username` and
`--osgeo-password` is optional; the GitHub release remains the primary artifact.

The tag, ZIP name, `metadata.txt` version, GitHub release tag, and any index entry
must agree. Re-running a release is not idempotent: do not reuse a version or
overwrite an existing asset silently.

## Custom repository plugins.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<plugins>
  <pyqgis_plugin name="My Plugin" version="1.2.0">
    <description>Short description</description>
    <version>1.2.0</version>
    <qgis_minimum_version>3.16</qgis_minimum_version>
    <file_name>my_plugin.1.2.0.zip</file_name>
    <download_url>https://github.com/my-org/my-plugin/releases/download/v1.2.0/my_plugin.1.2.0.zip</download_url>
    <icon>https://raw.githubusercontent.com/my-org/my-plugin/main/my_plugin/icon.png</icon>
    <author_name>Your Name</author_name>
    <homepage>https://github.com/my-org/my-plugin</homepage>
    <tracker>https://github.com/my-org/my-plugin/issues</tracker>
    <repository>https://github.com/my-org/my-plugin</repository>
    <experimental>False</experimental>
    <deprecated>False</deprecated>
    <create_date>2026-10-27</create_date>
    <update_date>2026-10-27</update_date>
  </pyqgis_plugin>
</plugins>
```

`file_name` is the archive name, `download_url` must be an absolute URL QGIS can
fetch, and `qgis_minimum_version` uses underscores. Point `download_url` at the
GitHub release asset, not at a local file or a branch archive. Host the XML on
GitHub Pages or another stable HTTPS URL and refresh it when you publish; QGIS
caches repository indexes, so users may need to refresh. Do not hand-maintain a
multi-plugin index.

## What to verify before publishing

- [ ] Plugin lives in a source code repository with release support; `origin`
      remote and metadata `repository`/`tracker`/`homepage` agree.
- [ ] Clean working tree; release commit pushed before the tag.
- [ ] Version bumped in `metadata.txt`, tag, and repo XML; tag pushed.
- [ ] GitHub release exists before `qgis-plugin-ci release`; asset uploaded.
- [ ] `qgisMinimumVersion` is 3.x; no `supportsQt6`; no QGIS 4 enum spellings.
- [ ] No placeholders, no `PyQt6`, no direct `PyQt5` imports in shipped code.
- [ ] `classFactory` present; `unload()` removes actions, docks, providers,
      tasks, timers, and signals.
- [ ] Validator and project checker pass; tests pass or are explicitly skipped.
- [ ] ZIP inspected: one root, `metadata.txt` and icon inside, no dev files.
- [ ] Installed from ZIP in a clean profile; action, dock, or algorithm appears.
- [ ] Unload and reload leave no duplicate UI; Log Messages has no traceback.
- [ ] `download_url` and `plugins.xml` work from a second machine.
- [ ] Runtime status recorded; static checks alone are reported as not tested.

## Licensing and third-party code

QGIS itself is GPLv2-or-later, and plugins commonly use a compatible license. Do
not copy GPL source into an incompatible plugin, and do not vendor
`qgis-plugin-ci`, `qgis-venv-creator`, or `qgis_plugin_tools`. Ship the full
canonical text of a GPLv2-or-later-compatible license in a root `LICENSE`; do not
commit truncated, summarized, or placeholder license text. Record the license in
`LICENSE` and the repository upload form; check every bundled dependency's
license.

## Sources

- QGIS 3.40 PyQGIS cookbook, releasing plugins:
  https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/plugins/releasing.html
- QGIS 3.44 PyQGIS cookbook, plugin metadata table:
  https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#metadata-txt
