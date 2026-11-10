import ast
import configparser
import re
import struct
from pathlib import Path

from report import Issue

REQUIRED_METADATA = ("name", "qgisMinimumVersion", "description", "version")
RECOMMENDED_METADATA = ("author", "email", "about", "repository", "tracker")
CATEGORY_VALUES = {"Raster", "Vector", "Database", "Mesh", "Web"}
TRUTHY = {"1", "true", "yes", "on"}
PLACEHOLDER = re.compile(r"\{\{[A-Z0-9_]+\}\}")
PACKAGE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
VERSION = re.compile(r"^\d+(?:\.\d+)*$")
QGIS4_VERSION = re.compile(r"^4\.\d+$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TEXT_SUFFIXES = {
    ".py",
    ".txt",
    ".md",
    ".ui",
    ".json",
    ".ini",
    ".cfg",
    ".qrc",
    ".xml",
    ".yml",
    ".yaml",
}
EXCLUDED_DIRS = {"__pycache__", ".git", ".hg", ".svn", ".tox", ".venv", "venv"}


def _read_metadata(path):
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with path.open("r", encoding="utf-8") as handle:
            parser.read_file(handle)
    except (OSError, UnicodeError, configparser.Error) as exc:
        return None, f"cannot read metadata.txt: {exc}"

    if not parser.has_section("general"):
        return None, "metadata.txt is missing the [general] section"
    return parser["general"], None


def _iter_text_files(plugin):
    for path in sorted(plugin.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def _check_icon(plugin, metadata, issues):
    icon = metadata.get("icon", "").strip()
    if not icon:
        issues.append(
            Issue(
                "warning",
                "metadata-icon",
                "add a 32x32 PNG icon and declare it with icon=",
                "metadata.txt",
            )
        )
        return

    icon_path = Path(icon)
    if icon_path.is_absolute() or ".." in icon_path.parts:
        issues.append(
            Issue(
                "error",
                "metadata-icon",
                "icon must be a relative path inside the plugin",
                "metadata.txt",
            )
        )
        return

    target = plugin / icon_path
    if not target.is_file():
        issues.append(
            Issue(
                "error",
                "metadata-icon",
                f"declared icon does not exist: {icon}",
                "metadata.txt",
            )
        )
        return

    try:
        header = target.read_bytes()[:24]
    except OSError as exc:
        issues.append(
            Issue(
                "error",
                "metadata-icon",
                f"cannot read icon: {exc}",
                "metadata.txt",
            )
        )
        return

    if header[:8] != PNG_SIGNATURE or len(header) < 24:
        issues.append(
            Issue(
                "warning",
                "metadata-icon-format",
                "prefer a PNG icon for the QGIS plugin repository",
                "metadata.txt",
            )
        )
        return

    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (32, 32):
        issues.append(
            Issue(
                "warning",
                "metadata-icon-size",
                f"expected a 32x32 icon, found {width}x{height}",
                "metadata.txt",
            )
        )


def _version_tuple(value):
    try:
        return tuple(int(part) for part in value.split("."))
    except ValueError:
        return None


def _read_tree(path):
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    try:
        return ast.parse(source, filename=str(path))
    except SyntaxError:
        return None


def _defined_names(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _path_for_module(base):
    candidate = base.with_suffix(".py")
    if candidate.is_file():
        return candidate
    package = base / "__init__.py"
    if package.is_file():
        return package
    return None


def _resolve_relative(plugin, source_path, level, module):
    base = source_path.parent
    for _ in range(level - 1):
        base = base.parent
    if module:
        base = base.joinpath(*module.split("."))
    try:
        base.relative_to(plugin)
    except ValueError:
        return None
    return _path_for_module(base)


def _resolve_absolute(plugin, module):
    """Return (rooted, path) for an absolute import.

    Only imports rooted at the plugin package are considered; unrelated
    absolute imports are ignored so they are not mistaken for the re-export.
    """
    if not module:
        return False, None
    parts = module.split(".")
    if parts[0] != plugin.name:
        return False, None
    if len(parts) == 1:
        init_path = plugin / "__init__.py"
        return True, init_path if init_path.is_file() else None
    return True, _path_for_module(plugin.joinpath(*parts[1:]))


def _module_label(plugin, path):
    relative = path.relative_to(plugin)
    if relative.name == "__init__.py":
        parts = relative.parent.parts
    else:
        parts = relative.with_suffix("").parts
    if not parts:
        return plugin.name
    return ".".join(parts)


def _find_reexport(tree, symbol):
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            if (alias.asname or alias.name) == symbol:
                return node, alias
    return None


def _import_target(plugin, source_path, node):
    """Resolve an ImportFrom node to the module it imports from.

    Returns (kind, detail) where kind is "module" (detail is a path),
    "missing-module" (detail is the module string), "self" for a bare
    relative import, or "ignored" for an unrelated absolute import.
    """
    module = node.module
    if node.level >= 1:
        if not module:
            return "self", None
        target = _resolve_relative(plugin, source_path, node.level, module)
        if target is None:
            return "missing-module", module
        return "module", target

    rooted, target = _resolve_absolute(plugin, module)
    if not rooted:
        return "ignored", None
    if target is None:
        return "missing-module", module
    return "module", target


def _resolve_symbol(plugin, path, symbol, seen):
    """Follow re-export chains to a module that defines the symbol."""
    if path in seen:
        return "cycle", path
    seen.add(path)
    tree = _read_tree(path)
    if tree is None:
        return "uninspectable", path
    if symbol in _defined_names(tree):
        return "defined", path
    reexport = _find_reexport(tree, symbol)
    if reexport is None:
        return "missing-symbol", path
    node, alias = reexport
    kind, detail = _import_target(plugin, path, node)
    if kind == "module":
        return _resolve_symbol(plugin, detail, symbol, seen)
    if kind == "missing-module":
        return "missing-module", detail
    if kind == "self":
        return "self", path
    return "missing-symbol", path


def _check_class_factory(plugin, init_path, issues):
    tree = _read_tree(init_path)
    if tree is None:
        # Syntax errors are reported by check_syntax; skip import analysis.
        return

    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "classFactory"
            and node not in tree.body
        ):
            issues.append(
                Issue(
                    "warning",
                    "classfactory-shape",
                    "classFactory should be a top-level function",
                    "__init__.py",
                    node.lineno,
                )
            )

    if "classFactory" in _defined_names(tree):
        return

    resolved = False
    attempted = False
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        for alias in node.names:
            if (alias.asname or alias.name) != "classFactory":
                continue
            kind, detail = _import_target(plugin, init_path, node)
            if kind == "ignored":
                continue
            attempted = True
            if kind == "self":
                issues.append(
                    Issue(
                        "error",
                        "classfactory-import",
                        "import classFactory from a relative submodule, not the package itself",
                        "__init__.py",
                        node.lineno,
                    )
                )
                continue
            if kind == "missing-module":
                issues.append(
                    Issue(
                        "error",
                        "classfactory-import",
                        f"module '{detail}' does not exist",
                        "__init__.py",
                        node.lineno,
                    )
                )
                continue
            status, failing = _resolve_symbol(plugin, detail, alias.name, set())
            if status == "defined":
                resolved = True
            elif status == "missing-module":
                issues.append(
                    Issue(
                        "error",
                        "classfactory-import",
                        f"module '{failing}' does not exist",
                        "__init__.py",
                        node.lineno,
                    )
                )
            elif status == "uninspectable":
                issues.append(
                    Issue(
                        "error",
                        "classfactory-import",
                        f"cannot inspect module '{_module_label(plugin, failing)}'",
                        "__init__.py",
                        node.lineno,
                    )
                )
            else:
                issues.append(
                    Issue(
                        "error",
                        "classfactory-import",
                        f"module '{_module_label(plugin, failing)}' does not define {alias.name}",
                        "__init__.py",
                        node.lineno,
                    )
                )

    if resolved:
        return

    if not attempted:
        for path in sorted(plugin.rglob("*.py")):
            if path == init_path or any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            submodule = _read_tree(path)
            if submodule is None:
                continue
            if "classFactory" in _defined_names(submodule):
                relative = path.relative_to(plugin).as_posix()
                issues.append(
                    Issue(
                        "error",
                        "classfactory-import",
                        f"classFactory is defined in {relative} but not re-exported by __init__.py",
                        "__init__.py",
                    )
                )
                break

    issues.append(
        Issue(
            "error",
            "missing-classfactory",
            "__init__.py must define or re-export classFactory(iface)",
            "__init__.py",
        )
    )


def collect(plugin):
    issues = []
    plugin = Path(plugin)

    if not PACKAGE_NAME.match(plugin.name):
        issues.append(
            Issue(
                "error",
                "invalid-package-name",
                f"folder name '{plugin.name}' is not a valid Python package name",
                plugin.name,
            )
        )

    metadata_path = plugin / "metadata.txt"
    if not metadata_path.is_file():
        issues.append(
            Issue(
                "error",
                "missing-metadata",
                "metadata.txt is required at the plugin root",
                "metadata.txt",
            )
        )
    else:
        metadata, error = _read_metadata(metadata_path)
        if error:
            issues.append(Issue("error", "metadata", error, "metadata.txt"))
        else:
            for key in REQUIRED_METADATA:
                if not metadata.get(key, "").strip():
                    issues.append(
                        Issue(
                            "error",
                            "metadata-required",
                            f"missing required key: {key}",
                            "metadata.txt",
                        )
                    )
            for key in RECOMMENDED_METADATA:
                if not metadata.get(key, "").strip():
                    issues.append(
                        Issue(
                            "warning",
                            "metadata-recommended",
                            f"add recommended key: {key}",
                            "metadata.txt",
                        )
                    )

            minimum = metadata.get("qgisMinimumVersion", "").strip()
            if minimum and not QGIS4_VERSION.match(minimum):
                if minimum.startswith("4."):
                    issues.append(
                        Issue(
                            "warning",
                            "metadata-version",
                            "qgisMinimumVersion should use major.minor, for example 4.0",
                            "metadata.txt",
                        )
                    )
                else:
                    issues.append(
                        Issue(
                            "error",
                            "qgis4-minimum",
                            "qgisMinimumVersion must target QGIS 4.x in major.minor form",
                            "metadata.txt",
                        )
                    )

            maximum = metadata.get("qgisMaximumVersion", "").strip()
            if maximum:
                if not QGIS4_VERSION.match(maximum):
                    if maximum.startswith("4."):
                        issues.append(
                            Issue(
                                "warning",
                                "metadata-version",
                                "qgisMaximumVersion should use major.minor, for example 4.0",
                                "metadata.txt",
                            )
                        )
                    else:
                        issues.append(
                            Issue(
                                "warning",
                                "qgis4-maximum",
                                "a QGIS 4 plugin should not advertise a non-4.x maximum",
                                "metadata.txt",
                            )
                        )
                elif minimum and QGIS4_VERSION.match(minimum):
                    if _version_tuple(maximum) < _version_tuple(minimum):
                        issues.append(
                            Issue(
                                "warning",
                                "qgis4-maximum",
                                "qgisMaximumVersion must be greater than or equal to qgisMinimumVersion",
                                "metadata.txt",
                            )
                        )

            category = metadata.get("category", "").strip()
            if category and category not in CATEGORY_VALUES:
                issues.append(
                    Issue(
                        "warning",
                        "metadata-category",
                        f"category '{category}' is not a documented QGIS value "
                        "(Raster, Vector, Database, Mesh, Web); omit it for the default menu",
                        "metadata.txt",
                    )
                )

            if "supportsQt6" in metadata:
                issues.append(
                    Issue(
                        "error",
                        "qgis4-metadata",
                        "remove supportsQt6; QGIS 4 no longer supports this key",
                        "metadata.txt",
                    )
                )

            version = metadata.get("version", "").strip()
            if version and not VERSION.match(version):
                issues.append(
                    Issue(
                        "warning",
                        "metadata-version",
                        "version should be numeric, for example 0.1.0",
                        "metadata.txt",
                    )
                )

            _check_icon(plugin, metadata, issues)

            processing = (
                metadata.get("hasProcessingProvider", "").strip().lower() in TRUTHY
            )
            provider_file = (plugin / "provider.py").is_file()
            if processing and not provider_file:
                issues.append(
                    Issue(
                        "warning",
                        "processing-provider",
                        "hasProcessingProvider=yes but provider.py is missing",
                        "metadata.txt",
                    )
                )
            elif provider_file and not processing:
                issues.append(
                    Issue(
                        "warning",
                        "processing-provider",
                        "provider.py is present but hasProcessingProvider is not yes",
                        "metadata.txt",
                    )
                )

    init_path = plugin / "__init__.py"
    if not init_path.is_file():
        issues.append(
            Issue(
                "error",
                "missing-init",
                "__init__.py is required at the plugin root",
                "__init__.py",
            )
        )
    else:
        _check_class_factory(plugin, init_path, issues)

    for path in _iter_text_files(plugin):
        relative = path.relative_to(plugin).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            issues.append(
                Issue("error", "read-error", "file is not readable UTF-8 text", relative)
            )
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if PLACEHOLDER.search(line):
                issues.append(
                    Issue(
                        "error",
                        "unreplaced-placeholder",
                        "replace template placeholders before packaging",
                        relative,
                        line_number,
                    )
                )

    for path in sorted(plugin.rglob("*")):
        if path.is_dir() and path.name in EXCLUDED_DIRS:
            relative = path.relative_to(plugin).as_posix()
            issues.append(
                Issue(
                    "warning",
                    "cache-directory",
                    "remove caches and VCS data before packaging",
                    relative,
                )
            )
        elif path.is_file() and path.suffix == ".pyc":
            issues.append(
                Issue(
                    "warning",
                    "compiled-python",
                    "remove .pyc files before packaging",
                    path.relative_to(plugin).as_posix(),
                )
            )

    return issues
