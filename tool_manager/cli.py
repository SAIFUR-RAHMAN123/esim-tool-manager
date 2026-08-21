"""
cli.py
------
Command-line entry point for the eSim Automated Tool Manager.

Commands:
  list                  Show all tools known to the registry.
  status  [tool]        Show installed/version status (one tool or all).
  check-deps [tool]     Run the dependency checker (one tool or all).
  install <tool>        Install a tool (with a pre-flight dependency check).

Kept intentionally thin: this module only parses args and prints
results — all real logic lives in the other modules so it stays
testable without shelling out to the CLI itself.
"""

import argparse
import sys

from tool_manager import config, dependency_checker, installer, platform_utils, version_utils
from tool_manager.logger_setup import setup_logger

logger = setup_logger()


def cmd_list(args, registry: dict) -> int:
    print("Tools known to the registry:\n")
    for name, cfg in sorted(registry.items()):
        print(f"  {name:12s} - {cfg['description']}")
    return 0


def cmd_status(args, registry: dict) -> int:
    tool_names = [args.tool] if args.tool else sorted(registry.keys())
    exit_code = 0
    for name in tool_names:
        try:
            cfg = config.get_tool_config(name, registry)
        except config.ToolNotFoundError as exc:
            logger.error(str(exc))
            exit_code = 1
            continue

        try:
            version = version_utils.get_installed_version(cfg)
        except version_utils.VersionCheckError as exc:
            logger.error(f"[{name}] version check failed: {exc}")
            exit_code = 1
            continue

        if version:
            print(f"  {name:12s} INSTALLED  (version {version})")
        else:
            print(f"  {name:12s} NOT INSTALLED")
    return exit_code


def cmd_check_deps(args, registry: dict) -> int:
    tool_names = [args.tool] if args.tool else sorted(registry.keys())
    exit_code = 0

    pm_summary = platform_utils.get_platform_summary()
    print(f"Platform: {pm_summary['os']}  |  Package manager: {pm_summary['package_manager']}\n")

    for name in tool_names:
        try:
            cfg = config.get_tool_config(name, registry)
        except config.ToolNotFoundError as exc:
            logger.error(str(exc))
            exit_code = 1
            continue

        report = dependency_checker.check_dependencies(name, cfg)
        print(dependency_checker.format_report(report))
        print()
        if not report.all_satisfied:
            exit_code = 1

    return exit_code


def cmd_install(args, registry: dict) -> int:
    try:
        cfg = config.get_tool_config(args.tool, registry)
    except config.ToolNotFoundError as exc:
        logger.error(str(exc))
        return 1

    logger.info(f"Running pre-install dependency check for '{args.tool}'...")
    dep_report = dependency_checker.check_dependencies(args.tool, cfg)
    print(dependency_checker.format_report(dep_report))

    if not dep_report.all_satisfied and not args.force:
        logger.warning(
            f"Dependencies not fully satisfied for '{args.tool}'. "
            f"Missing: {dep_report.missing or ['package manager']}. "
            "Re-run with --force to attempt install anyway."
        )
        return 1

    logger.info(f"Installing '{args.tool}'...")
    result = installer.install_tool(args.tool, cfg)

    if result.success:
        logger.info(f"{result.message} (version: {result.version})")
        return 0
    else:
        logger.error(result.message)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tool_manager",
        description="eSim Automated Tool Manager - install, check, and report on external tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all tools known to the registry.")

    p_status = subparsers.add_parser("status", help="Show installed version status.")
    p_status.add_argument("tool", nargs="?", help="Tool name (omit for all tools).")

    p_deps = subparsers.add_parser("check-deps", help="Check dependencies for a tool.")
    p_deps.add_argument("tool", nargs="?", help="Tool name (omit for all tools).")

    p_install = subparsers.add_parser("install", help="Install a tool.")
    p_install.add_argument("tool", help="Tool name (must exist in the registry).")
    p_install.add_argument(
        "--force",
        action="store_true",
        help="Attempt installation even if dependency checks fail.",
    )

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        registry = config.load_registry()
    except config.RegistryError as exc:
        logger.error(f"Failed to load tool registry: {exc}")
        return 2

    dispatch = {
        "list": cmd_list,
        "status": cmd_status,
        "check-deps": cmd_check_deps,
        "install": cmd_install,
    }
    return dispatch[args.command](args, registry)


if __name__ == "__main__":
    sys.exit(main())
