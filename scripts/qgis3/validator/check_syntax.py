import ast
from pathlib import Path

from report import Issue


def collect(plugin):
    issues = []
    plugin = Path(plugin)

    for path in sorted(plugin.rglob("*.py")):
        relative = path.relative_to(plugin).as_posix()
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            issues.append(
                Issue(
                    "error",
                    "syntax-read",
                    "cannot read Python file: {}".format(exc),
                    relative,
                )
            )
            continue
        try:
            ast.parse(source, filename=relative)
        except SyntaxError as exc:
            issues.append(
                Issue(
                    "error",
                    "syntax-error",
                    exc.msg or "invalid Python syntax",
                    relative,
                    exc.lineno,
                )
            )

    return issues
