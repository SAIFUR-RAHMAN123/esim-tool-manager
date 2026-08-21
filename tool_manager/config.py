"""
config.py
---------
Loads and validates the tool registry (tools_registry.json).

The registry is the single source of truth for every tool the manager
knows about: what package to install, how to check its version, and
what it depends on. Keeping this as data (JSON) instead of hard-coded
logic means adding a new supported tool never requires touching
installer.py or version_utils.py.
"""

import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent / "tools_registry.json"

REQUIRED_FIELDS = [
    "description",
    "apt_package",
    "choco_package",
    "check_command",
    "version_regex",
    "required_dependencies",
]


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not present in the registry."""


class RegistryError(Exception):
    """Raised when the registry file itself is missing or malformed."""


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    """
    Load and validate tools_registry.json.

    Returns a dict keyed by tool name. Raises RegistryError if the
    file can't be read/parsed, or if any entry is missing required
    fields — better to fail loudly at startup than to crash deep
    inside the installer later with a confusing KeyError.
    """
    if not path.exists():
        raise RegistryError(f"Registry file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise RegistryError(f"Registry file is not valid JSON: {exc}") from exc

    for tool_name, tool_config in data.items():
        missing = [field for field in REQUIRED_FIELDS if field not in tool_config]
        if missing:
            raise RegistryError(
                f"Tool '{tool_name}' in registry is missing fields: {missing}"
            )

    return data


def get_tool_config(tool_name: str, registry: dict) -> dict:
    """Fetch a single tool's config, raising a clear error if unknown."""
    if tool_name not in registry:
        available = ", ".join(sorted(registry.keys())) or "(none)"
        raise ToolNotFoundError(
            f"Unknown tool '{tool_name}'. Available tools: {available}"
        )
    return registry[tool_name]
