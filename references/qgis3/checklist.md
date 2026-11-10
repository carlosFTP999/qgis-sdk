# QGIS 3 Plugin Delivery Checklist

Run this after implementation and again after the final validation. The
validator and project checker are static gates; this checklist covers the
runtime and packaging evidence they cannot produce.

## Before writing

- [ ] The resolved package name, target path, and files to create were listed.
- [ ] If the target existed and was non-empty, explicit overwrite approval was
      obtained; nothing was truncated or merged silently.

## 1. Project layout

- [ ] Plugin folder is a valid Python package name (no dashes, no spaces).
- [ ] `__init__.py` exposes `classFactory(iface)`.
- [ ] `metadata.txt` is at the plugin root.
- [ ] `icon.png` exists if `metadata.txt` declares it.
- [ ] Tests live outside the plugin package.
- [ ] No unresolved template markers, `cookiecutter`, `jinja`, or `.j2` residue.
- [ ] No `__pycache__`, `.venv`, `.git`, local paths, secrets, or development
      requirements in the deliverable.
- [ ] The chosen template was adapted in place; no generator was run.

## 2. Metadata

- [ ] `[general]` section is present.
- [ ] `name`, `description`, `version`, `author`, `email`, and `about` are set.
- [ ] `qgisMinimumVersion` is 3.x (default `3.16`) and matches the code.
- [ ] `category` is `Raster`, `Vector`, `Database`, `Mesh`, `Web`, or omitted;
      `Plugins` and `Analysis` are not documented values.
- [ ] `experimental` and `deprecated` reflect the actual release.
- [ ] `changelog` names the current version and user-visible changes.
- [ ] `icon` path resolves inside the plugin root.
- [ ] `supportsQt6` is absent; no QGIS 4 fields were added.
- [ ] Repository, tracker, and homepage point at the GitHub repository that
      hosts the release; the index does not invent a different source.
- [ ] `LICENSE` holds the full canonical text of a GPLv2-or-later-compatible
      license, not a truncated, summarized, or placeholder stub; any metadata
      license field matches it.

## 3. Lifecycle

- [ ] `classFactory` imports the plugin lazily and returns an instance.
- [ ] `initGui()` creates actions, menus, docks, tools, providers, and timers.
- [ ] `unload()` removes every one of them, in reverse order.
- [ ] Map tools are unset from the canvas and dereferenced.
- [ ] Processing providers are removed from the registry.
- [ ] Timers are stopped.
- [ ] Running tasks are canceled; no work starts during unload.
- [ ] Signals connected to long-lived objects are disconnected.
- [ ] `unload()` is safe after a partial `initGui()` and leaves no duplicates.

## 4. UI cleanup

- [ ] Actions are kept on `self` and deleted after removal.
- [ ] Docks are removed, deleted, and dereferenced.
- [ ] Dialogs have `iface.mainWindow()` as parent.
- [ ] Dialogs use `exec_()` in PyQt5 and are not leaked when modeless.
- [ ] Layer combo filters use `QgsMapLayerProxyModel` constants.
- [ ] The field combo follows the selected layer.
- [ ] No widget is created or touched from a worker thread.
- [ ] Visible strings use `self.tr()` or the project translation path.
- [ ] `.qm` files are built from translated `.ts` files, not empty scaffolding.
- [ ] The installed `QTranslator` is removed in `unload()`.

## 5. Threading

- [ ] Long work runs in `QgsTask` or `QgsProcessingAlgRunnerTask`.
- [ ] `run()` checks `isCanceled()` between expensive steps.
- [ ] Progress is reported with `setProgress()` and stays within 0-100.
- [ ] `run()` does not access `iface`, widgets, the canvas, or the message bar.
- [ ] Results return through `finished()` or a queued signal.
- [ ] The task reference is kept for cancellation and cleared after completion.
- [ ] Exceptions are caught, logged, and returned as `False`.
- [ ] `waitForFinished()` is never called from the GUI thread.

## 6. CRS and geometry

- [ ] Every input layer has a valid CRS.
- [ ] Geometry is transformed before distance, area, or overlay work.
- [ ] Units are checked; degrees are never reported as metres.
- [ ] `QgsDistanceArea` uses the project transform context and an ellipsoid
      when geodesic measurements are required.
- [ ] Invalid geometries are handled or reported.
- [ ] Geometry types are checked before casting.

## 7. Processing provider

- [ ] Provider registration and removal are symmetric in `initGui`/`unload`.
- [ ] `metadata.txt` has `hasProcessingProvider=yes` when a provider is used.
- [ ] Algorithm `name()` is stable, lowercase, and documented.
- [ ] Parameters and outputs use QGIS 3 parameter classes.
- [ ] `processAlgorithm` checks `feedback.isCanceled()`.
- [ ] The algorithm appears in the toolbox after enabling the plugin.
- [ ] `qgis_process` can list it when the provider is available.
- [ ] See `processing-algorithms.md`.

## 8. Static validation

- [ ] `python3 ../../scripts/qgis3/validator/run_all.py <plugin-dir>` ran; exit code is 0.
- [ ] `--json` output was reviewed when a machine-readable report was needed.
- [ ] `--strict` was used for the release gate, if the project requires it.
- [ ] Every finding was fixed or explained; none was suppressed silently.
- [ ] The validator's limits are understood: it does not load the plugin.
- [ ] No QGIS 2 API, QGIS 4 enum, `PyQt6`, or `QMetaType` remains.

## 9. Project check

- [ ] `python3 ../../scripts/qgis3/check_project.py <project-dir>` ran; exit code is 0.
- [ ] `metadata.txt`, `pyproject.toml`, tests, CI, and `.qgis-plugin-ci`
      exist for a publishable project.
- [ ] The project is hosted in a source code repository with release support;
      a local folder is not release-ready. GitHub is the primary documented host.
- [ ] No Jinja, cookiecutter, or generation hooks are present.
- [ ] The package name is a valid Python identifier.
- [ ] Direct `PyQt5` and `PyQt6` imports are absent; use `qgis.PyQt`.
- [ ] `LICENSE` is present and the plugin metadata declares a repository URL.

## 10. Packaging and release

- [ ] `python3 ../../scripts/qgis3/validator/build_zip.py <plugin-dir>` produced the ZIP.
- [ ] The ZIP has one plugin root with `metadata.txt` inside it.
- [ ] No tests, CI files, caches, secrets, or local paths are in the ZIP.
- [ ] `metadata.txt` version equals the tag and repository index version.
- [ ] Release commit and tag are pushed to GitHub before publishing.
- [ ] The GitHub release exists before `qgis-plugin-ci release`; the asset ZIP
      was uploaded to that release.
- [ ] `qgis-plugin-ci` ran in a separate Python 3.10+ environment, pinned, with
      `--release-tag` matching the GitHub tag; it was not imported into the plugin.
- [ ] The icon is present and opens.
- [ ] Installation from the ZIP was tested in a clean QGIS 3 profile.
- [ ] Custom repository `plugins.xml` points at the GitHub release asset.
- [ ] See `release.md`.

## 11. Runtime honesty

- [ ] If no QGIS runtime was used, report `runtime not tested`.
- [ ] If manual testing ran, record QGIS version, OS, dataset, and steps.
- [ ] The tested QGIS version is 3.16 or newer and includes the minimum.
- [ ] Unload and reload were tested; no duplicate actions, docks, or providers.
- [ ] The Log Messages panel shows no traceback or critical error.
- [ ] Stated limitations match observed behavior.
- [ ] Static checks are not described as proof that the plugin loads.

## 12. Feature-log evidence

- [ ] Plugin path and chosen pattern are recorded.
- [ ] Validator command, exit code, and summary are recorded.
- [ ] Project checker command, exit code, and summary are recorded.
- [ ] ZIP path, or `not requested`, is recorded.
- [ ] Runtime status and limitations are recorded.
- [ ] Evidence lives in the existing ODD feature document; no new format was
      invented.
- [ ] No commit, tag, or release was made without authorization.

## Manual smoke test outline

1. Start QGIS 3 with a disposable profile.
2. Install the ZIP and enable the plugin.
3. Confirm the documented menu, toolbar, dock, map tool, or algorithm appears.
4. Run it on a small known dataset; check the output and Log Messages.
5. Cancel a long task and confirm the UI recovers without a traceback.
6. Unload and reload; confirm nothing duplicates.
7. Record the evidence above; if any step was skipped, say so.
