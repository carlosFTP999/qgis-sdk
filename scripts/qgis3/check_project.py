import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

VALIDATOR_DIR = Path(__file__).resolve().parent / "validator"
sys.path.insert(0, str(VALIDATOR_DIR))

from report import Issue, counts, print_issues  # noqa: E402
from run_all import collect_issues  # noqa: E402

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_MISSING = 2
EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
}
TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".txt",
    ".toml",
    ".yml",
    ".yaml",
    ".ini",
    ".cfg",
    ".json",
}


def _read(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def _require_file(project, relative, level, issues):
    path = project / relative
    if not path.is_file():
        issues.append(
            Issue(
                level,
                "project-file",
                "missing project file: {}".format(relative),
                relative,
            )
        )
        return None
    text = _read(path)
    if not text.strip():
        issues.append(
            Issue(
                level,
                "project-file",
                "project file is empty: {}".format(relative),
                relative,
            )
        )
    return text


def _check_generator_residue(project, issues):
    for path in sorted(project.rglob("*")):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        relative = path.relative_to(project).as_posix()
        if path.is_dir():
            if path.name == "hooks" and (
                (path / "pre_gen_project.py").is_file()
                or (path / "post_gen_project.py").is_file()
            ):
                issues.append(
                    Issue(
                        "error",
                        "cookiecutter-residue",
                        "remove Cookiecutter generation hooks",
                        relative,
                    )
                )
            continue
        if path.name == "cookiecutter.json":
            issues.append(
                Issue(
                    "error",
                    "cookiecutter-residue",
                    "remove the Cookiecutter configuration",
                    relative,
                )
            )
            continue
        if path.suffix == ".j2":
            issues.append(
                Issue(
                    "error",
                    "cookiecutter-residue",
                    "remove Jinja templates; use the static assets",
                    relative,
                )
            )
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = _read(path)
        if "{{ cookiecutter." in text or "{% cookiecutter" in text:
            issues.append(
                Issue(
                    "error",
                    "cookiecutter-residue",
                    "remove unreplaced Cookiecutter markers",
                    relative,
                )
            )


def _find_plugin(project):
    if (project / "metadata.txt").is_file():
        return project, None

    candidates = []
    try:
        children = sorted(project.iterdir())
    except OSError as exc:
        return None, "cannot read the project directory: {}".format(exc)
    for child in children:
        if not child.is_dir() or child.name.startswith("."):
            continue
        if (child / "metadata.txt").is_file():
            candidates.append(child)

    if len(candidates) == 1:
        return candidates[0], None
    if len(candidates) > 1:
        names = ", ".join(candidate.name for candidate in candidates)
        return None, "multiple plugin directories found: {}".format(names)
    return None, "no plugin directory with metadata.txt was found"


def _check_project_files(project, issues):
    readme = _require_file(project, "README.md", "warning", issues)
    if readme is not None and "qgis" not in readme.lower():
        issues.append(
            Issue(
                "warning",
                "readme-qgis",
                "README should name QGIS and the target version",
                "README.md",
            )
        )

    pyproject = _require_file(project, "pyproject.toml", "warning", issues)
    if pyproject is not None:
        if "[tool.pytest.ini_options]" not in pyproject:
            issues.append(
                Issue(
                    "warning",
                    "pytest-config",
                    "add [tool.pytest.ini_options] to pyproject.toml",
                    "pyproject.toml",
                )
            )
        if "testpaths" not in pyproject:
            issues.append(
                Issue(
                    "warning",
                    "pytest-config",
                    "declare testpaths for deterministic test discovery",
                    "pyproject.toml",
                )
            )

    precommit = _require_file(
        project, ".pre-commit-config.yaml", "warning", issues
    )
    if precommit is not None and "ruff" not in precommit:
        issues.append(
            Issue(
                "warning",
                "precommit-ruff",
                "add a Ruff hook for static checks",
                ".pre-commit-config.yaml",
            )
        )

    gitignore = _require_file(project, ".gitignore", "warning", issues)
    if gitignore is not None and ".venv" not in gitignore:
        issues.append(
            Issue(
                "warning",
                "gitignore-venv",
                "ignore the local virtual environment",
                ".gitignore",
            )
        )

    release = _require_file(project, ".qgis-plugin-ci", "warning", issues)
    if release is not None and "plugin_path" not in release:
        issues.append(
            Issue(
                "warning",
                "release-config",
                "declare plugin_path in .qgis-plugin-ci",
                ".qgis-plugin-ci",
            )
        )

    ci = _require_file(
        project, ".github/workflows/ci.yml", "warning", issues
    )
    if ci is not None:
        lowered = ci.lower()
        if "pytest" not in lowered:
            issues.append(
                Issue(
                    "warning",
                    "ci-pytest",
                    "CI should run the test suite",
                    ".github/workflows/ci.yml",
                )
            )
        if "qgis" not in lowered:
            issues.append(
                Issue(
                    "warning",
                    "ci-qgis",
                    "CI should exercise a QGIS 3 runtime",
                    ".github/workflows/ci.yml",
                )
            )
        for line in ci.splitlines():
            if not re.search(r"\b(?:pip|pip3)\s+install\b", line):
                continue
            if re.search(r"\b(?:PyQt5|PyQt6|qgis)\b", line, re.IGNORECASE):
                issues.append(
                    Issue(
                        "error",
                        "ci-direct-qt",
                        "do not install Qt or PyQGIS from PyPI in CI",
                        ".github/workflows/ci.yml",
                    )
                )

    tests_dir = project / "tests"
    if not tests_dir.is_dir():
        issues.append(
            Issue(
                "warning",
                "tests-missing",
                "add tests outside the plugin package",
                "tests",
            )
        )
    else:
        _require_file(project, "tests/conftest.py", "warning", issues)
        _require_file(project, "tests/test_plugin.py", "warning", issues)

    _require_file(project, "docs/development.md", "warning", issues)

    if not (project / "LICENSE").is_file() and not (
        project / "LICENSE.md"
    ).is_file():
        issues.append(
            Issue(
                "warning",
                "license-missing",
                "add a license file chosen for this project",
                "LICENSE",
            )
        )


def _plugin_issues(project, plugin, issues):
    if plugin == project:
        relative = "."
    else:
        try:
            relative = plugin.relative_to(project).as_posix()
        except ValueError:
            relative = str(plugin)
    for issue in collect_issues(plugin):
        path = issue.path
        if path:
            path = "{}/{}".format(relative, path) if relative != "." else path
        else:
            path = relative
        issues.append(
            Issue(issue.level, issue.rule, issue.message, path, issue.line)
        )


def _as_json(project, plugin, issues, strict):
    errors, warnings = counts(issues)
    return {
        "ok": errors == 0 and (not strict or warnings == 0),
        "project": str(project),
        "plugin": str(plugin) if plugin is not None else None,
        "strict": strict,
        "errors": errors,
        "warnings": warnings,
        "issues": [issue.to_dict() for issue in issues],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check a QGIS 3 plugin project and its plugin directory."
    )
    parser.add_argument("project", help="path to the project root")
    parser.add_argument("--plugin", help="plugin directory, relative to the project")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as failures"
    )
    args = parser.parse_args(argv)

    project = Path(args.project)
    if not project.is_dir():
        issue = Issue(
            "error",
            "project-missing",
            "project directory does not exist",
            str(project),
        )
        if args.json:
            print(json.dumps(_as_json(project, None, [issue], args.strict)))
        else:
            print_issues([issue])
        return EXIT_MISSING

    issues = []
    _check_project_files(project, issues)
    _check_generator_residue(project, issues)

    plugin = None
    if args.plugin:
        plugin = Path(args.plugin)
        if not plugin.is_absolute():
            plugin = project / plugin
        if not plugin.is_dir():
            issues.append(
                Issue(
                    "error",
                    "plugin-missing",
                    "plugin directory does not exist",
                    str(plugin),
                )
            )
            plugin = None
    else:
        plugin, error = _find_plugin(project)
        if error:
            issues.append(
                Issue("warning", "plugin-not-found", error, ".")
            )

    if plugin is not None:
        _plugin_issues(project, plugin, issues)

    issues.sort(
        key=lambda issue: (
            issue.path or "",
            issue.line if issue.line is not None else 0,
            issue.rule,
        )
    )
    errors, warnings = counts(issues)

    if args.json:
        print(json.dumps(_as_json(project, plugin, issues, args.strict), indent=2))
    else:
        print_issues(issues)

    if errors:
        return EXIT_FAILURE
    if args.strict and warnings:
        return EXIT_FAILURE
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
