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
        re.compile(r"from\s+qgis\.PyQt\.QtWidgets\s+import\s+[^\n]*\bQAction\b"),
        "QAction belongs to qgis.PyQt.QtGui",
    ),
    (
        "unscoped-qgis-enum",
        "error",
        re.compile(r"\bQgis\.(?:Info|Warning|Critical|Success)\b"),
        "use Qgis.MessageLevel.*",
    ),
    (
        "unscoped-qt-enum",
        "error",
        re.compile(
            r"\bQt\.(?:Checked|Unchecked|PartiallyChecked|AlignLeft|AlignRight|"
            r"AlignCenter|AlignJustify|LeftDockWidgetArea|RightDockWidgetArea|"
            r"TopDockWidgetArea|BottomDockWidgetArea)\b"
        ),
        "use the scoped Qt enum, for example Qt.CheckState.Checked",
    ),
    (
        "unscoped-wkb-enum",
        "error",
        re.compile(
            r"\bQgsWkbTypes\.(?:Point|LineString|Polygon|MultiPoint|"
            r"MultiLineString|MultiPolygon|GeometryCollection|NoGeometry|"
            r"PointGeometry|LineGeometry|PolygonGeometry|UnknownGeometry|"
            r"NullGeometry)\b"
        ),
        "use QgsWkbTypes.Type.* for WKB values or QgsWkbTypes.GeometryType.Point/Line/Polygon/Unknown/Null for geometry values; *Geometry names are unscoped aliases",
    ),
    (
        "invalid-scoped-wkb-geometry",
        "error",
        re.compile(
            r"\b(?:QgsWkbTypes|Qgis)\.GeometryType\.(?:PointGeometry|"
            r"LineGeometry|PolygonGeometry|UnknownGeometry|NullGeometry)\b"
        ),
        "QgsWkbTypes.GeometryType members are Point, Line, Polygon, Unknown, and Null; *Geometry names are unscoped aliases",
    ),
    (
        "unscoped-sink-flag",
        "error",
        re.compile(r"\bQgsFeatureSink\.(?:FastInsert|RollBackOnErrors)\b"),
        "use QgsFeatureSink.Flag.*",
    ),
    (
        "unscoped-processing-flag",
        "error",
        re.compile(r"\bQgsProcessingAlgorithm\.Flag[A-Z]\w*"),
        "use QgsProcessingAlgorithm.Flag.Flag*",
    ),
    (
        "legacy-layer-registry",
        "error",
        re.compile(r"\bQgsMapLayerRegistry\b"),
        "use QgsProject.instance()",
    ),
    (
        "legacy-qregexp",
        "warning",
        re.compile(r"\bQRegExp\b"),
        "prefer QRegularExpression",
    ),
    (
        "legacy-qvariant",
        "warning",
        re.compile(r"\bQVariant\b"),
        "prefer QMetaType for new fields",
    ),
    (
        "legacy-exec",
        "warning",
        re.compile(r"\.exec_\s*\("),
        "use exec()",
    ),
    (
        "print-call",
        "warning",
        re.compile(r"^\s*print\s*\("),
        "use QgsMessageLog or iface.messageBar()",
    ),
    (
        "gui-in-task",
        "error",
        re.compile(
            r"self\.iface|messageBar\s*\(|QgsMessageBar|QgsMapCanvas|"
            r"QMessageBox|QDialog\b"
        ),
        "do not touch GUI objects from QgsTask.run()",
    ),
)


def _task_run_gui(node):
    for base in node.bases:
        base_name = ast.unparse(base)
        if not base_name.endswith("QgsTask"):
            continue
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if item.name != "run":
                continue
            for child in ast.walk(item):
                try:
                    text = ast.unparse(child)
                except (ValueError, AttributeError):
                    continue
                if any(
                    marker in text
                    for marker in (
                        "self.iface",
                        "messageBar(",
                        "QgsMessageBar",
                        "QgsMapCanvas",
                        "QMessageBox",
                        "QDialog",
                    )
                ):
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
            if rule == "gui-in-task":
                continue
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
