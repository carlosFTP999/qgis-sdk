---
name: qgis-sdk
description: "Trigger: QGIS 3 and QGIS 4 plugin, PyQGIS, PyQt5/Qt6, Processing, dock widget, map tool, metadata, packaging, migration. Build and validate QGIS plugins."
license: Apache-2.0
metadata:
  author: "carlosftp999"
  version: "1.0"
---

## Activation Contract

Load for QGIS 3 or QGIS 4 plugin creation, modification, validation, packaging, or migration; also for PyQGIS, PyQt5/Qt6, Processing, UI, metadata, and release. Serve both versions; never ask which QGIS version is installed. Skip non-QGIS Python work.

## Hard Rules

Common:

- Keep `initGui()` and `unload()` symmetric: remove every action, dock, tool, provider, and signal.
- Run heavy or network work off the UI thread with `QgsTask`; honor `feedback.isCanceled()`.
- Transform CRS before distance, area, or overlay.
- Never `print()`; log with `QgsMessageLog` or `iface.messageBar()`.
- Import Qt only through `qgis.PyQt.*`; never import PyQt5, PyQt6, PySide2, or PySide6 directly.
- Keep `metadata.txt` truthful; never add `supportsQt6`.
- Never claim runtime verification from static checks alone.

QGIS 3:

- PyQt5, `QVariant` field types, `Qgis.Info|Warning|Critical`.
- `qgisMinimumVersion` 3.x; no `supportsQt6=True`; use the QGIS 3 validator.

QGIS 4:

- Qt6, `QMetaType.Type.*`, and scoped `Qgis.MessageLevel.*`, `Qgis.GeometryType.*`, `Qgis.LayerFilter.*`, valid `QgsWkbTypes.GeometryType.*`.
- QGIS 4-only uses `qgisMinimumVersion=4.0`; no `supportsQt6`; use the QGIS 4 validator.

## Decision Gates

| Request | Pattern |
|---|---|
| Click/draw/measure/identify on the map | `map-tool` |
| Layer input -> calculation -> new layer | `processing-algorithm` (preferred) |
| Persistent side panel or form | `dock-widget` |
| Button-driven layer workflow outside Processing | `layer-processor` |
| Fetch data from an API | `api-caller` |

| Target signal | Route |
|---|---|
| PyQt5, `QVariant`, `Qgis.Info`, `qgisMinimumVersion` 3.x | QGIS 3 |
| Qt6, `QMetaType.Type.*`, scoped `Qgis.MessageLevel.*`, QGIS 4 metadata | QGIS 4 |
| Explicit request, `metadata.txt`, or no target signal | stated version; if none, ask one blocking question: QGIS 3 or QGIS 4 |

## Execution Steps

1. Determine the target from the explicit request or project context (`metadata.txt`, imports, enums, project files); never ask which QGIS version is installed.
2. Only when creating a new plugin with no target signal, ask one blocking question: target QGIS 3 or QGIS 4.
3. Read the matching `references/qgis3/` or `references/qgis4/` file.
4. Generate from the matching `assets/qgis3/` or `assets/qgis4/` path; replace every `{{PLACEHOLDER}}`.
5. Validate with the matching `scripts/qgis3/` or `scripts/qgis4/` validator; fix and revalidate; stop after three failures.
6. Report target version, paths, commands, exit codes, runtime status, and limitations.

## Output Contract

Return target QGIS version; plugin path and files; pattern; validator command and exit code; ZIP path or `not requested`; runtime status; limitations and risks. Do not commit generated plugins, ZIPs, or scratch directories unless asked.

## References

- `references/common/README.md` — shared cross-version guidance.
- `references/common/official-docs.md` — official upstream documentation links.
- `references/qgis3/` and `references/qgis4/`: `plugin-structure.md`, `pyqgis-core.md`, `geometry-ops.md`, `processing-algorithms.md`, `signals-and-tasks.md`, `ui-dockwidgets.md`, `testing-and-ci.md`, `common-errors.md`, `checklist.md`
- QGIS 3 only: `references/qgis3/metadata-qgis3.md`, `pyqt5-tooling.md`, `project-scaffold.md`, `release.md`
- QGIS 4 only: `references/qgis4/qgis4-migration.md`, `packaging.md`
- `assets/qgis3/`, `assets/qgis4/`
- `scripts/qgis3/`, `scripts/qgis4/`
