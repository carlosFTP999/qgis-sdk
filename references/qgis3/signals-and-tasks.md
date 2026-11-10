# Signals and Background Tasks

QGIS 3 plugins run on Qt 5 through `qgis.PyQt`. Widgets, the map canvas, and the
message bar live in the GUI thread; `QgsTask.run()` does not. Return results
through `finished()` or a queued signal, never by touching a widget in `run()`.

## Connect signals deliberately

```python
self.layer_combo.layerChanged.connect(self.on_layer_changed)
self.canvas.mapToolSet.connect(self.on_map_tool_changed)
```

A connection created in `initGui()` can outlive a plugin reload. Disconnect it
in `unload()`:

```python
try:
    self.layer_combo.layerChanged.disconnect(self.on_layer_changed)
except TypeError:
    pass  # already disconnected or never connected
```

Connect UI updates to a bound method of a `QObject` (a dialog, a dock, or a
small controller object). Qt then delivers the call in the receiver's thread.
The same rule applies to signals emitted by a task.

## `QgsTask` lifecycle

```python
from qgis.core import QgsApplication, QgsTask


class AggregateTask(QgsTask):
    def __init__(self, values):
        super().__init__("Aggregate values", QgsTask.CanCancel)
        self.values = list(values)
        self.total = 0
        self.error = None

    def run(self):
        if not self.values:
            return True
        total = 0
        for index, value in enumerate(self.values, start=1):
            if self.isCanceled():
                return False
            total += value
            self.setProgress(100.0 * index / len(self.values))
        self.total = total
        return True

    def finished(self, result):
        # QgsTaskManager calls this in the GUI thread, success or not.
        if result:
            self.on_success(self.total)
        else:
            self.on_failure("Canceled or failed")
```

Keep `run()` pure Python as far as possible. `finished()` runs in the main thread
for success and for early termination, so it replaces most custom result signals.

## Completed and terminated signals

```python
task.taskCompleted.connect(self.on_task_completed)    # successful run
task.taskTerminated.connect(self.on_task_terminated)  # cancel or error
```

Exactly one fires per run on a task managed by `QgsTaskManager`: `taskCompleted`
on success, `taskTerminated` on cancellation or error. Use `finished()` or these
signals for feedback, not both.

## Schedule, retain, cancel

```python
self._task = AggregateTask(values)
self._task.taskCompleted.connect(self.on_task_completed)
self._task.taskTerminated.connect(self.on_task_terminated)
QgsApplication.taskManager().addTask(self._task)
```

`addTask()` transfers ownership to the task manager, but keep a Python
reference so `unload()` can cancel it. QGIS already shows task progress in the
task manager; connect `progressChanged` only if the plugin also has its own
progress bar.

```python
def unload(self):
    if self._task is not None:
        self._task.cancel()
        self._task = None
```

`cancel()` only sets the canceled flag. `run()` must check `isCanceled()`
between expensive steps; QGIS cannot stop a loop for you. Never call
`waitForFinished()` from a GUI slot: it blocks QGIS.

## Results and the GUI thread

Store plain data on the task (`self.total`, `self.rows`, `self.error`) and read
it in `finished()`. Do not read `iface`, create widgets, or edit vector layers in
`run()`. Only `finished()` and its slots touch the UI.

For layer processing, do not hand-roll edits in a worker. Use
`QgsProcessingAlgRunnerTask`, which runs an algorithm in the background and
reports results in the GUI thread:

```python
from qgis.core import (
    QgsApplication,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
)

self._context = QgsProcessingContext()
self._context.setProject(QgsProject.instance())
self._feedback = QgsProcessingFeedback()
self._task = QgsProcessingAlgRunnerTask(
    algorithm, parameters, self._context, self._feedback
)
self._task.executed.connect(self.on_algorithm_executed)  # (success, results)
QgsApplication.taskManager().addTask(self._task)
```

Keep `context` and `feedback` on `self` until the task finishes. See
`processing-algorithms.md` and `pyqgis-core.md`.

## Pitfalls

- `QgsTask.Flag.CanCancel` is not the QGIS 3.16 spelling; use
  `QgsTask.CanCancel`.
- An exception that escapes `run()` is not a result you can handle. Catch it,
  log it with `QgsMessageLog`, and return `False`.
- Do not update a `QProgressBar` directly from `run()`; update it in
  `finished()` or in a slot on a GUI-thread `QObject`.
- Do not start a task in `unload()`; cancel and let the task stop.
- Check `isCanceled()` inside loops, not only before the first iteration.
- Pass layer IDs or plain data to the task; resolve layers in the GUI thread.
- `QgsTask.fromFunction` is a Python convenience, but confirm it exists in the
  minimum QGIS version you support before using it instead of a subclass.

See `ui-dockwidgets.md` for the widgets that consume these results and
`testing-and-ci.md` for the difference between a task test and a runtime QGIS
test.
