# Project Scaffold

A QGIS 3 plugin is a plain Python package plus a few project files. There is no
renderer and no generated project state: copy the static assets, rename the
package, and edit the files in place. This keeps the repository reviewable and
avoids hiding project decisions inside a template engine.

## Purpose

Use this reference to lay out a QGIS 3.16+ plugin repository, decide which files
ship inside the ZIP, and adapt `../../assets/qgis3/project-files/` without introducing
Cookiecutter, Jinja2, hooks, or an interactive generator.

## Recommended tree

```text
contour-helper/
├── contour_helper/              # shipped plugin package
│   ├── __init__.py              # classFactory
│   ├── metadata.txt
│   ├── plugin.py
│   ├── icon.png
│   ├── provider.py
│   └── algorithms/
│       ├── __init__.py
│       └── buffer.py
├── tests/
│   ├── conftest.py
│   └── test_plugin.py
├── docs/
│   └── development.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── .qgis-plugin-ci
├── .pre-commit-config.yaml
├── pyproject.toml
├── .gitignore
├── LICENSE
└── README.md
```

The inner `contour_helper/` folder is the plugin package. Its name must be a
valid Python identifier: lowercase letters, digits, and underscores, starting
with a letter. The repository folder may use a hyphen; the package may not.

## Required and optional files

| Path | Required | Notes |
|---|---|---|
| `<package>/__init__.py` | yes | Defines `classFactory(iface)` |
| `<package>/metadata.txt` | yes | QGIS reads it from the package root |
| `<package>/plugin.py` | yes | Plugin object with `initGui()` and `unload()` |
| `<package>/icon.png` | for publishing | PNG icon referenced by `metadata.txt` |
| `<package>/provider.py` | only for Processing | Provider and algorithms |
| `tests/` | for maintained plugins | Keep outside the shipped package |
| `pyproject.toml` | for maintained plugins | Tool configuration, not runtime deps |
| `.github/workflows/ci.yml` | for maintained plugins | Test and lint jobs |
| `.qgis-plugin-ci` | for releases | Uploads assets to an existing GitHub release |
| `docs/development.md` | recommended | Setup, test, and release notes |
| `LICENSE` | for publishing | Full canonical GPLv2-or-later-compatible text; the assets do not bundle license texts |

`metadata.txt` belongs inside the package, not at the repository root. The ZIP
must contain exactly one top-level folder, and that folder must contain
`metadata.txt`. A ZIP with loose files at its root will not install as a plugin.

## GitHub repository

The release flow assumes the plugin lives in a source code repository that
supports releases; GitHub is the primary documented host. Initialize Git in the
project root, create the repository, and set `origin` before the first release.
Point `metadata.txt` `repository`, `tracker`, and `homepage` at that repository.

A local directory or a ZIP without a repository is a development copy, not a
release-ready project. Git hosting release assets is the primary distribution
path; a custom `plugins.xml` index points at the release assets.

## Static asset workflow

1. Copy the contents of `../../assets/qgis3/project-files/` to the repository root.
2. Add a root `LICENSE` file containing the full canonical text of a
   GPLv2-or-later-compatible license chosen for the project. Do not write
   truncated, summarized, or placeholder license text, and do not expect the
   assets to supply a license: licensing is a project decision.
3. Copy one pattern from `../../assets/qgis3/templates/` into `<package>/`.
4. Rename the package folder and update every import and menu label.
5. Replace every `{{PLACEHOLDER}}` marker with a real value.
6. Replace the example icon with the project icon.
7. Update `metadata.txt`, `pyproject.toml`, tests, CI names, and the
   `.qgis-plugin-ci` GitHub slugs for the project.
8. Initialize Git, create the GitHub repository, and set `origin`.
9. Run the plugin validator and the project checker before the first commit.

Search for leftover markers with `grep -R "{{"` before packaging. The assets are
starting points, not generated output: edit the copies, do not add a build step
that transforms them.

## No renderer

Do not add `.j2` files, a `cookiecutter.json`, generation hooks, or a script that
asks interactive questions and writes a project. Those mechanisms make the
plugin depend on a tool that is not present in QGIS or CI, and they obscure what
was actually shipped. A copied file is easier to review than a rendered one.

## Placement rules

- Keep tests in `tests/`, outside the package, so they are never installed.
- Keep CI in `.github/workflows/`, outside the package.
- Keep the icon and runtime resources inside the package.
- Keep `README.md` at the repository root for developers and users of the source.
- Keep `LICENSE` at the repository root with the full canonical text of a
  GPLv2-or-later-compatible license, and match the license declared for the
  plugin repository and in `metadata.txt`.
- Keep local environments (`.venv/`, `__pycache__/`, `.pytest_cache/`, `*.zip`)
  out of version control.

## Generated UI files

`pyuic5` output imports the Qt binding directly. Do not commit generated UI
modules with bare binding imports in a QGIS 3 plugin. Prefer writing widgets in
Python with `qgis.PyQt` imports, or rewrite generated imports to `qgis.PyQt` and
keep the file in sync with its `.ui` source. See `pyqt5-tooling.md`.

## Validation

```bash
python3 ../../scripts/qgis3/validator/run_all.py contour_helper
python3 ../../scripts/qgis3/check_project.py .
```

The validator checks the plugin package. The project checker checks the
surrounding repository for metadata, tests, CI, release configuration, and
leftover generator or Qt 6 markers. Neither proves that QGIS loaded the plugin;
record runtime testing separately.

## Pitfalls

- Putting `metadata.txt` at the repository root while the package is nested, so
  the ZIP has the wrong shape.
- Shipping `tests/` or CI files inside the plugin package.
- Committing a ZIP or a virtual environment instead of a tag.
- Copying the example icon without replacing its placeholder or dimensions.
- Renaming the package folder but leaving the old package name in imports.
- Adding a template engine to "simplify" a five-file project.
- Keeping generated UI code that imports Qt directly.

Related: `metadata-qgis3.md`, `pyqt5-tooling.md`, `plugin-structure.md`.
