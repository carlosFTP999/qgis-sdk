import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import check_rules
import check_structure
import check_syntax
from report import as_json, counts, print_issues

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_MISSING = 2


def collect_issues(plugin):
    plugin = Path(plugin)
    if not plugin.is_dir():
        from report import Issue

        return [Issue("error", "plugin-missing", "plugin directory does not exist", str(plugin))]
    issues = []
    issues.extend(check_structure.collect(plugin))
    issues.extend(check_syntax.collect(plugin))
    issues.extend(check_rules.collect(plugin))
    return sorted(
        issues,
        key=lambda issue: (
            issue.path or "",
            issue.line if issue.line is not None else 0,
            issue.rule,
        ),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a QGIS plugin directory with static checks."
    )
    parser.add_argument("plugin", help="path to the plugin directory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as failures"
    )
    args = parser.parse_args(argv)

    plugin = Path(args.plugin)
    if not plugin.is_dir():
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "plugin": str(plugin),
                        "strict": args.strict,
                        "errors": 1,
                        "warnings": 0,
                        "issues": [
                            {
                                "level": "error",
                                "rule": "plugin-missing",
                                "message": "plugin directory does not exist",
                                "path": str(plugin),
                                "line": None,
                            }
                        ],
                    }
                )
            )
        else:
            print(f"{plugin}: ERROR: plugin-missing: plugin directory does not exist")
        return EXIT_MISSING

    issues = collect_issues(plugin)
    errors, warnings = counts(issues)

    if args.json:
        print(json.dumps(as_json(plugin, issues, strict=args.strict), indent=2))
    else:
        print_issues(issues)

    if errors:
        return EXIT_FAILURE
    if args.strict and warnings:
        return EXIT_FAILURE
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
