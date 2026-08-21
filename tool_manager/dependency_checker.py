"""
dependency_checker.py
----------------------
Implements Requirement 4: Dependency Checker.

Two things are checked, independently:
  1. Is the OS package manager itself available? (apt / choco)
  2. Are each tool's `required_dependencies` (other binaries it
     needs, e.g. gcc/make for building ngspice from source) present
     on PATH?

This module never installs anything — it only reports. That
separation matters: `check-deps` should be safe to run any time,
including before you decide whether to install at all.
"""

import shutil
from dataclasses import dataclass, field
from typing import Optional

from tool_manager import platform_utils


@dataclass
class DependencyReport:
    tool_name: str
    package_manager: Optional[str]
    package_manager_available: bool
    dependencies: dict = field(default_factory=dict)  # dep_name -> bool

    @property
    def all_satisfied(self) -> bool:
        return self.package_manager_available and all(self.dependencies.values())

    @property
    def missing(self) -> list:
        return [dep for dep, ok in self.dependencies.items() if not ok]


def check_binary(binary_name: str) -> bool:
    """Return True if `binary_name` is found on PATH."""
    return shutil.which(binary_name) is not None


def check_dependencies(tool_name: str, tool_config: dict) -> DependencyReport:
    """
    Run the full dependency check for one tool and return a report.

    tool_config is the dict for this tool from the registry (see
    config.py) — must contain 'required_dependencies'.
    """
    pm = platform_utils.get_package_manager()
    pm_available = platform_utils.is_package_manager_available(pm) if pm else False

    dep_results = {
        dep: check_binary(dep) for dep in tool_config.get("required_dependencies", [])
    }

    return DependencyReport(
        tool_name=tool_name,
        package_manager=pm,
        package_manager_available=pm_available,
        dependencies=dep_results,
    )


def format_report(report: DependencyReport) -> str:
    """Human-readable rendering of a DependencyReport for CLI output."""
    lines = [f"Dependency check for '{report.tool_name}':"]

    if report.package_manager is None:
        lines.append("  [FAIL] No supported package manager for this OS.")
    else:
        status = "OK" if report.package_manager_available else "MISSING"
        lines.append(f"  [{status}] Package manager: {report.package_manager}")

    if not report.dependencies:
        lines.append("  (no additional dependencies declared)")
    else:
        for dep, ok in report.dependencies.items():
            status = "OK" if ok else "MISSING"
            lines.append(f"  [{status}] {dep}")

    overall = "ALL DEPENDENCIES SATISFIED" if report.all_satisfied else "MISSING DEPENDENCIES"
    lines.append(f"  => {overall}")
    return "\n".join(lines)