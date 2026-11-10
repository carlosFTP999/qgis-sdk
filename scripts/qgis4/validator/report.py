from dataclasses import dataclass, asdict
from typing import Optional


@dataclass(frozen=True)
class Issue:
    level: str
    rule: str
    message: str
    path: Optional[str] = None
    line: Optional[int] = None

    def format(self):
        location = self.path or "<plugin>"
        if self.line is not None:
            location = f"{location}:{self.line}"
        return f"{location}: {self.level.upper()}: {self.rule}: {self.message}"

    def to_dict(self):
        return asdict(self)


def counts(issues):
    errors = sum(1 for issue in issues if issue.level == "error")
    warnings = sum(1 for issue in issues if issue.level == "warning")
    return errors, warnings


def as_json(plugin, issues, strict=False):
    errors, warnings = counts(issues)
    return {
        "ok": errors == 0 and (not strict or warnings == 0),
        "plugin": str(plugin),
        "strict": strict,
        "errors": errors,
        "warnings": warnings,
        "issues": [issue.to_dict() for issue in issues],
    }


def print_issues(issues):
    for issue in issues:
        print(issue.format())
    errors, warnings = counts(issues)
    print(f"SUMMARY: {errors} error(s), {warnings} warning(s)")
