# QGIS Plugin Checklist

Use this checklist after implementation and before delivery. The validator is a
static gate, not a substitute for this review.

## Before writing

- [ ] The resolved package name, target path, and files to create were listed.
- [ ] If the target existed and was non-empty, explicit overwrite approval was
      obtained; nothing was truncated or merged silently.

## Structure

- [ ] Plugin folder name is a valid Python package name.
- [ ] `__init__.py` exposes `classFactory`.
- [ ] `metadata.txt` has a `[general]` section and required fields.
- [ ] `category` is a documented value or omitted; `supportsQt6` is absent.
- [ ] A QGIS 4-only plugin uses `qgisMinimumVersion=4.0`; any
      `qgisMaximumVersion` is deliberate.
- [ ] `hasProcessingProvider=yes` only when a provider is registered.
- [ ] `LICENSE` holds the full canonical GPLv2-or-later-compatible text and any
      metadata license fields match.
- [ ] `icon.png` exists if `metadata.txt` declares it.
- [ ] No template placeholders remain.
- [ ] No `__pycache__`, secrets, or local paths are included.

## Lifecycle

- [ ] `initGui()` and `unload()` are symmetric.
- [ ] Actions are removed and destroyed.
- [ ] Docks are removed and destroyed.
- [ ] Map tools are unset.
- [ ] Processing providers are removed.
- [ ] Timers and tasks are stopped or cancelled.
- [ ] Signals are disconnected from objects that outlive the plugin.

## Threading

- [ ] Long work runs in `QgsTask` or Processing.
- [ ] No GUI access from a task.
- [ ] Cancellation is checked.
- [ ] Task references are retained while running.
- [ ] Task completion returns to the GUI thread.

## CRS and geometry

- [ ] CRS validity is checked.
- [ ] Geometry is transformed before metric operations.
- [ ] Geometry type is checked.
- [ ] Invalid geometries are handled or reported.
- [ ] Spatial index is used for repeated queries.

## UI

- [ ] Actions appear in the expected menu or toolbar.
- [ ] Docks appear in the expected area.
- [ ] Dialogs have a parent.
- [ ] Layer and field widgets are filtered.
- [ ] Visible strings follow the project language policy.
- [ ] `.qm` files are built from translated `.ts` files, not empty scaffolding.
- [ ] The installed `QTranslator` is removed in `unload()`.
- [ ] No heavy work runs in a widget callback.

## Processing

- [ ] Provider is registered and removed.
- [ ] Algorithm `name()` is stable and lowercase.
- [ ] Parameters and outputs are declared.
- [ ] `processAlgorithm` checks cancellation.
- [ ] Algorithm appears in the toolbox and `qgis_process` when applicable.

## Delivery

- [ ] Validator command and exit code are recorded.
- [ ] ZIP path is reported, or packaging is marked not requested.
- [ ] Runtime testing status is explicit.
- [ ] Known limitations are listed.
- [ ] The user knows where the plugin appears in QGIS.

## Optional QGIS runtime smoke test

Run this only when a QGIS runtime is available. It is not part of the default
test suite, and the static validator cannot replace it.

1. Start QGIS with a clean profile or a disposable profile.
2. Install the plugin from its ZIP through **Plugins -> Manage and Install
   Plugins -> Install from ZIP**.
3. Enable the plugin and confirm that QGIS reports no Python error.
4. Verify the expected menu action, toolbar action, dock, map tool, or
   Processing algorithm is present in the documented location.
5. Run the plugin on a small, known dataset. Check the output layer, messages,
   and the QGIS Log Messages panel.
6. If the plugin edits data, verify that cancel and error paths do not leave a
   partial edit.
7. Unload and reload the plugin. Confirm that actions, docks, providers, and
   tasks do not duplicate or remain active.
8. Record the QGIS version, operating system, steps, and result in the feature
   log. If the test was not run, report `not tested` explicitly.
