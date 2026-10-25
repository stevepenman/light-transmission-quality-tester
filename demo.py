"""Run a synthetic GUI demonstration, an offscreen smoke test, or a local report."""

import argparse
import json
import logging
import os
from pathlib import Path
import tempfile


def generate_report():
    from excel_export import ExcelReportGenerator

    examples = Path(__file__).parent / "examples"
    data = json.loads((examples / "synthetic_weekly_history.json").read_text(encoding="utf-8"))
    calibration = json.loads((examples / "synthetic_calibration.json").read_text(encoding="utf-8"))
    path = ExcelReportGenerator().generate_weekly_report(
        data, {"total_tests_count": len(data)}, calibration
    )
    if path is None:
        raise RuntimeError("Synthetic report generation failed")
    print(f"SYNTHETIC DEMO ONLY - local workbook: {path}")


def run_gui(headless, scenario):
    if headless:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["WTT_DEMO_SCENARIO"] = scenario
    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QApplication
    import ui

    app = QApplication([])
    gui = ui.BottleTesterGUI()
    gui.show()
    if not headless:
        print(f"SYNTHETIC DEMO ONLY - scenario: {scenario}; demo gate: demo")
        return app.exec_()

    # No modal warning can stall the automated lid-open scenario.
    gui.show_warning = lambda *_args: None
    gui.show_error = lambda *_args: None
    gui.idle_timer.stop()
    gui.run_test_sequence()

    def finish():
        expected = {"pass": "PASS", "fail": "FAIL", "lid-open": "CLOSE LID"}[scenario]
        expected_count = 0 if scenario == "lid-open" else 1
        ok = (
            gui.batch_result_label.text() == expected
            and len(gui.history_entries) == expected_count
            and not gui.test_in_progress
            and ui.GPIO.pin_states[gui.LED_PIN] == ui.GPIO.LOW
            and len(gui.tested_combinations) == expected_count
        )
        print(f"SYNTHETIC {scenario}: {'OK' if ok else 'FAILED'}; "
              f"result={gui.batch_result_label.text()}; recorded={len(gui.history_entries)}")
        gui.close()
        app.exit(0 if ok else 1)

    QTimer.singleShot(4500, finish)
    return app.exec_()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--headless", action="store_true", help="Check a complete sequence offscreen")
    mode.add_argument("--report", action="store_true", help="Write a local synthetic Excel workbook")
    parser.add_argument("--scenario", choices=("pass", "fail", "lid-open"), default="pass")
    args = parser.parse_args()
    if args.report:
        generate_report()
        return 0
    if args.headless:
        # A clean sandbox makes the smoke check independent of interactive history.
        with tempfile.TemporaryDirectory(prefix="light-transmission-demo-") as data_dir:
            os.environ["WTT_DATA_DIR"] = data_dir
            try:
                return run_gui(True, args.scenario)
            finally:
                logging.shutdown()  # Release Windows file handles before cleanup.
    return run_gui(False, args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
