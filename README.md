# eSim Automated Tool Manager

Screening Task 5 (Tool Manager) submission — FOSSEE Semester Long Internship, Autumn 2026.

Automates **Tool Installation Management (Requirement 1)** and **Dependency
Checking (Requirement 4)** for external tools used by eSim (Ngspice, KiCad),
by wrapping the OS package manager (`apt` on Linux, `choco` on Windows) and
verifying results with real version checks.

See [`DESIGN.md`](DESIGN.md) for architecture and design rationale.

## Requirements

- Python 3.10+ (uses the `X | None` type-hint syntax)
- No third-party packages — standard library only
- Linux: `apt-get` (and `sudo` if not running as root)
- Windows: [Chocolatey](https://chocolatey.org/) (`choco`) installed and on PATH

## Installation

```bash
git clone <your-repo-url>
cd esim-tool-manager
# No pip install needed — stdlib only.
```

## Usage

All commands run through the CLI module:

```bash
python3 -m tool_manager.cli <command> [args]
```

### List all tools the manager knows about

```bash
python3 -m tool_manager.cli list
```

### Check installed status / version of a tool (or all tools)

```bash
python3 -m tool_manager.cli status
python3 -m tool_manager.cli status ngspice
```

### Run the dependency checker

```bash
python3 -m tool_manager.cli check-deps
python3 -m tool_manager.cli check-deps ngspice
```

Checks two things: whether the OS package manager is available, and
whether each tool's required supporting binaries (e.g. `gcc`, `make`)
are on PATH. Safe to run any time — never installs anything.

### Install a tool

```bash
python3 -m tool_manager.cli install ngspice
```

- Runs a dependency check first; aborts if unsatisfied (pass `--force`
  to install anyway).
- Skips cleanly (does not re-download) if the tool is already installed.
- Verifies success by re-checking the installed version afterwards.
- On Linux this runs `sudo apt-get install -y <package>` — you will be
  prompted for your sudo password if not already cached, or it must be
  run as root in a non-interactive environment.

### Example session

```
$ python3 -m tool_manager.cli check-deps ngspice
Platform: Linux  |  Package manager: apt

Dependency check for 'ngspice':
  [OK] Package manager: apt
  [OK] gcc
  [OK] make
  => ALL DEPENDENCIES SATISFIED

$ python3 -m tool_manager.cli install ngspice
Running pre-install dependency check for 'ngspice'...
Dependency check for 'ngspice':
  [OK] Package manager: apt
  [OK] gcc
  [OK] make
  => ALL DEPENDENCIES SATISFIED
Installing 'ngspice'...
'ngspice' installed successfully. (version: 42)

$ python3 -m tool_manager.cli status ngspice
  ngspice      INSTALLED  (version 42)
```

All of the above runs are also written to `logs/tool_manager.log`
with timestamps.

## Adding a new tool

Add an entry to `tool_manager/tools_registry.json`:

```json
"newtool": {
    "description": "What it is.",
    "apt_package": "newtool-apt-name",
    "choco_package": "newtool-choco-name",
    "check_command": ["newtool", "--version"],
    "version_regex": "(\\d+\\.\\d+\\.\\d+)",
    "required_dependencies": ["somebinary"]
}
```

No code changes needed — every module reads from this registry.

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

12 unit tests covering the dependency checker, version parser, and
installer, using `unittest.mock` to simulate subprocess calls — so the
suite runs the same on any machine, regardless of what's actually
installed.

## Project structure

```
esim-tool-manager/
├── README.md
├── DESIGN.md
├── requirements.txt
├── .gitignore
├── tool_manager/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── tools_registry.json
│   ├── platform_utils.py
│   ├── dependency_checker.py
│   ├── installer.py
│   ├── version_utils.py
│   └── logger_setup.py
├── logs/                  # created at runtime, log file is gitignored
├── tests/
│   ├── test_dependency_checker.py
│   ├── test_version_utils.py
│   └── test_installer.py
└── docs/
```

## Known limitations (honest scope notes)

- Only Linux (`apt`) and Windows (`choco`) are wired up; macOS
  (`brew`) is a straightforward extension (see DESIGN.md) but out of
  scope for this screening task.
- Requirement 2 (auto-update) and Requirement 3 (config/env-var
  management) were intentionally **not** attempted — this submission
  targets R1 + R4 to keep the scope realistic and the implementation
  fully working rather than partially covering more requirements.
- `install` currently requires the tool's package name to exist in
  the OS's default repositories; it does not add third-party
  repositories (e.g. a KiCad PPA) automatically.
