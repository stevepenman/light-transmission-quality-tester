# Architecture and data flow

## Measurement sequence

1. Select a bank/position for a batch test; single mode has no batch position.
2. Reject overlapping starts and confirm duplicate or completed-batch actions.
3. Read ambient light with the simulated relay off. Any channel over 500 lx blocks the start.
4. Set the relay state high in memory. A Qt single-shot timer allows a three-second stabilisation interval.
5. Select each virtual multiplexer channel, wait briefly, and read it once.
6. Switch the simulated relay off in a `finally` block, including when a read raises an exception.
7. Reject missing, non-finite, or negative readings. Above 500 lx means lid open; otherwise apply the four saved upper limits.
8. Update the UI and, when requested, history and total count. Only PASS/FAIL advance batch positions; failed reads do not record a result.

Window closure also attempts relay shutdown and mock GPIO cleanup. This demonstrates cleanup logic; it is not evidence of electrical safety.

## Local state

All mutable files use `runtime_paths.data_directory()`. The default `.demo-data/` is excluded from Git.

| Runtime file | Data |
| --- | --- |
| `history.json` | Latest 90 display strings |
| `weekly_history.json` | Timestamp/result records accumulated for reporting |
| `stats.json` | Lifetime count independent of recent history |
| `batch_state.json` | Completed combinations, selection, and cycle start |
| `calibration_settings.json` | Channel limits and optional locked reference/audit fields |
| `email_settings.json` | Inert example settings; no saved credential or gate password |

`_write_json_atomic` writes a temporary sibling file and replaces the target. This prevents partially written individual JSON files but does not coordinate updates across several files. A single GUI instance is assumed.

The logger is a process-wide singleton initialised on first use. Set `WTT_DATA_DIR` before importing the GUI to control its output directory. The headless runner and screenshot generator do so, and close logging handlers before deleting temporary files on Windows.

## Calibration

The master capture averages three runs. Every channel must have a spread within `max(2 lx, 2% of its average)` before the reference can be locked. Verification compares one run with the stored reference using a similar tolerance. Audit fields are local fictional demo entries. PASS/FAIL limits remain separately editable.

## Reporting

`ExcelReportGenerator` builds four styled worksheets with openpyxl. It parses the existing textual result format rather than importing a database. A separator hyphen after a channel letter is removed before numeric conversion, preserving positive lux values. Unknown results may appear in imported data; the supplied report example contains only PASS and FAIL.

The report command loads only the two checked-in synthetic fixtures. Workbook generation timestamps and filenames use the machine's clock. Generated workbooks, logs, and GUI state are excluded from publication.

## Offline boundary

The application imports mocks unconditionally; no auto-detection or real-bus creation remains. The retained `TCA9548A` and `BH1750` classes document protocol operations but are not wired into startup. Email methods return without sending and the scheduling entry point starts no thread. There is no runtime switch to enable live delivery or equipment.

The CI runner must download dependencies and Actions components. That infrastructure network activity is separate from the application, which has no outbound integration in this edition.
