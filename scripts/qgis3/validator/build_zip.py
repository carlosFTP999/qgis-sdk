import argparse
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True

from report import counts, print_issues
from run_all import collect_issues

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_MISSING = 2
EXCLUDED_PARTS = {
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "tests",
    "test",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".zip"}


def should_include(path, root, output):
    if path.resolve() == output.resolve():
        return False
    relative = path.relative_to(root)
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if any(part.startswith(".") for part in relative.parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build a QGIS 3 plugin ZIP.")
    parser.add_argument("plugin", help="path to the plugin directory")
    parser.add_argument("--output", help="output ZIP path")
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="build without static validation (debugging only)",
    )
    args = parser.parse_args(argv)

    plugin = Path(args.plugin)
    if not plugin.is_dir():
        print(
            "{}: ERROR: plugin-missing: plugin directory does not exist".format(
                plugin
            )
        )
        return EXIT_MISSING

    if not args.skip_validation:
        issues = collect_issues(plugin)
        errors, _ = counts(issues)
        if errors:
            print_issues(issues)
            print("ZIP not created because validation failed.")
            return EXIT_FAILURE

    output = (
        Path(args.output)
        if args.output
        else plugin.parent / "{}.zip".format(plugin.name)
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(plugin.rglob("*")):
            if not path.is_file():
                continue
            if not should_include(path, plugin, output):
                continue
            relative = path.relative_to(plugin).as_posix()
            info = zipfile.ZipInfo("{}/{}".format(plugin.name, relative))
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())

    print("Created {}".format(output))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
