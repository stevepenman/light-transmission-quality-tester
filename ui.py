import sys
import time
import os
import json
import datetime
import html
import random
import math
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QTabWidget, QLineEdit, QTextEdit, QInputDialog, QMessageBox, QCheckBox, QDialog
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QEvent, QEventLoop, pyqtSignal

# Import logging and Excel export
from runtime_paths import data_directory
from logger_config import get_logger
from excel_export import ExcelReportGenerator

# The portfolio edition is deliberately offline on every platform.
from mock_hardware import MockTCA9548A, MockBH1750, MockGPIO

FORCE_TEST_MODE = True
ON_PI = False
GPIO = MockGPIO()


# Custom Keyboard Input Window (Standalone, not a dialog)
class KeyboardInputWindow(QWidget):
    def __init__(self, title, current_text="", is_password=False, target_widget=None, on_close=None, numeric_mode=False):
        super().__init__(None)  # NO parent - completely independent
        self.shift_active = False
        self.result_text = current_text
        self.is_password = is_password
        self.target_widget = target_widget
        self.saved = False
        self.on_close = on_close
        self.numeric_mode = numeric_mode
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.initUI(title, current_text)
    
    def initUI(self, title, current_text):
        self.setWindowTitle(title)
        # Simple window that stays on top
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.ApplicationModal)  # Block main window until closed
        
        # Touch-friendly keyboard sized for, and contained by, the 800x480 display.
        screen = QApplication.primaryScreen().geometry()
        window_width = min(760, screen.width() - 20)
        window_height = min(270, screen.height() - 20)
        
        # Position at lower centre of screen
        x = screen.x() + (screen.width() - window_width) // 2
        y = screen.y() + screen.height() - window_height - 8
        self.setGeometry(x, y, window_width, window_height)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Title label
        title_label = QLabel(title)
        title_label.setFont(QFont('IBM Plex Sans', 10, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Text input at top
        if isinstance(self.target_widget, QTextEdit):
            self.text_input = QTextEdit()
            self.text_input.setPlainText(current_text)
            self.text_input.setFixedHeight(42)
        else:
            self.text_input = QLineEdit(current_text)
        self.text_input.setFont(QFont('IBM Plex Sans', 11))
        self.text_input.setMinimumHeight(30)
        
        # Hide text for password fields
        if self.is_password and isinstance(self.text_input, QLineEdit):
            self.text_input.setEchoMode(QLineEdit.Password)
        
        layout.addWidget(self.text_input)
        
        # Keyboard layout
        keyboard_layout = QVBoxLayout()
        keyboard_layout.setSpacing(2)
        
        if self.numeric_mode:
            keys = [
                ['1', '2', '3', 'Back'],
                ['4', '5', '6', 'Clear'],
                ['7', '8', '9', '.'],
                ['0', '-', 'Cancel', 'OK'],
            ]
        else:
            keys = [
                ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'Back'],
                ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P', '@'],
                ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', '-', '_'],
                ['Shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '.', 'Clear'],
                ['Space', 'Enter', 'Cancel', 'OK']
            ]
        
        for row in keys:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)
            
            for key in row:
                btn = QPushButton(key)
                btn.setMinimumHeight(34)
                btn.setMaximumHeight(34)
                btn.setFont(QFont('IBM Plex Sans', 9, QFont.Bold))
                
                if key in ['Back', 'Shift', 'Clear', 'OK', 'Cancel', 'Space', 'Enter']:
                    if key == 'OK':
                        btn.setMinimumWidth(75)
                        btn.setStyleSheet("""
                            QPushButton {
                                background-color: #007BFF;
                                color: white;
                                border-radius: 3px;
                                border: none;
                                font-weight: bold;
                            }
                            QPushButton:pressed {
                                background-color: #0056b3;
                            }
                        """)
                    elif key == 'Cancel':
                        btn.setMinimumWidth(75)
                        btn.setStyleSheet("""
                            QPushButton {
                                background-color: #dc3545;
                                color: white;
                                border-radius: 3px;
                                border: none;
                                font-weight: bold;
                            }
                            QPushButton:pressed {
                                background-color: #c82333;
                            }
                        """)
                    else:
                        btn.setStyleSheet("""
                            QPushButton {
                                background-color: #28a745;
                                color: white;
                                border-radius: 3px;
                                border: none;
                            }
                            QPushButton:pressed {
                                background-color: #1e7e34;
                            }
                        """)
                        if key == 'Space':
                            btn.setMinimumWidth(112)
                else:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #6c757d;
                            color: white;
                            border-radius: 3px;
                            border: none;
                        }
                        QPushButton:pressed {
                            background-color: #545b62;
                        }
                    """)
                
                # Direct connection - no lambda, no partial
                if key == 'Back':
                    btn.clicked.connect(self.handle_back)
                elif key == 'Clear':
                    btn.clicked.connect(self.handle_clear)
                elif key == 'Space':
                    btn.clicked.connect(self.handle_space)
                elif key == 'Shift':
                    btn.clicked.connect(self.handle_shift)
                elif key == 'Enter':
                    btn.clicked.connect(self.handle_enter)
                elif key == 'OK':
                    btn.clicked.connect(self.handle_ok)
                elif key == 'Cancel':
                    btn.clicked.connect(self.handle_cancel)
                else:
                    # For letter/number keys, store the key text as a property
                    btn.setProperty('key_char', key)
                    btn.clicked.connect(self.handle_char)
                
                row_layout.addWidget(btn)
            
            keyboard_layout.addLayout(row_layout)
        
        layout.addLayout(keyboard_layout)
        self.setLayout(layout)
    
    def handle_back(self):
        current = self._input_text()
        self._set_input_text(current[:-1])
    
    def handle_clear(self):
        self.text_input.clear()
    
    def handle_space(self):
        self._set_input_text(self._input_text() + ' ')
    
    def handle_shift(self):
        self.shift_active = not self.shift_active

    def handle_enter(self):
        if isinstance(self.target_widget, QTextEdit):
            self._set_input_text(self._input_text() + '\n')
        else:
            self.handle_ok()
    
    def handle_ok(self):
        self.result_text = self._input_text()
        self.saved = True
        # Update target widget directly
        if self.target_widget:
            if isinstance(self.target_widget, QLineEdit):
                self.target_widget.setText(self.result_text)
            elif isinstance(self.target_widget, QTextEdit):
                self.target_widget.setPlainText(self.result_text)
        self.close()
    
    def handle_cancel(self):
        self.saved = False
        self.close()
    
    def handle_char(self):
        sender = self.sender()
        if sender:
            key = sender.property('key_char')
            if key:
                char = key if self.shift_active else key.lower()
                self._set_input_text(self._input_text() + char)
                if self.shift_active and key.isalpha():
                    self.shift_active = False

    def _input_text(self):
        if isinstance(self.text_input, QTextEdit):
            return self.text_input.toPlainText()
        return self.text_input.text()

    def _set_input_text(self, value):
        if isinstance(self.text_input, QTextEdit):
            self.text_input.setPlainText(value)
            cursor = self.text_input.textCursor()
            cursor.movePosition(cursor.End)
            self.text_input.setTextCursor(cursor)
        else:
            self.text_input.setText(value)
    
    def closeEvent(self, event):
        """Override close event"""
        if self.on_close:
            self.on_close()
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle physical keyboard - allow typing and special keys"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.handle_ok()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            print("Physical Escape key pressed - treating as Cancel button")
            self.handle_cancel()
            event.accept()
        else:
            # Forward all other keys to the text input so physical keyboard works
            self.text_input.event(event)
            event.accept()


class ScreenSaverOverlay(QWidget):
    dismissed = pyqtSignal()

    def __init__(self, parent=None, logo_path=""):
        super().__init__(parent)
        self.logo_path = logo_path
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        self.setWindowFlags(Qt.Widget | Qt.FramelessWindowHint)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("background-color: #071827;")

        self.logo_label = QLabel(self)
        self.logo_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._load_logo()

        self.move_timer = QTimer(self)
        self.move_timer.setInterval(20)
        self.move_timer.timeout.connect(self._tick)

        self.dx = 3
        self.dy = 3
        self.hide()

    def _load_logo(self):
        pixmap = QPixmap(self.logo_path) if self.logo_path and os.path.exists(self.logo_path) else QPixmap()
        if not pixmap.isNull():
            scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled)
            self.logo_label.setFixedSize(scaled.size())
            # Add rounded corners to the logo
            self.logo_label.setStyleSheet("""
                border-radius: 20px;
                background-color: white;
                padding: 10px;
            """)
        else:
            self.logo_label.setText("OFFLINE DEMO")
            self.logo_label.setFont(QFont('Inter', 36, QFont.Bold))
            self.logo_label.setStyleSheet("color: white;")
            self.logo_label.adjustSize()

    def start(self):
        self.sync_geometry()
        if self.width() <= 0 or self.height() <= 0:
            return

        # Randomize starting point and direction for variety
        max_x = max(0, self.width() - self.logo_label.width())
        max_y = max(0, self.height() - self.logo_label.height())
        start_x = random.randint(0, max_x) if max_x else 0
        start_y = random.randint(0, max_y) if max_y else 0
        self.logo_label.move(start_x, start_y)

        self.dx = random.choice([-4, -3, 3, 4])
        self.dy = random.choice([-4, -3, 3, 4])

        self.show()
        self.raise_()
        self.setFocus()
        if not self.move_timer.isActive():
            self.move_timer.start()

    def stop(self):
        if self.move_timer.isActive():
            self.move_timer.stop()
        self.hide()

    def sync_geometry(self):
        parent = self.parentWidget()
        if parent:
            self.setGeometry(parent.rect())

    def _tick(self):
        if not self.isVisible():
            return

        x = self.logo_label.x() + self.dx
        y = self.logo_label.y() + self.dy
        label_width = self.logo_label.width()
        label_height = self.logo_label.height()
        bounds_width = self.width()
        bounds_height = self.height()

        if x <= 0 or x + label_width >= bounds_width:
            self.dx *= -1
            x = max(0, min(x, bounds_width - label_width))
        if y <= 0 or y + label_height >= bounds_height:
            self.dy *= -1
            y = max(0, min(y, bounds_height - label_height))

        self.logo_label.move(x, y)

    def _handle_activity(self):
        self.dismissed.emit()

    def mousePressEvent(self, event):
        self._handle_activity()
        event.accept()

    def mouseMoveEvent(self, event):
        self._handle_activity()
        event.accept()

    def mouseReleaseEvent(self, event):
        self._handle_activity()
        event.accept()

    def keyPressEvent(self, event):
        self._handle_activity()
        event.accept()

    def touchEvent(self, event):
        self._handle_activity()
        event.accept()

    def event(self, event):
        if event.type() in (QEvent.TouchBegin, QEvent.TouchEnd, QEvent.TouchUpdate):
            self._handle_activity()
            return True
        return super().event(event)


class BottleTesterGUI(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize loggers
        self.logger = get_logger('app')
        self.hardware_logger = get_logger('hardware')
        self.email_logger = get_logger('email')
        
        self.logger.info("=" * 60)
        self.logger.info("Light Transmission Tester - Offline Demo Starting")
        self.logger.info("=" * 60)

        # --- Hardware Configuration ---
        self.LED_PIN = 17  # GPIO pin for the relay controlling the LED
        self.I2C_BUS = 1   # Default I2C bus for Raspberry Pi
        self.PASS_THRESHOLD = 200  # Lux value threshold for a PASS condition
        
        self.logger.info(f"Hardware Configuration - LED Pin: {self.LED_PIN}, I2C Bus: {self.I2C_BUS}")
        self.logger.info(f"Pass Threshold: {self.PASS_THRESHOLD} lx")

        # Track keyboard suppression so we don't immediately reopen after closing
        self.keyboard_suppress_focus = False
        self.keyboard_target = None

        # --- Sensor Setup ---
        self.using_mock_hardware = True  # default to mock

        self.tca = MockTCA9548A()
        self.sensors = [MockBH1750(channel) for channel in range(4)]
        self.bus = None

        # --- GPIO Setup ---
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.LED_PIN, GPIO.OUT)
            GPIO.output(self.LED_PIN, GPIO.LOW) # Ensure LED is off initially
            self.hardware_logger.info("GPIO initialized successfully")
        except Exception as e:
            self.logger.error(f"GPIO initialization error: {e}", exc_info=True)
            self.show_error("Hardware Error", f"Failed to initialize GPIO: {e}")

        # --- Email and Weekly Report Setup ---
        self.data_dir = str(data_directory())
        self.email_settings_file = os.path.join(self.data_dir, 'email_settings.json')
        self.weekly_history_file = os.path.join(self.data_dir, 'weekly_history.json')
        self.calibration_settings_file = os.path.join(self.data_dir, 'calibration_settings.json')
        # Stats (total tests counter)
        self.stats_file = os.path.join(self.data_dir, 'stats.json')
        
        # Initialize Excel report generator
        self.excel_generator = ExcelReportGenerator()
        self.logger.info("Excel report generator initialized")
        
        self.load_email_settings()
        self.load_calibration_settings()
        self.load_stats()
        
        # Public demo gate; this is not a security boundary.
        self.setup_password = os.environ.get('WTT_DEMO_PASSWORD', 'demo')
        self.setup_tab_unlocked = False
        self.calibration_tab_unlocked = False
        self.setup_tab_index = 3  # Setup is the 4th tab (index 3)
        self.calibration_tab_index = 2  # Calibration is the 3rd tab (index 2)
        self.previous_tab_index = 0  # Start on Main tab
        
        # 18-cavity testing cycle tracker
        self.tested_combinations = set()  # Track which ABC+number combinations have been tested
        self.current_cycle_start = datetime.datetime.now()
        self.batch_state_file = os.path.join(self.data_dir, 'batch_state.json')
        self.selected_bank = 'A'
        self.selected_position = '2'
        self.test_in_progress = False
        self.relay_active = False
        self._active_test_context = None
        self._active_combination = None
        self.load_batch_state()
        
        # Start weekly email scheduler
        self.start_weekly_email_scheduler()

        # --- UI Initialization ---
        self.initUI()

    
    def initUI(self):
        """Build the native premium touchscreen UI around the existing backend."""
        from premium_ui import build_premium_ui

        build_premium_ui(self, ScreenSaverOverlay)

    def setup_virtual_keyboard(self):
        """Install event filters on all text input widgets to show virtual keyboard"""
        # Find all QLineEdit and QTextEdit widgets
        for widget in self.findChildren(QLineEdit):
            widget.installEventFilter(self)
        for widget in self.findChildren(QTextEdit):
            widget.installEventFilter(self)
        
        # Store keyboard reference
        self.current_keyboard = None
        self.keyboard_process = None
    
    def show_virtual_keyboard(self, target_widget=None):
        """Show the built-in keyboard window"""
        # Clear any suppression when keyboard is explicitly requested
        self.keyboard_suppress_focus = False

        # If keyboard already open, don't open another
        if self.current_keyboard is not None and self.current_keyboard.isVisible():
            print("Keyboard already open, skipping")
            return
        
        # Clear old keyboard reference if it exists
        if self.current_keyboard is not None:
            self.current_keyboard.deleteLater()
            self.current_keyboard = None
        
        # If no target specified, try to find the focused widget
        if target_widget is None:
            target_widget = QApplication.focusWidget()
        
        # Only show keyboard for text input widgets
        if isinstance(target_widget, (QLineEdit, QTextEdit)):
            # Get current text
            current_text = target_widget.text() if isinstance(target_widget, QLineEdit) else target_widget.toPlainText()
            
            # Check if this is a password field
            is_password = False
            if isinstance(target_widget, QLineEdit):
                is_password = (target_widget.echoMode() == QLineEdit.Password)
            
            # Create and show keyboard window (NOT modal, standalone window)
            self.current_keyboard = KeyboardInputWindow(
                "Enter Text",
                current_text,
                is_password,
                target_widget,
                on_close=self._on_keyboard_closed,
                numeric_mode=bool(target_widget.property('inputMode') == 'numeric'),
            )
            self.current_keyboard.show()
            self.current_keyboard.raise_()
            
            print(f"✓ Keyboard window opened for {type(target_widget).__name__}")
    
    def _on_keyboard_closed(self):
        """Callback from the on-screen keyboard when it closes"""
        self.keyboard_suppress_focus = True
        self.current_keyboard = None

    def create_password_dialog(self, title, prompt):
        """Create the reusable touch password dialog and its masked input."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setFixedSize(430, 150)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        label = QLabel(prompt, dialog)
        label.setWordWrap(True)
        layout.addWidget(label)
        password_input = QLineEdit(dialog)
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setPlaceholderText('Supervisor password')
        layout.addWidget(password_input)
        actions = QHBoxLayout()
        cancel = QPushButton('Cancel', dialog)
        cancel.clicked.connect(dialog.reject)
        unlock = QPushButton('Unlock', dialog)
        unlock.setProperty('role', 'primary')
        unlock.clicked.connect(dialog.accept)
        actions.addWidget(cancel)
        actions.addWidget(unlock)
        layout.addLayout(actions)
        QTimer.singleShot(0, password_input.setFocus)
        return dialog, password_input

    def get_password_input(self, title, prompt):
        """Touch-first full-text password dialog backed by the shared keyboard."""
        dialog, password_input = self.create_password_dialog(title, prompt)
        QTimer.singleShot(80, lambda: self.show_virtual_keyboard(password_input))
        accepted = dialog.exec_() == QDialog.Accepted
        return password_input.text(), accepted
    
    def is_valid_password(self, password):
        """Check the local demonstration gate; no service override exists."""
        return password == self.setup_password
    
    # --- User Feedback Methods ---
    def show_error(self, title, message):
        """Display error message to user and log it"""
        self.logger.error(f"{title}: {message}")
        QMessageBox.critical(self, title, message)
    
    def show_warning(self, title, message):
        """Display warning message to user and log it"""
        self.logger.warning(f"{title}: {message}")
        QMessageBox.warning(self, title, message)
    
    def show_info(self, title, message):
        """Display info message to user and log it"""
        self.logger.info(f"{title}: {message}")
        QMessageBox.information(self, title, message)
    
    def show_success(self, title, message):
        """Display success message to user and log it"""
        self.logger.info(f"{title}: {message}")
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    
    def on_abc_checkbox_changed(self, part, state):
        """Ensure only one checkbox from A, B, C is selected at a time"""
        if state == Qt.Checked:
            # Uncheck all other A, B, C checkboxes
            for p in ['A', 'B', 'C']:
                if p != part and p in self.part_checkboxes:
                    self.part_checkboxes[p].blockSignals(True)
                    self.part_checkboxes[p].setChecked(False)
                    self.part_checkboxes[p].blockSignals(False)
    
    def on_number_checkbox_changed(self, part, state):
        """Ensure only one checkbox from 2, 3, 4, 5, 6, 7 is selected at a time"""
        if state == Qt.Checked:
            # Uncheck all other number checkboxes
            for p in ['2', '3', '4', '5', '6', '7']:
                if p != part and p in self.part_checkboxes:
                    self.part_checkboxes[p].blockSignals(True)
                    self.part_checkboxes[p].setChecked(False)
                    self.part_checkboxes[p].blockSignals(False)

    @staticmethod
    def cavity_order():
        """Return the single canonical order for the 18 valid cavities."""
        return [f"{bank}+{position}" for bank in ('A', 'B', 'C') for position in ('2', '3', '4', '5', '6', '7')]

    def load_batch_state(self):
        """Load additive batch progress state without changing legacy JSON schemas."""
        try:
            if not os.path.exists(self.batch_state_file):
                return
            with open(self.batch_state_file, 'r', encoding='utf-8') as state_file:
                data = json.load(state_file)
            valid = set(self.cavity_order())
            completed = data.get('tested_combinations', [])
            if not isinstance(completed, list):
                raise ValueError('tested_combinations must be a list')
            self.tested_combinations = {item for item in completed if item in valid}
            bank = str(data.get('selected_bank', 'A'))
            position = str(data.get('selected_position', '2'))
            self.selected_bank = bank if bank in ('A', 'B', 'C') else 'A'
            self.selected_position = position if position in ('2', '3', '4', '5', '6', '7') else '2'
            cycle_start = data.get('cycle_start')
            if cycle_start:
                self.current_cycle_start = datetime.datetime.fromisoformat(cycle_start)
            self.logger.info('Batch state restored: %d of 18 cavities', len(self.tested_combinations))
        except Exception as exc:
            self.logger.error('Could not load batch state; existing file was left untouched: %s', exc, exc_info=True)

    def save_batch_state(self):
        """Persist batch progress atomically."""
        data = {
            'version': 1,
            'tested_combinations': [item for item in self.cavity_order() if item in self.tested_combinations],
            'selected_bank': self.selected_bank,
            'selected_position': self.selected_position,
            'cycle_start': self.current_cycle_start.isoformat(),
        }
        temporary_path = f"{self.batch_state_file}.tmp"
        try:
            os.makedirs(os.path.dirname(self.batch_state_file) or '.', exist_ok=True)
            with open(temporary_path, 'w', encoding='utf-8') as state_file:
                json.dump(data, state_file, indent=2)
            os.replace(temporary_path, self.batch_state_file)
        except Exception as exc:
            self.logger.error('Could not save batch state: %s', exc, exc_info=True)
            try:
                if os.path.exists(temporary_path):
                    os.remove(temporary_path)
            except OSError:
                pass

    def on_cavity_selection_changed(self, bank, position):
        self.selected_bank = bank
        self.selected_position = position
        if hasattr(self, 'current_cavity_label'):
            self.current_cavity_label.setText(f'Current cavity  {bank}{position}')
        self.save_batch_state()

    def update_batch_progress_ui(self):
        completed = len(self.tested_combinations)
        remaining = max(0, 18 - completed)
        if hasattr(self, 'batch_progress_bar'):
            self.batch_progress_bar.setValue(completed)
        if hasattr(self, 'batch_progress_label'):
            self.batch_progress_label.setText(f'{completed} of 18 completed')
        if hasattr(self, 'batch_missing_label'):
            noun = 'cavity' if remaining == 1 else 'cavities'
            self.batch_missing_label.setText(f'{remaining} {noun} remaining · progress is retained after restart')
        if hasattr(self, 'current_cavity_label'):
            self.current_cavity_label.setText(f'Current cavity  {self.selected_bank}{self.selected_position}')

    def advance_to_next_cavity(self):
        """Select the first remaining cavity in the documented canonical order."""
        remaining = [item for item in self.cavity_order() if item not in self.tested_combinations]
        if not remaining:
            return
        bank, position = remaining[0].split('+', 1)
        self.selected_bank, self.selected_position = bank, position
        if hasattr(self, 'cavity_selector'):
            self.cavity_selector.select(bank, position)
        self.save_batch_state()
        self.update_batch_progress_ui()
    
    def check_missing_combinations(self):
        """Check which cavity combinations haven't been tested yet and display them"""
        all_combinations = [f"{abc}+{num}" for abc in ['A', 'B', 'C'] for num in ['2', '3', '4', '5', '6', '7']]
        missing = [combo for combo in all_combinations if combo not in self.tested_combinations]
        
        if missing:
            # Format missing combinations nicely
            missing_text = "\n".join([f"  • {combo}" for combo in missing])
            elapsed = datetime.datetime.now() - self.current_cycle_start
            elapsed_mins = int(elapsed.total_seconds() / 60)
            
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('Missing Cavity Tests')
            msg_box.setText(f"⚠️ {len(missing)} cavity combinations have not been tested yet!")
            msg_box.setInformativeText(
                f"Time elapsed: {elapsed_mins} minutes\n"
                f"Tested: {len(self.tested_combinations)}/18\n\n"
                f"Missing combinations:\n{missing_text}"
            )
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
            
            self.logger.warning(f"Missing cavity tests: {missing}")
            return len(missing)
        return 0
    
    def on_tab_changed(self, index):
        """Check password when Calibration or Setup tab is accessed"""
        if getattr(self, 'test_in_progress', False) and index != self.previous_tab_index:
            self.tab_widget.blockSignals(True)
            self.tab_widget.setCurrentIndex(self.previous_tab_index)
            self.tab_widget.blockSignals(False)
            if hasattr(self, 'bottom_navigation'):
                self.bottom_navigation.set_active(self.previous_tab_index)
            return
        # Only protect Calibration and Setup tabs
        if index == self.calibration_tab_index and not self.calibration_tab_unlocked:
            self.tab_widget.blockSignals(True)
            self.tab_widget.setCurrentIndex(self.previous_tab_index)
            self.tab_widget.blockSignals(False)
            password, ok = self.get_password_input('Password Required', 'Enter password to access Calibration:')
            if ok and self.is_valid_password(password):
                self.calibration_tab_unlocked = True
                self.tab_widget.blockSignals(True)
                self.tab_widget.setCurrentIndex(self.calibration_tab_index)
                self.tab_widget.blockSignals(False)
                self.previous_tab_index = index
            else:
                if hasattr(self, 'bottom_navigation'):
                    self.bottom_navigation.set_active(self.previous_tab_index)
                if ok:
                    print("Incorrect password!")
        elif index == self.setup_tab_index and not self.setup_tab_unlocked:
            self.tab_widget.blockSignals(True)
            self.tab_widget.setCurrentIndex(self.previous_tab_index)
            self.tab_widget.blockSignals(False)
            password, ok = self.get_password_input('Password Required', 'Enter password to access Setup:')
            if ok and self.is_valid_password(password):
                self.setup_tab_unlocked = True
                self.tab_widget.blockSignals(True)
                self.tab_widget.setCurrentIndex(self.setup_tab_index)
                self.tab_widget.blockSignals(False)
                self.previous_tab_index = index
            else:
                if hasattr(self, 'bottom_navigation'):
                    self.bottom_navigation.set_active(self.previous_tab_index)
                if ok:
                    print("Incorrect password!")
        else:
            self.previous_tab_index = index
            if index != self.setup_tab_index:
                self.setup_tab_unlocked = False
            if index != self.calibration_tab_index:
                self.calibration_tab_unlocked = False

    def reset_idle_timer(self):
        """Restart the inactivity timer whenever user interaction occurs."""
        try:
            if hasattr(self, 'idle_timer'):
                self.idle_timer.start(self.idle_timeout_ms)
        except Exception:
            pass

    def eventFilter(self, obj, event):
        """Monitor user input events to reset idle timer and show virtual keyboard."""
        if event.type() in (
            QEvent.MouseMove,
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.TouchBegin,
            QEvent.TouchEnd,
            QEvent.Wheel,
        ):
            self.hide_screensaver()
            self.reset_idle_timer()

        if event.type() in (QEvent.MouseButtonPress, QEvent.TouchBegin) and isinstance(obj, (QLineEdit, QTextEdit)):
            # User deliberately tapped an input, allow keyboard to reopen immediately
            parent_widget = obj.parent()
            is_keyboard_widget = False
            while parent_widget:
                if isinstance(parent_widget, KeyboardInputWindow):
                    is_keyboard_widget = True
                    break
                parent_widget = parent_widget.parent()
            if not is_keyboard_widget:
                self.keyboard_suppress_focus = False
                if not (self.current_keyboard and self.current_keyboard.isVisible()):
                    self.show_virtual_keyboard(obj)
                return super().eventFilter(obj, event)
        
        # Show virtual keyboard when text input is clicked
        # BUT NOT if it's the keyboard window's own text field!
        # Page construction can assign focus while a screen is being shown.
        # Open on an intentional tap unless a dialog explicitly opts in.
        if event.type() == QEvent.FocusIn and bool(obj.property('showKeyboardOnFocus')):
            if isinstance(obj, (QLineEdit, QTextEdit)):
                if self.keyboard_suppress_focus:
                    # Skip opening the keyboard once after it has just closed
                    return super().eventFilter(obj, event)

                # Check if this widget belongs to the keyboard window
                parent_widget = obj.parent()
                is_keyboard_widget = False
                while parent_widget:
                    if isinstance(parent_widget, KeyboardInputWindow):
                        is_keyboard_widget = True
                        break
                    parent_widget = parent_widget.parent()
                
                # Only show keyboard if NOT part of keyboard window
                if not is_keyboard_widget:
                    self.show_virtual_keyboard(obj)
        
        return super().eventFilter(obj, event)

    def return_to_main_tab(self):
        """Switch back to the Main tab after inactivity."""
        if getattr(self, 'test_in_progress', False):
            self.reset_idle_timer()
            return
        try:
            if getattr(self, 'tab_widget', None) and self.tab_widget.currentIndex() != 0:
                self.tab_widget.setCurrentIndex(0)
        except Exception:
            pass
        finally:
            self.reset_idle_timer()
            self.show_screensaver()

    def show_screensaver(self):
        try:
            if getattr(self, 'test_in_progress', False):
                return
            if getattr(self, 'screensaver_overlay', None) and not self.screensaver_overlay.isVisible():
                self.screensaver_overlay.start()
        except Exception:
            pass

    def hide_screensaver(self):
        try:
            if getattr(self, 'screensaver_overlay', None) and self.screensaver_overlay.isVisible():
                self.screensaver_overlay.stop()
        except Exception:
            pass

    def _on_screensaver_dismissed(self):
        self.hide_screensaver()
        self.reset_idle_timer()

    def resizeEvent(self, event):
        try:
            if getattr(self, 'screensaver_overlay', None):
                self.screensaver_overlay.sync_geometry()
        except Exception:
            pass
        super().resizeEvent(event)

    def _get_ui_context(self, context):
        """Return UI widgets for the requested test context."""
        if context == 'single':
            return {
                'test_button': getattr(self, 'single_test_button', None),
                'status_label': getattr(self, 'status_label_single', None),
                'sensor_labels': getattr(self, 'single_sensor_labels', []),
                'simulate_checkbox': getattr(self, 'simulate_lid_off_checkbox_single', None)
            }
        return {
            'test_button': getattr(self, 'test_button', None),
            'status_label': getattr(self, 'status_label', None),
            'sensor_labels': getattr(self, 'sensor_labels', []),
            'simulate_checkbox': getattr(self, 'simulate_lid_off_checkbox', None)
        }




    # --- Premium test orchestration and relay safety ---
    def _write_json_atomic(self, path, data, indent=None):
        """Write JSON through a same-directory temporary file to avoid truncation."""
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        temporary_path = f'{path}.tmp'
        try:
            with open(temporary_path, 'w', encoding='utf-8') as output_file:
                json.dump(data, output_file, indent=indent)
                output_file.flush()
                os.fsync(output_file.fileno())
            os.replace(temporary_path, path)
        except Exception:
            try:
                if os.path.exists(temporary_path):
                    os.remove(temporary_path)
            except OSError:
                pass
            raise

    def _sensor_limits(self):
        """Return the four saved maximum readings in physical channel order."""
        limits = []
        for name in self.sensor_names:
            value = self.calibration_settings.get(name.lower(), self.PASS_THRESHOLD)
            try:
                limits.append(float(value))
            except (TypeError, ValueError):
                limits.append(float(self.PASS_THRESHOLD))
        return limits

    def _set_relay(self, enabled):
        """Set relay state and retain enough state for defensive shutdown."""
        GPIO.output(self.LED_PIN, GPIO.HIGH if enabled else GPIO.LOW)
        self.relay_active = bool(enabled)
        self.hardware_logger.debug('LED relay turned %s', 'ON' if enabled else 'OFF')

    def _ensure_relay_off(self):
        try:
            self._set_relay(False)
        except Exception as exc:
            self.relay_active = False
            self.logger.error('Failed to force LED relay off: %s', exc, exc_info=True)

    def _set_test_status(self, context, text, state):
        widgets = self._get_ui_context(context)
        status = widgets.get('status_label')
        if hasattr(status, 'set_state'):
            status.set_state(text, state)
        elif status:
            status.setText(text)
        summary = self.single_status_pill if context == 'single' else self.batch_status_pill
        if hasattr(summary, 'set_state'):
            summary.set_state(text, state)
        if hasattr(self, 'app_header'):
            if state == 'measuring':
                self.app_header.set_system_state('MEASURING', 'measuring')
            elif state == 'error':
                self.app_header.set_system_state('ATTENTION', 'error')
            else:
                self.app_header.set_system_state('SYSTEM READY', 'ready')

    def _set_sensor_card(self, context, index, value=None, state='idle', text=None):
        cards = self.single_sensor_cards if context == 'single' else self.sensor_cards
        if index < len(cards):
            cards[index].set_reading(value=value, state=state, text=text, limit=self._sensor_limits()[index])

    def _set_testing_controls(self, running):
        self.test_in_progress = running
        for name in ('test_button', 'single_test_button'):
            button = getattr(self, name, None)
            if button:
                button.setEnabled(not running)
        if hasattr(self, 'bottom_navigation'):
            self.bottom_navigation.set_navigation_enabled(not running)
        if running:
            self.idle_timer.stop()
        else:
            self.reset_idle_timer()

    def _finish_test(self):
        self._ensure_relay_off()
        self._active_test_context = None
        self._active_combination = None
        self._set_testing_controls(False)

    def _precheck_lid(self, context):
        """Read ambient light with the relay off before allowing a test to start."""
        widgets = self._get_ui_context(context)
        simulate = widgets.get('simulate_checkbox')
        if simulate and simulate.isChecked():
            return False
        self._ensure_relay_off()
        for index, sensor in enumerate(self.sensors):
            try:
                self.tca.select_channel(index)
                time.sleep(0.1)
                ambient = sensor.measure_high_res()
                self.hardware_logger.debug(
                    'Ambient precheck %s: %.2f lx', self.sensor_names[index], ambient
                )
                if ambient > 500.0:
                    return False
            except Exception as exc:
                self.logger.error(
                    'Ambient precheck failed for %s: %s', self.sensor_names[index], exc, exc_info=True
                )
                raise
        return True

    def _show_close_lid(self, context):
        self._set_test_status(context, 'CLOSE LID', 'warning')
        if context == 'main':
            self.batch_result_label.setText('CLOSE LID')
            self.batch_result_detail.setText('Testing is blocked while ambient light is detected.')
            self.batch_result_icon.set_state('BLOCKED', 'warning')
        else:
            self.single_result_detail.setText('Close the lid fully, then press Start again.')
        self.show_warning(
            'CLOSE LID',
            'CLOSE LID\n\nAmbient light is too high. Close the lid completely before starting the test.'
        )

    def run_test_sequence(self, log_results=True, context='main'):
        """Run the authoritative lid → relay → stabilise → read sequence."""
        if self.test_in_progress:
            self.logger.warning('Ignored second start request while a test is active')
            return

        combination = None
        if context == 'main':
            bank = next((part for part in ('A', 'B', 'C') if self.part_checkboxes[part].isChecked()), None)
            position = next((part for part in ('2', '3', '4', '5', '6', '7') if self.part_checkboxes[part].isChecked()), None)
            if not bank or not position:
                self.show_warning('Selection Required', 'Select one bank and one position before starting.')
                return
            combination = f'{bank}+{position}'

            if len(self.tested_combinations) == 18:
                reply = QMessageBox.question(
                    self, 'Start New Batch',
                    'All 18 cavities are complete. Start a new 18-cavity batch?',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                self.tested_combinations.clear()
                self.current_cycle_start = datetime.datetime.now()
                self.save_batch_state()
                self.update_batch_progress_ui()

            if combination in self.tested_combinations:
                reply = QMessageBox.question(
                    self, 'Duplicate Test Detected',
                    f"Cavity '{combination}' is already complete in this batch.\n\nTest it again?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return

        try:
            if not self._precheck_lid(context):
                self._show_close_lid(context)
                return
        except Exception:
            self._set_test_status(context, 'PRECHECK ERROR', 'error')
            self.show_error('Sensor Error', 'The ambient-light safety check failed. The test was not started.')
            return

        self._active_test_context = context
        self._active_combination = combination
        self._set_testing_controls(True)
        self._set_test_status(context, 'STABILISING', 'measuring')
        for index in range(4):
            self._set_sensor_card(context, index, state='measuring', text='—')

        try:
            self._set_relay(True)
        except Exception as exc:
            self.logger.error('Failed to energise LED relay: %s', exc, exc_info=True)
            self._set_test_status(context, 'HARDWARE ERROR', 'error')
            self._finish_test()
            self.show_error('Hardware Error', 'The LED relay could not be enabled. The test was cancelled.')
            return

        self.logger.info('%s test sequence initiated', 'Single' if context == 'single' else 'Batch')
        QTimer.singleShot(3000, lambda: self.take_readings(log_results=log_results, context=context))

    def take_readings(self, log_results=True, context='main'):
        """Read each channel once and always de-energise the relay."""
        if not self.test_in_progress or self._active_test_context != context:
            self._ensure_relay_off()
            return
        readings = []
        sensor_error = False
        self._set_test_status(context, 'MEASURING', 'measuring')
        limits = self._sensor_limits()
        try:
            for index, sensor in enumerate(self.sensors):
                try:
                    self.tca.select_channel(index)
                    time.sleep(0.1)
                    value = float(sensor.measure_high_res())
                    readings.append(value)
                    state = 'fail' if value > limits[index] else ('warning' if value > limits[index] * 0.8 else 'pass')
                    self._set_sensor_card(context, index, value=value, state=state)
                    self.hardware_logger.debug(
                        'Sensor %d (%s): %.2f lx', index, self.sensor_names[index], value
                    )
                except Exception as exc:
                    sensor_error = True
                    readings.append(float('inf'))
                    self._set_sensor_card(context, index, state='error', text='ERR')
                    self.logger.error(
                        'Error reading sensor %d (%s): %s', index, self.sensor_names[index], exc, exc_info=True
                    )
        finally:
            self._ensure_relay_off()

        try:
            if sensor_error:
                self._set_test_status(context, 'SENSOR ERROR', 'error')
                if context == 'main':
                    self.batch_result_label.setText('Test not recorded')
                    self.batch_result_detail.setText('A sensor read failed; batch progress was not advanced.')
                    self.batch_result_icon.set_state('ERROR', 'error')
                else:
                    self.single_result_detail.setText('A sensor read failed. No result was recorded.')
                self.show_error('Sensor Error', 'One or more sensor channels could not be read. The relay is off.')
                return

            result = self.evaluate_results(readings, log_results=log_results, context=context)
            if context == 'main' and result in ('PASS', 'FAIL') and self._active_combination:
                self.tested_combinations.add(self._active_combination)
                self.save_batch_state()
                self.update_batch_progress_ui()
                if len(self.tested_combinations) < 18:
                    self.advance_to_next_cavity()
                else:
                    self.show_success('Batch Complete', 'All 18 cavity combinations are complete.')
        finally:
            self._finish_test()

    def evaluate_results(self, readings, log_results=True, context='main'):
        """Evaluate once using saved channel limits, update UI, and optionally record."""
        if len(readings) != 4 or any(not math.isfinite(value) or value < 0 for value in readings):
            self._set_test_status(context, 'SENSOR ERROR', 'error')
            return 'ERROR'

        cavity = self._active_combination if context == 'main' else ''
        letters = ('F', 'L', 'B', 'R')
        summary = ', '.join(f'{letters[i]}-{int(round(readings[i]))}' for i in range(4))
        now = datetime.datetime.now()
        date_text = now.strftime('%d-%m-%Y')
        time_text = now.strftime('%H:%M:%S')

        if any(value > 500.0 for value in readings):
            result = 'LID OPEN'
            state = 'warning'
            display = 'CLOSE LID'
        else:
            limits = self._sensor_limits()
            passed = all(readings[index] <= limits[index] for index in range(4))
            result = 'PASS' if passed else 'FAIL'
            state = 'pass' if passed else 'fail'
            display = result

        self._set_test_status(context, display, state)
        if context == 'main':
            self.batch_result_label.setText(display)
            if result == 'PASS':
                detail = 'All four sensor channels satisfy their saved limits.'
            elif result == 'FAIL':
                detail = 'One or more sensor channels exceeds its saved limit.'
            else:
                detail = 'Ambient light is too high. Close the lid and repeat the test.'
            self.batch_result_detail.setText(detail)
            self.batch_result_icon.set_state(result.replace('LID OPEN', 'BLOCKED'), state)
        else:
            self.single_result_detail.setText(
                'All four sensor channels satisfy their saved limits.' if result == 'PASS'
                else ('One or more sensor channels exceeds its saved limit.' if result == 'FAIL'
                      else 'Close the lid completely and repeat the test.')
            )

        if log_results:
            entry = result
            if cavity:
                entry += f' ({cavity})'
            entry += f' | {summary} | {date_text} | {time_text}'
            if result == 'PASS':
                self.logger.info('Test result: PASS - %s', summary)
            else:
                self.logger.warning('Test result: %s - %s', result, summary)
            self.add_history_entry(entry)
            self.total_tests_count = getattr(self, 'total_tests_count', 0) + 1
            self.save_stats()
            self.update_tests_counter_label()
        return result

    # --- History persistence methods ---
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError('history root must be a list')
                    self.history_entries = data[-90:]  # Keep up to 90 most recent entries (single column)
                    self.refresh_history_display()
        except Exception as exc:
            self.logger.error('Could not load history; the existing file was left untouched: %s', exc, exc_info=True)
    
    def refresh_history_display(self):
        # Clear existing grid
        for i in reversed(range(self.history_grid.count())):
            self.history_grid.itemAt(i).widget().setParent(None)
        
        # Reverse the entries so most recent appears at top
        reversed_entries = list(reversed(self.history_entries))
        
        # Add entries to a single column, up to 90 rows (scrolling vertically)
        for idx, text in enumerate(reversed_entries[:90]):
            row = idx
            col = 0

            # Parse result and remainder to align readings across rows
            result = None
            rest_text = ''
            if text.startswith('PASS') or text.startswith('FAIL') or text.startswith('LID OPEN'):
                parts = text.split(' | ', 1)
                result = parts[0]
                rest_text = parts[1] if len(parts) > 1 else ''
            else:
                # Fallback for legacy entries
                if 'LID OPEN' in text or 'Close Lid' in text:
                    result = 'LID OPEN'
                    rest_text = text
                elif 'FAIL' in text:
                    result = 'FAIL'
                    rest_text = text
                elif 'PASS' in text:
                    result = 'PASS'
                    rest_text = text
                else:
                    rest_text = text

            # Row container styled with a subtle outline instead of solid fill
            row_widget = QWidget(self)
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(8, 3, 8, 3)  # balanced padding
            row_layout.setSpacing(10)  # consistent spacing between result and data

            # Choose background color based on result
            outline_color = None
            if result and 'PASS' in result:
                outline_color = '#28A745'
            elif result and 'FAIL' in result:
                outline_color = '#DC3545'
            elif result and 'LID OPEN' in result:
                outline_color = '#CC7000'

            base_style = "background-color: #ffffff; color: #1a1a1a; border-radius: 6px; border: none;"
            row_widget.setStyleSheet(base_style)

            # Fixed-width result label (aligns readings start across rows) - 50% larger
            result_label = QLabel(result or '', self)
            result_label.setFont(QFont('Inter', 11, QFont.DemiBold))
            result_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            result_label.setFixedWidth(120) # Increased width to accommodate cavity info
            result_label.setFixedHeight(24)
            label_style = "padding: 0px; margin: 0px; color: #1a1a1a;"
            result_label.setStyleSheet(label_style)
            if outline_color:
                safe_text = html.escape(result or '')
                result_label.setTextFormat(Qt.RichText)
                result_label.setText(
                    f"<span style='color:{outline_color}; text-decoration: underline;'>{safe_text}</span>"
                )
            else:
                result_label.setText(result or '')

            # Rest of the text (readings, date, time) - single line, no wrap - 50% larger
            rest_html = html.escape(rest_text)
            try:
                parts = [p.strip() for p in rest_text.split('|')]
                if parts and ',' in parts[0]:
                    summary_tokens = [token.strip() for token in parts[0].split(',')]
                    formatted_tokens = []
                    for token in summary_tokens:
                        compact = token.replace(' ', '')
                        if not compact:
                            formatted_tokens.append(html.escape(token))
                            continue
                        letter = compact[0]
                        value_part = compact[1:]
                        is_fail = False
                        try:
                            value = float(value_part)
                            if value > self.PASS_THRESHOLD:
                                is_fail = True
                        except ValueError:
                            if value_part.lower() == 'err':
                                is_fail = True
                        display_token = html.escape(token)
                        if is_fail:
                            display_token = f"<span style='color:#DC3545; text-decoration: underline;'>{display_token}</span>"
                        formatted_tokens.append(display_token)
                    summary_html = ', '.join(formatted_tokens)
                    other_html = ' | '.join(html.escape(p) for p in parts[1:]) if len(parts) > 1 else ''
                    rest_html = summary_html
                    if other_html:
                        rest_html = f"{summary_html} | {other_html}"
            except Exception:
                rest_html = html.escape(rest_text)

            rest_label = QLabel(self)
            rest_label.setFont(QFont('Inter', 11))
            rest_label.setWordWrap(False)  # Keep everything on one line
            rest_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            rest_label.setTextFormat(Qt.RichText)
            rest_label.setText(rest_html)
            # Cap the data width so the whole row fits on 800x480 screens without horizontal scroll
            rest_label.setMaximumWidth(620)
            rest_label.setFixedHeight(24)  # 16 * 1.5 = 24
            rest_label.setStyleSheet("padding: 0px; margin: 0px; color: #1a1a1a;")

            row_layout.addWidget(result_label)
            row_layout.addWidget(rest_label, 1)
            row_widget.setLayout(row_layout)
            # Fixed width for all rows so colored blocks are identical width
            try:
                # Ensure row fits within 800px: 8+8 margins + 120 result + 10 spacing + 620 data = 766px total
                row_widget.setFixedWidth(760)  # Fixed width instead of max - all rows same size
                row_widget.setFixedHeight(30)  # slightly taller for breathing room
            except Exception:
                pass

            self.history_grid.addWidget(row_widget, row, col, alignment=Qt.AlignHCenter)

    def save_history(self):
        try:
            # Keep only last 90 entries (single column)
            items = self.history_entries[-90:]
            self._write_json_atomic(self.history_file, items)
            self.logger.debug(f"Saved {len(items)} history entries to {self.history_file}")
        except Exception as e:
            self.logger.error(f"Error saving history: {e}", exc_info=True)

    # --- Stats (Total Tests Counter) ---
    def load_stats(self):
        """Load persisted stats such as total tests count."""
        self.total_tests_count = 0
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.total_tests_count = int(data.get('total_tests_count', 0))
        except Exception as e:
            print(f"Error loading stats: {e}")

    def save_stats(self):
        """Persist stats to disk."""
        try:
            data = {
                'total_tests_count': int(getattr(self, 'total_tests_count', 0))
            }
            self._write_json_atomic(self.stats_file, data, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def update_tests_counter_label(self):
        """Refresh the on-screen counter label if present."""
        try:
            if hasattr(self, 'tests_counter_label') and self.tests_counter_label is not None:
                self.tests_counter_label.setText(f"{int(getattr(self, 'total_tests_count', 0))} total tests")
        except Exception:
            pass

    def add_history_entry(self, text):
        # Append to the entries list and ensure it stays to 90 entries (30 rows x 3 cols)
        self.history_entries.append(text)
        while len(self.history_entries) > 90:
            self.history_entries.pop(0)
        
        # Refresh the display
        self.refresh_history_display()
        
        # Save to disk
        self.save_history()
        
        # Also add to weekly history for email reports
        self.add_to_weekly_history(text)

    def clear_history(self):
        """Clear all history entries from memory and disk, with confirmation."""
        try:
            # Require the current demonstration gate password
            pwd, ok = self.get_password_input('Password Required',
                                              'Enter password to clear History:')
            if not ok:
                return
            if not self.is_valid_password(pwd):
                QMessageBox.warning(self, 'Access Denied', 'Incorrect password. History was not cleared.')
                return

            # Confirm destructive action
            reply = QMessageBox.question(
                self,
                'Clear History',
                'This will delete all saved history results (up to 90).\nDo you want to continue?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.history_entries = []
                # Persist empty list
                self.save_history()
                # Refresh UI
                self.refresh_history_display()
        except Exception as e:
            print(f"Error clearing history: {e}")
    
    # --- Weekly Email Report Methods ---
    def add_to_weekly_history(self, text):
        """Add test result to weekly history file for email reports"""
        try:
            weekly_data = []
            if os.path.exists(self.weekly_history_file):
                with open(self.weekly_history_file, 'r') as f:
                    weekly_data = json.load(f)
            
            weekly_data.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'result': text
            })
            
            self._write_json_atomic(self.weekly_history_file, weekly_data, indent=2)
        except Exception as e:
            print(f"Error adding to weekly history: {e}")
    
    def load_email_settings(self):
        """Load email settings from file"""
        self.email_settings = {
            'recipients': [],
            'smtp_server': 'smtp.example.test',
            'smtp_port': '587',
            'username': '',
            'password': ''
        }
        try:
            if os.path.exists(self.email_settings_file):
                with open(self.email_settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.email_settings.update(loaded_settings)
                self.logger.info(f"Email settings loaded: {len(self.email_settings.get('recipients', []))} recipients configured")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in email settings file: {e}")
        except Exception as e:
            self.logger.error(f"Error loading email settings: {e}", exc_info=True)
    
    def load_calibration_settings(self):
        """Load calibration settings from file"""
        self.calibration_settings = {
            'front': 100.0,
            'left': 100.0,
            'back': 100.0,
            'right': 100.0,
            'master_readings': {
                'front': None,
                'left': None,
                'back': None,
                'right': None
            },
            'master_locked': False,
            'master_locked_date': None
        }
        try:
            if os.path.exists(self.calibration_settings_file):
                with open(self.calibration_settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.calibration_settings.update(loaded_settings)
                self.logger.info("Calibration settings loaded successfully")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in calibration settings file: {e}")
        except Exception as e:
            self.logger.error(f"Error loading calibration settings: {e}", exc_info=True)
        
        # Store temporary master test readings (not saved until locked)
        self.temp_master_readings = None
    
    def save_email_settings_ui(self):
        """Save email settings from UI inputs"""
        try:
            recipients = self.email_recipients_input.toPlainText().strip().split('\n')
            recipients = [r.strip() for r in recipients if r.strip()]
            
            self.email_settings = {
                'recipients': recipients,
                'smtp_server': self.smtp_server_input.text().strip(),
                'smtp_port': self.smtp_port_input.text().strip(),
                'username': self.email_username_input.text().strip(),
                'password': '',  # Credentials are never persisted in the offline edition.
                'offline_demo': True
            }
            
            # Validate port is numeric
            try:
                port = int(self.email_settings['smtp_port'])
                if port < 1 or port > 65535:
                    self.show_warning("Invalid Port", "Port must be between 1 and 65535")
                    return
            except ValueError:
                self.show_warning("Invalid Port", "Port must be a number")
                return
            
            self._write_json_atomic(self.email_settings_file, self.email_settings, indent=2)
            self.logger.info(f"Email settings saved: {len(recipients)} recipients")
            self.show_success("Settings Saved", "Email settings saved successfully!")
        except Exception as e:
            self.logger.error(f"Error saving email settings: {e}", exc_info=True)
            self.show_error("Save Failed", f"Failed to save email settings:\n{str(e)}")
    
    def change_setup_password(self):
        """Change the Setup tab password"""
        try:
            new_pass = self.new_password_input.text().strip()
            confirm_pass = self.confirm_password_input.text().strip()
            
            if not new_pass:
                self.show_warning("Invalid Password", "Password cannot be empty!")
                return
            
            if new_pass != confirm_pass:
                self.show_warning("Password Mismatch", "Passwords do not match!")
                return
            
            self.setup_password = new_pass
            # Session-only: do not write access credentials to disk.
            
            self.logger.info("Setup password changed successfully")
            self.show_success("Success", "Demo password changed for this session only.")
            self.new_password_input.clear()
            self.confirm_password_input.clear()
        except Exception as e:
            self.logger.error(f"Error changing password: {e}", exc_info=True)
            self.show_error("Error", f"Failed to change password:\n{str(e)}")
    
    def save_calibration_settings(self):
        """Validate and save all four sensor limits as one atomic update."""
        sensor_names = ("Front", "Left", "Back", "Right")
        parsed_values = []
        try:
            for index, name in enumerate(sensor_names):
                raw_value = self.threshold_inputs[index].text().strip()
                value = float(raw_value)
                if not math.isfinite(value) or value <= 0:
                    raise ValueError
                parsed_values.append(value)
        except (TypeError, ValueError):
            self.show_warning('Invalid Threshold', 'Enter a positive numeric limit for every sensor.')
            return

        previous = {name.lower(): self.calibration_settings.get(name.lower()) for name in sensor_names}
        changed_entries = []
        try:
            for name, value in zip(sensor_names, parsed_values):
                key = name.lower()
                old_value = previous[key]
                self.calibration_settings[key] = value
                if old_value is None or abs(value - float(old_value)) > 1e-6:
                    changed_entries.append((name, old_value, value))
            self._write_json_atomic(self.calibration_settings_file, self.calibration_settings, indent=2)
            self.logger.info('Calibration thresholds saved')
            self.populate_calibration_settings_ui()
            self.show_success('Thresholds Saved', 'All four sensor limits were saved successfully.')
            if changed_entries:
                self.send_threshold_change_email(changed_entries)
        except Exception as exc:
            self.logger.error('Error saving calibration thresholds: %s', exc, exc_info=True)
            self.show_error('Save Failed', 'Calibration limits could not be saved.')
    
    def send_threshold_change_email(self, changes):
        """Offline edition: delivery is intentionally unavailable."""
        self.logger.info("Email delivery disabled in offline portfolio edition")
        return False

    
    def lock_master_readings(self):
        """Lock the current master readings as the reference datum"""
        if not self.temp_master_readings:
            print("No master readings to lock!")
            return
        
        # Get the reason for calibration update
        reason = self.calibration_reason_input.text().strip()
        if not reason:
            self.show_warning("Reason Required", "Please provide a reason for this calibration update before locking.")
            return
        
        # Get who is performing the calibration
        performed_by = self.calibration_performed_by_input.text().strip()
        if not performed_by:
            self.show_warning("Performed By Required", "Please enter who is performing this calibration.")
            return
        
        # Save to calibration settings
        self.calibration_settings['master_readings'] = self.temp_master_readings
        self.calibration_settings['master_locked'] = True
        locked_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.calibration_settings['master_locked_date'] = locked_date
        self.calibration_settings['master_locked_reason'] = reason
        self.calibration_settings['master_locked_by'] = performed_by
        
        try:
            self._write_json_atomic(self.calibration_settings_file, self.calibration_settings, indent=2)
            
            # Update display
            sensor_names = ["front", "left", "back", "right"]
            for i, name in enumerate(sensor_names):
                reading = self.temp_master_readings[name]
                self.master_reading_labels[i].setText(f'{reading:.2f} lx')
                self.master_reading_labels[i].setStyleSheet("background-color: #28A745; color: white; padding: 4px; border-radius: 4px; font-weight: bold;")
            
            self.master_status_label.setText(f'✓ Master readings locked on {locked_date}')
            self.master_status_label.setStyleSheet("color: #28A745; font-weight: bold;")
            
            # Disable lock button and clear input fields
            self.lock_master_btn.setEnabled(False)
            self.calibration_reason_input.clear()
            self.calibration_performed_by_input.clear()
            
            # Send calibration update email
            self.send_calibration_update_email(locked_date, reason, performed_by, self.temp_master_readings)
            
            print(f"Master readings locked successfully on {locked_date}")
            self.logger.info("Master readings locked by %s: %s", performed_by, reason)
        except Exception as e:
            error_msg = f"Error locking master readings: {e}"
            print(error_msg)
            self.logger.error(error_msg, exc_info=True)
            self.show_error("Calibration Error", error_msg)
    
    def update_master_readings(self):
        """Allow updating of locked master readings"""
        # Get the reason for calibration update
        reason = self.calibration_reason_input.text().strip()
        if not reason:
            self.show_warning("Reason Required", "Please provide a reason for unlocking the master readings.")
            return
        
        # Get who is performing the update
        performed_by = self.calibration_performed_by_input.text().strip()
        if not performed_by:
            self.show_warning("Performed By Required", "Please enter who is performing this update.")
            return
        
        reply = QMessageBox.question(self, 'Update Master Readings',
                                     'This will unlock the current master readings.\nYou will need to test and lock new readings.\n\nContinue?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Save old readings for email
            old_readings = self.calibration_settings.get('master_readings', {}).copy()
            old_date = self.calibration_settings.get('master_locked_date', 'Unknown')
            old_locked_by = self.calibration_settings.get('master_locked_by', 'Unknown')
            
            # Unlock master readings
            self.calibration_settings['master_locked'] = False
            self.calibration_settings['master_locked_date'] = None
            self.calibration_settings['master_unlocked_reason'] = reason
            self.calibration_settings['master_unlocked_by'] = performed_by
            self.calibration_settings['master_unlocked_date'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.temp_master_readings = None
            
            # Save settings
            try:
                self._write_json_atomic(self.calibration_settings_file, self.calibration_settings, indent=2)
            except Exception as e:
                print(f"Error saving calibration settings: {e}")
            
            # Clear display
            sensor_names = ["front", "left", "back", "right"]
            for i in range(4):
                self.master_reading_labels[i].setText('-- lx')
                self.master_reading_labels[i].setStyleSheet("background-color: #E0E0E0; padding: 4px; border-radius: 4px;")
            
            self.master_status_label.setText('Master readings unlocked. Test a new master sample.')
            self.master_status_label.setStyleSheet("color: #DC3545; font-weight: bold;")
            
            self.lock_master_btn.setEnabled(False)
            
            # Send unlock notification email
            self.send_calibration_unlock_email(old_date, reason, performed_by, old_readings, old_locked_by)
            
            print("Master readings unlocked for update")
            self.logger.info("Master readings unlocked by %s: %s", performed_by, reason)
    
    
    def _responsive_wait(self, seconds):
        """Keep paint/touch processing alive during legacy hardware stabilisation waits."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
            time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))

    def test_master_sample(self):
        """Capture three safe, repeatable master runs using the supported driver API."""
        if self.test_in_progress:
            return
        sensor_keys = ('front', 'left', 'back', 'right')
        runs = []
        self._set_testing_controls(True)
        self.master_status_label.setText('Reading master sample · keep the lid closed…')
        try:
            for run_index in range(3):
                current = []
                try:
                    self._set_relay(True)
                    self._responsive_wait(2.0)
                    for index, sensor in enumerate(self.sensors):
                        self.tca.select_channel(index)
                        self._responsive_wait(0.1)
                        current.append(float(sensor.measure_high_res()))
                except Exception as exc:
                    self.logger.error('Master sample run %d failed: %s', run_index + 1, exc, exc_info=True)
                    self.temp_master_readings = None
                    self.lock_master_btn.setEnabled(False)
                    self.master_status_label.setText('Master sample read failed. The relay is off.')
                    self.show_error('Calibration Error', 'A master-sample sensor read failed.')
                    return
                finally:
                    self._ensure_relay_off()

                if any(value > 500.0 for value in current):
                    self.temp_master_readings = None
                    self.lock_master_btn.setEnabled(False)
                    self.master_status_label.setText('CLOSE LID · master sample was not recorded.')
                    self.show_warning('CLOSE LID', 'Close the lid completely before reading the master sample.')
                    return
                runs.append(current)
                if run_index < 2:
                    self._responsive_wait(1.5)

            averages = []
            spreads = []
            consistent = []
            for index in range(4):
                values = [run[index] for run in runs]
                average = sum(values) / 3.0
                spread = max(values) - min(values)
                tolerance = max(2.0, 0.02 * max(average, 1.0))
                averages.append(average)
                spreads.append(spread)
                consistent.append(spread <= tolerance)

            for index, average in enumerate(averages):
                self.master_reading_labels[index].setText(f'{average:.2f} lx')
            if all(consistent):
                self.temp_master_readings = dict(zip(sensor_keys, averages))
                self.lock_master_btn.setEnabled(True)
                spread_text = ', '.join(
                    f'{self.sensor_names[index]} ±{spreads[index]:.2f} lx' for index in range(4)
                )
                self.master_status_label.setText(
                    f'Three runs are consistent ({spread_text}). Enter the audit fields, then lock the reference.'
                )
                if hasattr(self, 'master_state_pill'):
                    self.master_state_pill.set_state('New reading', 'warning')
            else:
                self.temp_master_readings = None
                self.lock_master_btn.setEnabled(False)
                self.master_status_label.setText('Readings were not repeatable. Reposition the sample and test again.')
                if hasattr(self, 'master_state_pill'):
                    self.master_state_pill.set_state('Retest required', 'fail')
        finally:
            self._finish_test()

    def verify_master_sample(self):
        """Safely compare one run with the locked reference."""
        if not self.calibration_settings.get('master_locked', False):
            self.verify_status_label.setText('No locked master reference is available.')
            return
        if self.test_in_progress:
            return
        reference = self.calibration_settings.get('master_readings') or {}
        if not all(reference.get(key) is not None for key in ('front', 'left', 'back', 'right')):
            self.verify_status_label.setText('The saved master reference is incomplete.')
            return

        self._set_testing_controls(True)
        readings = []
        try:
            try:
                self._set_relay(True)
                self._responsive_wait(2.0)
                for index, sensor in enumerate(self.sensors):
                    self.tca.select_channel(index)
                    self._responsive_wait(0.1)
                    readings.append(float(sensor.measure_high_res()))
            except Exception as exc:
                self.logger.error('Master verification failed: %s', exc, exc_info=True)
                self.verify_status_label.setText('Verification could not read every sensor. The relay is off.')
                self.show_error('Verification Error', 'A sensor could not be read during verification.')
                return
            finally:
                self._ensure_relay_off()

            details = []
            all_ok = True
            for index, key in enumerate(('front', 'left', 'back', 'right')):
                master_value = float(reference[key])
                difference = abs(readings[index] - master_value)
                tolerance = max(2.0, 0.02 * master_value)
                channel_ok = difference <= tolerance
                all_ok = all_ok and channel_ok
                details.append(f'{self.sensor_names[index]} Δ{difference:.2f} lx')
            prefix = 'PASS' if all_ok else 'FAIL'
            self.verify_status_label.setText(f'{prefix} · ' + ' · '.join(details))
        finally:
            self._finish_test()

    def populate_email_settings_ui(self):
        """Populate UI with saved email settings"""
        try:
            self.email_recipients_input.setPlainText('\n'.join(self.email_settings.get('recipients', [])))
            self.smtp_server_input.setText(self.email_settings.get('smtp_server', 'smtp.example.test'))
            self.smtp_port_input.setText(self.email_settings.get('smtp_port', '587'))
            self.email_username_input.setText(self.email_settings.get('username', ''))
            self.email_password_input.setText(self.email_settings.get('password', ''))
        except Exception as e:
            print(f"Error populating email settings: {e}")
    
    def populate_calibration_settings_ui(self):
        """Populate UI with saved calibration settings"""
        try:
            sensor_names = ["front", "left", "back", "right"]
            for i, name in enumerate(sensor_names):
                threshold = self.calibration_settings.get(name, 100.0)
                self.threshold_inputs[i].setText(str(threshold))
            
            # Populate master readings if they exist
            master_readings = self.calibration_settings.get('master_readings', {})
            for i, name in enumerate(sensor_names):
                reading = master_readings.get(name)
                if reading is not None:
                    self.master_reading_labels[i].setText(f'{reading:.2f} lx')
                    self.master_reading_labels[i].setStyleSheet("background-color: #28A745; color: white; padding: 4px; border-radius: 4px; font-weight: bold;")
                else:
                    self.master_reading_labels[i].setText('-- lx')
                    self.master_reading_labels[i].setStyleSheet("background-color: #E0E0E0; padding: 4px; border-radius: 4px;")
            
            # Update status based on locked state
            if self.calibration_settings.get('master_locked', False):
                locked_date = self.calibration_settings.get('master_locked_date', 'Unknown')
                if hasattr(self, 'master_state_pill'):
                    self.master_state_pill.set_state('Reference locked', 'pass')
                self.master_status_label.setText(f'✓ Master readings locked on {locked_date}')
                self.master_status_label.setStyleSheet("color: #28A745; font-weight: bold;")
            else:
                if hasattr(self, 'master_state_pill'):
                    self.master_state_pill.set_state('Not locked', 'warning')
                self.master_status_label.setText('No master readings locked yet.')
                self.master_status_label.setStyleSheet("color: #666;")
                
        except Exception as e:
            print(f"Error populating calibration settings: {e}")
    
    def send_weekly_email(self):
        """Offline edition: delivery is intentionally unavailable."""
        self.logger.info("Email delivery disabled in offline portfolio edition")
        return False
    
    def send_calibration_update_email(self, locked_date, reason, performed_by, master_readings):
        """Offline edition: delivery is intentionally unavailable."""
        self.logger.info("Email delivery disabled in offline portfolio edition")
        return False
    
    def send_calibration_unlock_email(self, old_date, reason, performed_by, old_readings, old_locked_by):
        """Offline edition: delivery is intentionally unavailable."""
        self.logger.info("Email delivery disabled in offline portfolio edition")
        return False
    
    def send_test_email(self):
        """Offline edition: delivery is intentionally unavailable."""
        self.logger.info("Email delivery disabled in offline portfolio edition")
        return False
    
    def start_weekly_email_scheduler(self):
        """Offline edition: no scheduler or background sender is started."""
        return None

    def closeEvent(self, event):
        """Clean up GPIO pins when the application closes."""
        try:
            if QApplication.instance():
                QApplication.instance().removeEventFilter(self)
        except Exception:
            pass
        # De-energise before cleanup even if a timer/read sequence is interrupted.
        try:
            self.test_in_progress = False
            self._ensure_relay_off()
        except Exception:
            try:
                GPIO.output(self.LED_PIN, GPIO.LOW)
            except Exception:
                pass
        # Clean up GPIO but avoid printing to console in normal operation
        try:
            GPIO.cleanup()
        except Exception:
            pass
        event.accept()


# --- Real Hardware Classes (for Raspberry Pi) ---
class TCA9548A:
    """I2C Multiplexer Driver"""
    def __init__(self, bus, address=0x70):
        self.bus = bus
        self.address = address

    def select_channel(self, channel):
        if not 0 <= channel <= 7:
            raise ValueError("Channel must be an integer between 0 and 7.")
        self.bus.write_byte(self.address, 1 << channel)

class BH1750:
    """BH1750 Ambient Light Sensor Driver"""
    def __init__(self, bus, address=0x23):
        self.bus = bus
        self.address = address
        # Power on and set to High-Resolution Mode
        self.bus.write_byte(self.address, 0x01) # Power On
        self.bus.write_byte(self.address, 0x10) # High-Res Mode

    def measure_high_res(self):
        """Reads the light intensity in lux."""
        data = self.bus.read_i2c_block_data(self.address, 0x10, 2)
        result = (data[0] << 8) | data[1]
        # Conversion factor from datasheet for high-res mode
        lux = result / 1.2
        return lux

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BottleTesterGUI()
    window.show()
    sys.exit(app.exec_())
