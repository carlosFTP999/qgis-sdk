# QGIS plugin templates

Each directory is a complete, runnable plugin pattern. Replace every
`{{PLACEHOLDER}}` before packaging.

| Placeholder | Meaning | Example |
|---|---|---|
| `{{PLUGIN_NAME}}` | Python package and folder name | `sample_plugin` |
| `{{PLUGIN_TITLE}}` | User-visible plugin name | `Sample Plugin` |
| `{{PLUGIN_CLASS}}` | Plugin class name | `SamplePlugin` |
| `{{PROVIDER_CLASS}}` | Processing provider class | `SampleProvider` |
| `{{PLUGIN_DESCRIPTION}}` | One-line description | `Buffers vector features.` |
| `{{AUTHOR}}` | Author name | `Ada Lovelace` |
| `{{EMAIL}}` | Contact email | `ada@example.com` |
| `{{MENU_TEXT}}` | Menu action label | `Open panel` |

## Patterns

- `processing-algorithm`: provider plus buffer algorithm.
- `layer-processor`: dialog that inspects a vector layer.
- `map-tool`: canvas click tool.
- `dock-widget`: dock panel with a refresh action.
- `api-caller`: `QgsTask` HTTP request with lifecycle cleanup.

## Validation

Copy a template, replace all placeholders, then run from the repository root
that contains the `qgis-sdk` skill:

```bash
python3 scripts/qgis4/validator/run_all.py <plugin-dir>
python3 scripts/qgis4/validator/build_zip.py <plugin-dir>
```

The templates are static starting points. They are not proof that the plugin
loads in the user's QGIS version.
