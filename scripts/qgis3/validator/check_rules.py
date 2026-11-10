import ast
import re
from pathlib import Path

from report import Issue

RULES = (
    (
        "direct-qt-import",
        "error",
        re.compile(r"^\s*(?:from|import)\s+(?:PyQt[56]|PySide[26])\b"),
        "import Qt through qgis.PyQt",
    ),
    (
        "qaction-wrong-module",
        "error",
        re.compile(
            r"from\s+qgis\.PyQt\.QtGui\s+import\s+[^\n]*\bQAction\b"
        ),
        "QAction belongs to qgis.PyQt.QtWidgets in QGIS 3",
    ),
    (
        "qgis4-message-level",
        "error",
        re.compile(r"\bQgis\.MessageLevel\b"),
        "use Qgis.Info, Qgis.Warning, or Qgis.Critical",
    ),
    (
        "qgis4-qmetatype",
        "error",
        re.compile(r"\bQMetaType\b"),
        "use QVariant field types in QGIS 3",
    ),
    (
        "qgis4-wkb-enum",
        "error",
        re.compile(r"\bQgsWkbTypes\.Type\.\w+"),
        "use QgsWkbTypes.Point and other QGIS 3 enum values",
    ),
    (
        "qgis4-sink-flag",
        "error",
        re.compile(r"\bQgsFeatureSink\.Flag\.\w+"),
        "use QgsFeatureSink.FastInsert in QGIS 3",
    ),
    (
        "qgis4-processing-flag",
        "error",
        re.compile(r"\bQgsProcessingAlgorithm\.Flag\.\w+"),
        "use QgsProcessingAlgorithm.FlagHideFromToolbox in QGIS 3",
    ),
    (
        "qgis4-task-flag",
        "error",
        re.compile(r"\bQgsTask\.Flag\.\w+"),
        "use QgsTask.CanCancel in QGIS 3",
    ),
    (
        "qgis4-dialog-exec",
        "warning",
        re.compile(r"\.exec\s*\("),
        "QGIS 3 PyQt5 dialogs use exec_()",
    ),
    (
        "qgis2-layer-registry",
        "error",
        re.compile(r"\bQgsMapLayerRegistry\b"),
        "use QgsProject.instance()",
    ),
    (
        "qgis2-distance-ellipsoidal-mode",
        "error",
        re.compile(r"\.setEllipsoidalMode\s*\("),
        "use QgsDistanceArea.setEllipsoid() in QGIS 3",
    ),
    (
        "legacy-qregexp",
        "warning",
        re.compile(r"\bQRegExp\b"),
        "prefer QRegularExpression",
    ),
    (
        "print-call",
        "warning",
        re.compile(r"^\s*print\s*\("),
        "use QgsMessageLog or iface.messageBar()",
    ),
)

GUI_NAMES = {
    "QgsMessageBar",
    "QgsMapCanvas",
    "QgsDockWidget",
    "QMessageBox",
    "QDialog",
    "QWidget",
}


def _is_qgs_task(node):
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "QgsTask":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "QgsTask":
            return True
    return False


def _task_run_gui(node):
    for item in node.body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if item.name != "run":
            continue
        for child in ast.walk(item):
            if isinstance(child, ast.Attribute):
                if (
                    isinstance(child.value, ast.Name)
                    and child.value.id == "self"
                    and child.attr == "iface"
                ):
                    return child.lineno
                if child.attr == "messageBar":
                    return child.lineno
            if isinstance(child, ast.Name) and child.id in GUI_NAMES:
                return child.lineno
    return None


def collect(plugin):
    issues = []
    plugin = Path(plugin)

    for path in sorted(plugin.rglob("*.py")):
        relative = path.relative_to(plugin).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue

        for rule, level, pattern, message in RULES:
            for line_number, line in enumerate(source.splitlines(), start=1):
                if pattern.search(line):
                    issues.append(Issue(level, rule, message, relative, line_number))

        if "def initGui" in source and "def unload" not in source:
            issues.append(
                Issue(
                    "error",
                    "asymmetric-lifecycle",
                    "a plugin with initGui() must also define unload()",
                    relative,
                )
            )

        try:
            tree = ast.parse(source, filename=relative)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not _is_qgs_task(node):
                continue
            line = _task_run_gui(node)
            if line is not None:
                issues.append(
                    Issue(
                        "error",
                        "gui-in-task",
                        "QgsTask.run() must not touch widgets or the canvas",
                        relative,
                        line,
                    )
                )

    return issues
