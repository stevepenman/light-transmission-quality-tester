# Verification results

Verification date: 25 October 2026.

## Environment and results

Local execution used the workspace's existing Windows environment: Python 3.14.2, PyQt5 5.15.9, and openpyxl 3.1.2. The package versions match `requirements.txt`. Paths and machine identifiers are intentionally omitted.

| Check | Result |
| --- | --- |
| `python -m unittest discover -s tests -v` | **29 tests passed**, including the 24 retained application tests and five portfolio regression tests |
| Compilation of application, tests, and tools with `compileall` | Passed |
| Python 3.11 / 3.12 source grammar checks | Passed using the local interpreter's AST parser; these are not target-runtime tests |
| `python demo.py --headless --scenario pass` | Passed: PASS recorded, one batch position complete, simulated relay off |
| `python demo.py --headless --scenario fail` | Passed: FAIL recorded, one batch position complete, simulated relay off |
| `python demo.py --headless --scenario lid-open` | Passed: blocked before measurement, no history or batch advancement, simulated relay off |
| `python demo.py --report` | Passed: four-sheet synthetic workbook generated locally |
| Workbook regression checks | Passed: expected sheet names, nonnegative channel values, two PASS and two FAIL rows, empty-data handling |
| `python tools/capture_demo.py` | Passed: newly generated 800 × 480 synthetic screenshot; visually reviewed |
| `python tools/check_publication.py` | Passed: no findings in final Git publication candidates |
| Private review of final candidate paths/content | No known identifying terms or embedded original access codes found |
| Original-file integrity | SHA-256 hashes of all 57 original non-environment, non-cache, non-Git files unchanged |
| Fresh local Git repository | Initialised on `main`; no commits, remotes, copied history, or upload |

The sensor-exception regression intentionally logs a simulated read failure. That output is expected; the assertion verifies relay shutdown and absence of a recorded result. PyQt/SIP and openpyxl emitted deprecation warnings on Python 3.14; warnings were not suppressed or reported as failures.

## Defects corrected during preparation

- Excel parsing treated the UI's channel separator hyphen as a numeric minus sign; the portfolio parser now reads the emitted nonnegative lux values correctly.
- Invalid non-finite, negative, missing, or excess readings are rejected before result formatting and recording.
- Redundant overridden methods and unused legacy UI construction were removed so the active workflow is easier to inspect.
- New headless checks initially exposed locked temporary log files on Windows. Explicit logger shutdown fixed cleanup; all three scenarios subsequently exited successfully.
- Workbook tests initially retained reader handles. Explicit binary file contexts fixed their cleanup; the final suite passed.

The final successful runs supersede those intermediate failures. A temporary publication scan performed while tests were creating/deleting fixture files saw one transient unreadable file; the final scan ran after test cleanup and had no findings.

## Not verified or unresolved

- **Fresh dependency installation did not succeed in this session.** The `py` launcher was inaccessible. A new environment created with the available interpreter started pip, but pip reported no matching distribution for the pinned PyQt5 version. The exact cause was not established. The unsuccessful environment was removed; no replacement package bundle was copied into this repository. Repeat installation on the intended desktop, preferably using the Python 3.11/3.12 CI target, before relying on this setup.
- GitHub Actions is configured for Windows with Python 3.11 and 3.12 but has not run on GitHub. Source grammar checks do not establish package availability or runtime compatibility there.
- Physical equipment, touch input on a real panel, Raspberry Pi drivers, sensor accuracy, calibration validity, lid detection, and electrical shutdown behaviour were not tested.
- No real email or external-service delivery was attempted; those application paths were removed or made inert.
- No physical thickness calculation, performance benchmark, production deployment, or business impact was established.
- Sanitisation and a clean heuristic scan do not resolve ownership or publication permission. See [PUBLICATION_REVIEW.md](PUBLICATION_REVIEW.md).
