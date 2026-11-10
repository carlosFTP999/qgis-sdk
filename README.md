# qgis-sdk

`qgis-sdk` is one agent skill for QGIS 3 and QGIS 4 plugin work. It builds,
modifies, validates, packages, and migrates PyQGIS plugins from a single entry
point, with version-specific references, templates, and validators split into
`qgis3/` and `qgis4/` folders.

## Install with skills.sh

```bash
npx skills add carlosftp999/opencode-qgis-sdk
```

The [skills.sh CLI](https://www.skills.sh/docs/cli) discovers the root
`SKILL.md` and installs it for your agent. Repository-page grouping is declared in
[`skills.sh.json`](./skills.sh.json); see the
[skills.sh customization docs](https://www.skills.sh/docs/customize).

## What the skill covers

- **QGIS 3 and QGIS 4 from one skill.** The router selects the version-specific
  references, assets, and validator at execution time.
- **No installed-version prompt.** The skill infers the target from the explicit
  request, `metadata.txt`, imports, enums, or project files. It asks a single
  blocking question — QGIS 3 or QGIS 4 — only when creating a new plugin with no
  target signal, and never asks which QGIS version is installed.
- **Split layout.** Shared guidance lives in `references/common/`; everything
  version-specific lives in parallel `qgis3/` and `qgis4/` trees.

## Repository layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Unified router: activation, rules, gates, steps, output |
| `references/qgis3/`, `references/qgis4/` | Version-specific PyQGIS guidance |
| `references/common/` | Cross-version guidance and official documentation index |
| `assets/qgis3/` | QGIS 3 templates and project files |
| `assets/qgis4/` | QGIS 4 templates |
| `scripts/qgis3/` | QGIS 3 validator and project checker |
| `scripts/qgis4/` | QGIS 4 validator |
| `skills.sh.json` | skills.sh repository-page grouping |
| `package.json` | Repository metadata |
| `LICENSE` | Apache-2.0 license |

## Validation

Sample validation commands:

```bash
# QGIS 4 plugin
python3 scripts/qgis4/validator/run_all.py ./my_plugin

# QGIS 3 plugin, plus the surrounding project check
python3 scripts/qgis3/validator/run_all.py ./my_plugin
python3 scripts/qgis3/check_project.py .
```

The validators are static: they check structure, syntax, placeholders, version
markers, API leakage, and lifecycle heuristics; they do not load the plugin in
QGIS. Runtime testing remains a separate check.

## Official documentation

- [QGIS documentation](https://docs.qgis.org/)
- [QGIS plugin repository docs](https://plugins.qgis.org/docs)
- [Qt 6 reference](https://doc.qt.io/qt-6/)
- [Python 3 documentation](https://docs.python.org/3/)
- [PyQGIS API](https://qgis.org/pyqgis/)
- [QGIS 4 plugin migration guide](https://plugins.qgis.org/docs/migrate-qgis4)
- [Plugin migration to Qt 5 and Qt 6](https://github.com/qgis/QGIS/wiki/Plugin-migration-to-be-compatible-with-Qt5-and-Qt6)

The full index lives in
[`references/common/official-docs.md`](./references/common/official-docs.md).
It links the official QGIS and PyQGIS docs, plugin repository and migration
guides, Qt and PyQt references, and Python packaging documentation.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
