# Shared QGIS Plugin Guidance

This folder holds only guidance that is identical for QGIS 3 and QGIS 4.
Version-specific references live in `../qgis3/` and `../qgis4/`.

## Cross-version invariants

- Keep `initGui()` and `unload()` symmetric; remove every action, dock, tool,
  provider, and signal.
- Run heavy or network work off the UI thread and honor cancellation.
- Transform CRS before distance, area, or overlay measurement.
- Import Qt only through `qgis.PyQt.*`.
- Log with `QgsMessageLog` or `iface.messageBar()`; never `print()`.
- Treat static validation as structure evidence, not runtime proof.

For version-specific API, metadata, packaging, and migration rules, read the
matching `../qgis3/` or `../qgis4/` reference.
