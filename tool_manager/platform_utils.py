"""
platform_utils.py
------------------
Detects the operating system and the package manager to use for it.

Kept deliberately small: this is the ONLY module that should ever
call platform.system(). Every other module asks this one "what OS
am I on / what package manager should I use", instead of sprinkling
platform checks throughout the codebase.
"""

import platform
import shutil
from typing import Optional


SUPPORTED_PACKAGE_MANAGERS = {
    "Linux": "apt",
    "Windows": "choco",
}


def get_os() -> str:
    """Return 'Linux', 'Windows', 'Darwin', etc. (platform.system() value)."""
    return platform.system()


def get_package_manager() -> Optional[str]:
    """
    Return the expected package manager name for the current OS,
    or None if this OS isn't supported by the tool manager yet
    (e.g. macOS — see DESIGN.md for why it's out of scope for now).
    """
    return SUPPORTED_PACKAGE_MANAGERS.get(get_os())


def is_package_manager_available(pm_name: str) -> bool:
    """
    Check whether a package manager binary is actually on PATH.

    Knowing "this OS should use apt" isn't the same as "apt is
    installed and callable" — e.g. some minimal containers strip
    it out. This check prevents the installer from assuming a
    tool exists and failing with a confusing subprocess error later.
    """
    return shutil.which(pm_name) is not None


def get_platform_summary() -> dict:
    """Convenience bundle used by the CLI's `list`/status output."""
    pm = get_package_manager()
    return {
        "os": get_os(),
        "package_manager": pm,
        "package_manager_available": is_package_manager_available(pm) if pm else False,
    }