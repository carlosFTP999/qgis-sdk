# Plugin Structure and Lifecycle

A QGIS plugin is a Python package with a stable folder name, a `metadata.txt`
file, a `classFactory` entry point, and a plugin object that QGIS can load and
unload repeatedly.

## Minimal package

```text
my_plugin/
├── __init__.py
├── metadata.txt
├── plugin.py
├── icon.png
└── <pattern module>.py
```

Optional directories:

```text
my_plugin/
├── resources/
├── ui/
├── tests/
├── LICENSE
└── README.md
```

## Folder name

The folder name is the plugin package name. Use lowercase letters, digits, and
underscores; start with a letter. Do not use keywords or spaces. The class
factory must import from this package consistently.

## `metadata.txt`

Use a `[general]` section and include at least:

```ini
[general]
name=My Plugin
qgisMinimumVersion=4.0
description=One sentence describing the plugin.
version=0.1.0
author=Your Name
email=you@example.com
about=Longer description, usage notes, and limitations.
repository=https://example.com/repository
tracker=https://example.com/issues
icon=icon.png
```

Keep `name` aligned with the plugin folder and `classFactory` contract. Avoid
multi-line values in fields that QGIS expects to be single-line.

Use only documented values:

- `category` is one of `Raster`, `Vector`, `Database`, `Mesh`, or `Web`. Omit it
  to leave the plugin in the default Plugins menu; `category=Plugins` is not a
  documented value.
- `qgisMinimumVersion=4.0` marks a QGIS 4-only plugin. `qgisMaximumVersion` is
  optional; omit it unless you deliberately cap the supported range.
- `supportsQt6` was removed from QGIS 4 and is not recognized. Do not add it.
- `hasProcessingProvider=yes` only when the plugin actually registers a
  Processing provider; omit the key otherwise.
- `license` is optional metadata. When present, it must match the chosen license
  and the `LICENSE` file.

For a publishable plugin, ship the full canonical text of a GPLv2-or-later
compatible license in a `LICENSE` file at the plugin root, and include it in the
ZIP. Do not scaffold truncated, summarized, or placeholder license text.

## `__init__.py`

The class factory is the stable entry point:

```python
def classFactory(iface):
    from .plugin import MyPlugin

    return MyPlugin(iface)
```

Keep the import inside `classFactory` so QGIS can load the package without
resolving every optional dependency at import time.

## Plugin object lifecycle

```python
class MyPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        self.action = QAction("My action", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&My Plugin", self.action)

    def unload(self):
        if self.action is not None:
            self.iface.removePluginMenu("&My Plugin", self.action)
            self.action.deleteLater()
            self.action = None

    def run(self):
        pass
```

`initGui()` and `unload()` must be symmetric. For every action, dock, map tool,
provider, signal connection, timer, or task created during initialization,
remove or cancel it during unload.

## Pattern entry points

| Pattern | Initialization | Cleanup |
|---|---|---|
| Processing algorithm | Add provider to the processing registry | Remove provider |
| Layer processor | Add menu action | Remove action and dialog |
| Map tool | Create map tool and activate it | Unset map tool and remove action |
| Dock widget | Add dock to the main window | Remove dock and action |
| API caller | Add action and start task | Cancel task and remove action |

## External material

Treat external plugin-generator examples as study material, not a source to
copy. MCP servers are optional aids; the bundled references are primary and no
QGIS-specific MCP server is a dependency.

## Reload behavior

QGIS can unload and reload a plugin without restarting. Duplicate menu entries,
duplicate providers, stale dock widgets, and live tasks after unload are
lifecycle bugs, not cosmetic issues.

## Validation

Run:

```bash
python3 ../../scripts/qgis4/validator/run_all.py <plugin-dir>
```

The validator checks the package shape, `classFactory`, placeholders, syntax,
and common PyQGIS lifecycle rules. For `metadata.txt` it checks the recommended
keys, that `qgisMinimumVersion` is a 4.x `major.minor` value, that an optional
`qgisMaximumVersion` is a 4.x value at or above the minimum, that `category` is
one of the documented values or absent, that `supportsQt6` is absent, and that
`hasProcessingProvider=yes` matches a `provider.py`. For a declared icon it warns
(non-fatal) when the PNG is not 32x32; official QGIS metadata guidance does not
mandate a 32x32 size, so treat that as a polish recommendation, not a
requirement. It does not replace loading the plugin inside QGIS.

## Sources

- QGIS 3.44 PyQGIS cookbook, plugin metadata table:
  https://docs.qgis.org/3.44/en/docs/pyqgis_developer_cookbook/plugins/plugins.html#metadata-txt
- Migrate to QGIS 4 (official QGIS plugin repository):
  https://plugins.qgis.org/docs/migrate-qgis4
