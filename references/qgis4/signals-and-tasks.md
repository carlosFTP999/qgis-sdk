# Signals and Background Tasks

Qt widgets and the map canvas belong to the GUI thread. Long work must move to a
`QgsTask` or a Processing algorithm, and results must return to the GUI thread
through signals.

## Signals

```python
self.action.triggered.connect(self.run)
self.combo.layerChanged.connect(self.on_layer_changed)
```

Disconnect or destroy objects in `unload()`. A signal connected to a deleted
widget can crash QGIS or produce duplicate work after the plugin is reloaded.

```python
self.combo.layerChanged.disconnect(self.on_layer_changed)
```

Use `try/except TypeError` only when a connection is genuinely optional.

## QgsTask

```python
from qgis.core import QgsTask

class FetchTask(QgsTask):
    def __init__(self, url):
        super().__init__("Fetch data", QgsTask.Flag.CanCancel)
        self.url = url
        self.error = None

    def run(self):
        try:
            # Network or long CPU work. No widgets, canvas, or message bar.
            if self.isCanceled():
                return False
            return True
        except Exception as exc:
            self.error = str(exc)
            return False

    def finished(self, result):
        # Runs in the GUI thread.
        if result:
            ...
        else:
            ...
```

Register the task:

```python
from qgis.core import QgsApplication

task = FetchTask(url)
QgsApplication.taskManager().addTask(task)
```

Keep a reference to the task while it runs. Cancel it in `unload()` and do not
allow its `finished` handler to touch a widget that no longer exists.

## Thread rules

- Do not create or modify widgets outside the GUI thread.
- Do not access `iface`, `QgsMapCanvas`, or `QgsMessageBar` from `run()`.
- Do not edit vector layers from a background thread.
- Use `QgsMessageLog` inside the task and emit a signal for UI updates.
- Check `isCanceled()` between expensive steps.
- Never leave a task running after the plugin has been unloaded.

## Error handling

Return a result object rather than raising across the task boundary. In
`finished()`, show a concise message bar notification and log the details.

## Signals and lifecycle checklist

- [ ] Every signal connection has an owner and a cleanup path.
- [ ] `unload()` disconnects signals from objects that outlive the plugin.
- [ ] `QgsTask` is stored while running.
- [ ] `unload()` cancels the task.
- [ ] The task never touches GUI objects.
- [ ] Cancellation is checked in long loops.
- [ ] Errors are reported without crashing QGIS.
