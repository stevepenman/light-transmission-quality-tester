import json
import os
import sys
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton

import ui


class FixedSensor:
    def __init__(self, value):
        self.value = value

    def measure_high_res(self):
        if isinstance(self.value, BaseException):
            raise self.value
        return self.value


class WallThicknessTesterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(dir=os.path.join(ROOT, "tests"))
        os.environ["WTT_DATA_DIR"] = self.temp_dir.name
        self.scheduler_patch = mock.patch.object(
            ui.BottleTesterGUI, "start_weekly_email_scheduler", lambda _self: None
        )
        self.scheduler_patch.start()
        self.gui = ui.BottleTesterGUI()
        self.gui.show()
        self.app.processEvents()
        self.gui.show_warning = mock.Mock()
        self.gui.show_error = mock.Mock()
        self.gui.show_success = mock.Mock()

    def tearDown(self):
        self.gui.hide_screensaver()
        self.gui.close()
        self.app.processEvents()
        self.scheduler_patch.stop()
        self.temp_dir.cleanup()

    def new_gui(self):
        widget = ui.BottleTesterGUI()
        widget.show_warning = mock.Mock()
        widget.show_error = mock.Mock()
        widget.show_success = mock.Mock()
        return widget

    def test_exactly_18_cavity_combinations_in_canonical_order(self):
        order = self.gui.cavity_order()
        self.assertEqual(18, len(order))
        self.assertEqual(18, len(set(order)))
        self.assertEqual("A+2", order[0])
        self.assertEqual("C+7", order[-1])

    def test_cavity_selector_only_allows_valid_bank_and_position(self):
        self.gui.cavity_selector.select("B", "6")
        self.assertEqual(("B", "6"), self.gui.cavity_selector.selection())
        self.assertEqual(1, sum(self.gui.part_checkboxes[x].isChecked() for x in "ABC"))
        self.assertEqual(1, sum(self.gui.part_checkboxes[x].isChecked() for x in "234567"))

    def test_cavity_advancement_uses_first_remaining_combination(self):
        self.gui.tested_combinations = {"A+2"}
        self.gui.advance_to_next_cavity()
        self.assertEqual(("A", "3"), (self.gui.selected_bank, self.gui.selected_position))

    def test_batch_progress_restores_from_additive_state_file(self):
        self.gui.tested_combinations = {"A+2", "A+3", "B+7"}
        self.gui.selected_bank, self.gui.selected_position = "C", "4"
        self.gui.save_batch_state()
        restored = self.new_gui()
        try:
            self.assertEqual(self.gui.tested_combinations, restored.tested_combinations)
            self.assertEqual(("C", "4"), (restored.selected_bank, restored.selected_position))
        finally:
            restored.close()

    def test_single_result_does_not_change_batch_progress(self):
        self.gui.tested_combinations = {"A+2"}
        before = set(self.gui.tested_combinations)
        result = self.gui.evaluate_results([10, 10, 10, 10], log_results=False, context="single")
        self.assertEqual("PASS", result)
        self.assertEqual(before, self.gui.tested_combinations)

    def test_all_four_saved_limits_drive_pass(self):
        self.gui.calibration_settings.update(front=11, left=12, back=13, right=14)
        self.assertEqual("PASS", self.gui.evaluate_results([11, 12, 13, 14], False, "single"))

    def test_each_individual_sensor_can_cause_fail(self):
        self.gui.calibration_settings.update(front=20, left=20, back=20, right=20)
        for failed_index in range(4):
            with self.subTest(channel=failed_index):
                readings = [10, 10, 10, 10]
                readings[failed_index] = 21
                self.assertEqual("FAIL", self.gui.evaluate_results(readings, False, "single"))

    def test_lid_open_rule_blocks_normal_result(self):
        result = self.gui.evaluate_results([10, 600, 10, 10], False, "single")
        self.assertEqual("LID OPEN", result)
        self.assertIn("lid", self.gui.single_result_detail.text().lower())

    def _prepare_direct_read(self, values, context="main"):
        self.gui.sensors = [FixedSensor(value) for value in values]
        self.gui._set_testing_controls(True)
        self.gui._active_test_context = context
        self.gui._active_combination = "A+2" if context == "main" else None
        self.gui._set_relay(True)

    def test_relay_shutdown_after_success(self):
        self.gui.calibration_settings.update(front=100, left=100, back=100, right=100)
        self._prepare_direct_read([10, 10, 10, 10])
        self.gui.take_readings(True, "main")
        self.assertEqual(ui.GPIO.LOW, ui.GPIO.pin_states[self.gui.LED_PIN])
        self.assertFalse(self.gui.test_in_progress)

    def test_relay_shutdown_and_no_progress_after_sensor_exception(self):
        self._prepare_direct_read([10, RuntimeError("read failed"), 10, 10])
        self.gui.take_readings(True, "main")
        self.assertEqual(ui.GPIO.LOW, ui.GPIO.pin_states[self.gui.LED_PIN])
        self.assertNotIn("A+2", self.gui.tested_combinations)
        self.assertEqual([], self.gui.history_entries)

    def test_close_event_forces_relay_low(self):
        self.gui._set_relay(True)
        self.gui.close()
        self.assertEqual(ui.GPIO.LOW, ui.GPIO.pin_states[self.gui.LED_PIN])

    def test_history_record_rolling_limit_and_weekly_accumulation(self):
        for index in range(95):
            self.gui.add_history_entry(f"PASS (A+2) | F-{index}, L-1, B-1, R-1 | 01-01-2026 | 00:00:00")
        self.assertEqual(90, len(self.gui.history_entries))
        with open(self.gui.weekly_history_file, "r", encoding="utf-8") as history_file:
            weekly = json.load(history_file)
        self.assertEqual(95, len(weekly))
        self.assertEqual({"timestamp", "result"}, set(weekly[0]))

    def test_lifetime_count_is_independent_of_recent_history(self):
        self.gui.total_tests_count = 44
        self.gui.save_stats()
        self.gui.history_entries = ["PASS"]
        self.gui.history_entries.clear()
        self.gui.save_history()
        restored = self.new_gui()
        try:
            self.assertEqual(44, restored.total_tests_count)
            self.assertEqual([], restored.history_entries)
        finally:
            restored.close()

    def test_legacy_history_string_json_loads(self):
        legacy = ["01-02-2025 - PASS legacy", "FAIL (B+4) | F-1, L-2, B-3, R-4 | date | time"]
        with open(self.gui.history_file, "w", encoding="utf-8") as history_file:
            json.dump(legacy, history_file)
        self.gui.load_history()
        self.assertEqual(legacy, self.gui.history_entries)

    def test_threshold_save_and_reload(self):
        for field, value in zip(self.gui.threshold_inputs, (21.5, 22.5, 23.5, 24.5)):
            field.setText(str(value))
        self.gui.save_calibration_settings()
        restored = self.new_gui()
        try:
            self.assertEqual(21.5, restored.calibration_settings["front"])
            self.assertEqual(24.5, restored.calibration_settings["right"])
        finally:
            restored.close()

    def test_master_reference_save_and_reload(self):
        self.gui.temp_master_readings = {"front": 1.0, "left": 2.0, "back": 3.0, "right": 4.0}
        self.gui.calibration_reason_input.setText("scheduled check")
        self.gui.calibration_performed_by_input.setText("QA")
        self.gui.send_calibration_update_email = mock.Mock()
        self.gui.lock_master_readings()
        restored = self.new_gui()
        try:
            self.assertTrue(restored.calibration_settings["master_locked"])
            self.assertEqual(3.0, restored.calibration_settings["master_readings"]["back"])
        finally:
            restored.close()

    def test_setup_settings_save_and_reload(self):
        self.gui.email_recipients_input.setPlainText("qa@example.test")
        self.gui.smtp_server_input.setText("smtp.example.test")
        self.gui.smtp_port_input.setText("2525")
        self.gui.email_username_input.setText("qa-user")
        self.gui.email_password_input.setText("fictional-demo-value")
        self.gui.save_email_settings_ui()
        restored = self.new_gui()
        try:
            self.assertEqual("smtp.example.test", restored.email_settings["smtp_server"])
            self.assertEqual("2525", restored.email_settings["smtp_port"])
            self.assertEqual("", restored.email_settings["password"])
        finally:
            restored.close()

    def test_protected_navigation_accepts_full_text_password(self):
        self.gui.setup_password = "Alpha-12_@"
        self.assertTrue(self.gui.is_valid_password("Alpha-12_@"))
        self.gui.get_password_input = mock.Mock(return_value=("Alpha-12_@", True))
        self.gui.tab_widget.setCurrentIndex(self.gui.calibration_tab_index)
        self.assertTrue(self.gui.calibration_tab_unlocked)
        self.assertEqual(self.gui.calibration_tab_index, self.gui.tab_widget.currentIndex())

    def test_keyboard_contains_required_email_and_editing_keys(self):
        keyboard = ui.KeyboardInputWindow("Input")
        try:
            labels = {button.text() for button in keyboard.findChildren(QPushButton)}
            self.assertTrue({"@", ".", "-", "_", "Back", "Space", "OK"}.issubset(labels))
        finally:
            keyboard.close()

    def test_screensaver_activation_and_dismissal(self):
        self.gui.show_screensaver()
        self.app.processEvents()
        self.assertTrue(self.gui.screensaver_overlay.isVisible())
        self.gui._on_screensaver_dismissed()
        self.assertFalse(self.gui.screensaver_overlay.isVisible())

    def test_mock_hardware_is_default_and_no_real_pi_is_selected(self):
        self.assertTrue(ui.FORCE_TEST_MODE)
        self.assertFalse(ui.ON_PI)
        self.assertTrue(self.gui.using_mock_hardware)

    def test_application_startup_and_primary_controls_fit_800_by_480(self):
        self.assertEqual((800, 480), (self.gui.width(), self.gui.height()))
        for widget in self.gui.findChildren((QLabel, QPushButton)):
            if not widget.isVisible() or widget.window() is not self.gui:
                continue
            top_left = widget.mapTo(self.gui, QPoint(0, 0))
            self.assertGreaterEqual(top_left.x(), 0, widget.objectName())
            self.assertGreaterEqual(top_left.y(), 0, widget.objectName())
            self.assertLessEqual(top_left.x() + widget.width(), 800, widget.text())
            self.assertLessEqual(top_left.y() + widget.height(), 480, widget.text())

    def test_start_button_and_cavity_selector_do_not_overlap(self):
        start_top_left = self.gui.test_button.mapTo(self.gui, QPoint(0, 0))
        selector_top_left = self.gui.cavity_selector.mapTo(self.gui, QPoint(0, 0))
        start_rect = self.gui.test_button.rect().translated(start_top_left)
        selector_rect = self.gui.cavity_selector.rect().translated(selector_top_left)
        self.assertFalse(start_rect.intersects(selector_rect))

    def test_operator_ui_contains_no_automatic_report_controls_or_text(self):
        visible_text = " ".join(
            widget.text().lower()
            for widget in self.gui.findChildren((QLabel, QPushButton))
            if widget.text()
        )
        self.assertNotIn("weekly report", visible_text)
        self.assertNotIn("weekly email", visible_text)
        self.assertNotIn("report schedule", visible_text)
        self.assertNotIn("enable report", visible_text)


if __name__ == "__main__":
    unittest.main()
