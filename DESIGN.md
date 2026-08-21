# Design Document — eSim Automated Tool Manager

FOSSEE Semester Long Internship, Autumn 2026 — Screening Task 5 (Tool Manager)
Scope covered: **Requirement 1 (Tool Installation Management)** and
**Requirement 4 (Dependency Checker)**.

## 1. Problem framing

eSim depends on external tools (Ngspice, KiCad) that users currently install
and manage by hand — a process that's tedious and error-prone across
different machines. The task asks for a tool that automates installation
and version-checking, and can tell a user what's missing before something
breaks.

Two implementation paths exist for "installation":

1. Reimplement downloading, building, and installing each tool from source.
2. Wrap the OS's existing package manager (`apt`, `choco`) and add
   version-verification and dependency-checking around it.

This project deliberately takes path 2. Reimplementing installers is out of
scope for a screening task, duplicates work the OS already does reliably,
and is explicitly listed as a **bonus** requirement ("integration with
popular package managers") — so wrapping the package manager satisfies the
core requirement and the bonus at the same time, with one code path.

## 2. Scope decision

Only 2 of the 6 requirements are mandatory. This submission targets:

- **R1 — Tool Installation Management**: install a tool via the OS package
  manager, skip cleanly if already present, verify success by re-checking
  the installed version.
- **R4 — Dependency Checker**: before installing, verify the package
  manager itself is available and that each tool's supporting binaries
  (e.g. `gcc`, `make` for Ngspice) are present — report clearly, don't
  guess or install anything as a side effect.

**R1 is effectively non-negotiable** regardless of which two requirements
are formally chosen — the task's deliverables section separately requires
the prototype to "demonstrate at least tool installation and version
checking." R4 was chosen as the second requirement because it shares the
same subprocess/registry infrastructure as R1 (no second subsystem to
build), keeping the implementation small enough to finish completely and
test properly rather than half-covering more requirements.

R2 (auto-update) and R3 (config/env-var management) were deliberately not
attempted. R2 needs a real "check latest available version" source per
tool (out of scope for the time available); R3 involves OS-specific
environment/PATH mutation that is easy to get subtly wrong and hard to
verify without a live eSim install to test against. Attempting either
would have traded a fully-working R1+R4 for a partially-working four
requirements — a worse outcome on the stated evaluation criteria
(functionality, code quality).

## 3. Architecture

```
                    CLI (cli.py, argparse)
                 list | status | check-deps | install
                              |
                              v
                Tool Registry (tools_registry.json)
        name -> {apt_package, choco_package, check_command,
                  version_regex, required_dependencies}
                              |
              +---------------+---------------+
              |                               |
              v                               v
   dependency_checker.py              installer.py
   - is package manager present?      - depends on dependency_checker
   - are required_dependencies          (pre-install check, abortable)
     on PATH?                         - builds + runs install command
   - read-only, never installs          via platform_utils
                              \\             /
                               v           v
                          version_utils.py
                    runs check_command, applies
                    version_regex, returns version
                              |
                              v
                       logger_setup.py
                 timestamped log -> logs/tool_manager.log
                        + console output
```

Every module reads the registry rather than hardcoding tool-specific
logic, so adding a new tool is a JSON edit, not a code change.

## 4. Module breakdown

| Module | Responsibility | Notes |
|---|---|---|
| `platform_utils.py` | Detect OS; map OS to package manager (`apt`/`choco`); check the package manager binary is on PATH. | Single source of truth for "what OS am I on" — nothing else re-implements this. |
| `config.py` | Load and validate `tools_registry.json`. | Keeps the JSON schema in one place. |
| `dependency_checker.py` | Report-only check: package manager availability + each tool's `required_dependencies`. Returns a structured `DependencyReport`, never installs. | Safe to run standalone (`check-deps`) any time. |
| `installer.py` | Orchestrates install: pre-checks via `dependency_checker`, skips if already installed (idempotent), runs the install command, verifies via `version_utils`. Returns a structured `InstallResult` — no silent failures. | The only module that runs a mutating command. |
| `version_utils.py` | Runs each tool's `check_command`, applies its `version_regex`, returns a parsed version string or `None`. | Shared by both R1 (post-install verification) and `status`. |
| `logger_setup.py` | Configures `logging` to write timestamped entries to `logs/tool_manager.log` and echo to console. | Satisfies the "log of actions taken" expectation without being counted as a formal requirement. |
| `cli.py` | `argparse`-based entry point: `list`, `status`, `check-deps`, `install`. | Thin — delegates all logic to the modules above. |

## 5. Error handling philosophy

Every operation that can fail returns a structured result
(`InstallResult`, `DependencyReport`) rather than raising past its own
boundary or printing and continuing. This means:

- The CLI decides how to present failure, not the internal modules.
- A failed install still reports partial state (e.g. "package manager
  missing" vs. "install command failed" vs. "installed but version
  unverifiable") instead of a generic error.
- Tests can assert on structured fields instead of parsing text output.

## 6. Testing approach

12 unit tests (`unittest` + `unittest.mock`) cover `dependency_checker`,
`installer`, and `version_utils` by mocking `subprocess.run` and
`shutil.which` — so the suite is deterministic and doesn't require actually
having `apt`/`choco`/Ngspice present, and gives the same result on any
machine, including CI.

## 7. Known limitations

See the "Known limitations" section in `README.md` — listed there rather
than duplicated here to avoid the two documents drifting out of sync.
