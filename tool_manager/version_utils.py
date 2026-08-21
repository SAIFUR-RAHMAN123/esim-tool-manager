"""
version_utils.py
-----------------
Runs a tool's version-check command and extracts a clean version
string using the regex declared for it in the registry.

Split out from installer.py because "is X installed, and which
version" is useful on its own (e.g. running `version ngspice`
without ever installing anything), and because the installer
calls this right after installing to confirm success.
"""

import re
import shutil
import subprocess
from typing import Optional


class VersionCheckError(Exception):
    """Raised when a version cannot be determined."""


def is_installed(tool_config: dict) -> bool:
    """Quick check: is the tool's binary even on PATH?"""
    command = tool_config["check_command"]
    return shutil.which(command[0]) is not None


def get_installed_version(
    tool_config: dict, timeout: int = 10
) -> Optional[str]:
    """
    Run the tool's check_command and parse its version.

    Returns the matched version string, or None if the tool isn't
    installed / the command failed / the output didn't match the
    expected pattern. Never raises for "not installed" — that's an
    expected, normal outcome, not an error condition. Genuine
    unexpected failures (e.g. command exists but times out) still
    raise VersionCheckError so callers don't silently misreport them
    as "not installed".
    """
    command = tool_config["check_command"]

    if shutil.which(command[0]) is None:
        return None

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise VersionCheckError(
            f"Timed out running '{' '.join(command)}'"
        ) from exc
    except OSError as exc:
        raise VersionCheckError(
            f"Could not run '{' '.join(command)}': {exc}"
        ) from exc

    # Some tools (e.g. ngspice -v) write version info to stderr, not stdout.
    output = f"{result.stdout}\n{result.stderr}"

    match = re.search(tool_config["version_regex"], output)
    if not match:
        return None

    return match.group(1)