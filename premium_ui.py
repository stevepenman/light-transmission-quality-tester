"""Native PyQt5 construction of the 800 × 480 premium interface."""

import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QApplication,
)

from premium_widgets import (
    AppHeader,
    BottomNavigation,
    CavitySelector,
    PremiumCard,
    SensorCard,
    StatusPill,
)


def _label(text, object_name="", parent=None, word_wrap=False):
    widget = QLabel(text, parent)
    if object_name:
        widget.setObjectName(object_name)
    widget.setWordWrap(word_wrap)
    return widget


def _button(text, role=None, parent=None):
    widget = QPushButton(text, parent)
    if role:
        widget.setProperty("role", role)
    return widget


def _page(parent):
    page = QWidget(parent)
    layout = QVBoxLayout(page)
    layout.setContentsMargins(12, 10, 12, 10)
    layout.setSpacing(8)
    return page, layout


def _sensor_grid(gui, parent, context):
    grid = QGridLayout()
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(7)
    grid.setVerticalSpacing(7)
    cards = []
    for index, name in enumerate(gui.sensor_names):
        card = SensorCard(name, parent)
        card.setMinimumHeight(91)
        grid.addWidget(card, index // 2, index % 2)
        cards.append(card)
    if context == "main":
        gui.sensor_cards = cards
        gui.sensor_labels = [card.value_label for card in cards]
    else:
        gui.single_sensor_cards = cards
        gui.single_sensor_labels = [card.value_label for card in cards]
    return grid


def _build_batch(gui, stack):
    page, page_layout = _page(stack)
    body = QHBoxLayout()
    body.setSpacing(10)

    batch = PremiumCard(page)
    batch.setMinimumWidth(405)
    left = QVBoxLayout(batch)
    left.setContentsMargins(13, 11, 13, 10)
    left.setSpacing(7)

    heading = QHBoxLayout()
    title_box = QVBoxLayout()
    title_box.setSpacing(1)
    title_box.addWidget(_label("SYNTHETIC BATCH TEST", "eyebrow", batch))
    title_box.addWidget(_label("18-cavity batch", "pageTitle", batch))
    heading.addLayout(title_box)
    heading.addStretch(1)
    gui.batch_status_pill = StatusPill("Ready", "ready", batch)
    heading.addWidget(gui.batch_status_pill, 0, Qt.AlignTop)
    left.addLayout(heading)

    control = QHBoxLayout()
    control.setSpacing(12)
    gui.test_button = QPushButton("START\nBATCH", batch)
    gui.test_button.setObjectName("startButton")
    gui.test_button.clicked.connect(lambda: gui.run_test_sequence(log_results=True, context="main"))
    control.addWidget(gui.test_button, 0, Qt.AlignVCenter)

    gui.cavity_selector = CavitySelector(batch)
    gui.cavity_selector.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    gui.part_checkboxes = gui.cavity_selector.buttons
    gui.cavity_selector.selectionChanged.connect(gui.on_cavity_selection_changed)
    control.addWidget(gui.cavity_selector, 1)
    left.addLayout(control)

    progress_top = QHBoxLayout()
    gui.current_cavity_label = _label("Current cavity  A2", "sectionTitle", batch)
    gui.batch_progress_label = _label("0 of 18 completed", "helperText", batch)
    gui.batch_progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    progress_top.addWidget(gui.current_cavity_label)
    progress_top.addStretch(1)
    progress_top.addWidget(gui.batch_progress_label)
    left.addLayout(progress_top)
    gui.batch_progress_bar = QProgressBar(batch)
    gui.batch_progress_bar.setObjectName("batchProgress")
    gui.batch_progress_bar.setTextVisible(False)
    gui.batch_progress_bar.setRange(0, 18)
    left.addWidget(gui.batch_progress_bar)
    gui.batch_missing_label = _label("18 cavities remaining · progress is retained after restart", "helperText", batch)
    left.addWidget(gui.batch_missing_label)
    left.addStretch(1)
    body.addWidget(batch, 11)

    right_stack = QVBoxLayout()
    right_stack.setSpacing(8)
    readings = PremiumCard(page)
    readings_layout = QVBoxLayout(readings)
    readings_layout.setContentsMargins(11, 9, 11, 9)
    readings_layout.setSpacing(6)
    sensor_head = QHBoxLayout()
    sensor_head.addWidget(_label("Simulated sensor readings", "sectionTitle", readings))
    sensor_head.addStretch(1)
    gui.status_label = StatusPill("Ready", "ready", readings)
    sensor_head.addWidget(gui.status_label)
    readings_layout.addLayout(sensor_head)
    readings_layout.addLayout(_sensor_grid(gui, readings, "main"))
    right_stack.addWidget(readings, 1)

    result = PremiumCard(page, "resultCard")
    result_layout = QHBoxLayout(result)
    result_layout.setContentsMargins(12, 8, 12, 8)
    result_text = QVBoxLayout()
    result_text.setSpacing(1)
    result_text.addWidget(_label("LAST BATCH RESULT", "eyebrow", result))
    gui.batch_result_label = _label("No test yet", "sectionTitle", result)
    result_text.addWidget(gui.batch_result_label)
    gui.batch_result_detail = _label("Close the lid and start the selected cavity.", "helperText", result, True)
    result_text.addWidget(gui.batch_result_detail)
    result_layout.addLayout(result_text, 1)
    gui.batch_result_icon = StatusPill("READY", "neutral", result)
    gui.batch_result_icon.setMinimumWidth(62)
    result_layout.addWidget(gui.batch_result_icon)
    right_stack.addWidget(result)
    body.addLayout(right_stack, 9)
    page_layout.addLayout(body)

    gui.simulate_lid_off_checkbox = QCheckBox(page)
    gui.simulate_lid_off_checkbox.hide()
    stack.addWidget(page)


def _build_single(gui, stack):
    page, page_layout = _page(stack)
    body = QHBoxLayout()
    body.setSpacing(10)

    action = PremiumCard(page, "guidanceCard")
    action.setMinimumWidth(330)
    layout = QVBoxLayout(action)
    layout.setContentsMargins(14, 12, 14, 11)
    layout.setSpacing(6)
    layout.addWidget(_label("STANDALONE CHECK", "eyebrow", action))
    top = QHBoxLayout()
    top.addWidget(_label("Single measurement", "pageTitle", action))
    top.addStretch(1)
    gui.single_status_pill = StatusPill("Ready", "ready", action)
    top.addWidget(gui.single_status_pill)
    layout.addLayout(top)

    middle = QHBoxLayout()
    gui.single_test_button = QPushButton("START\nSINGLE", action)
    gui.single_test_button.setObjectName("startButton")
    gui.single_test_button.clicked.connect(lambda: gui.run_test_sequence(log_results=False, context="single"))
    middle.addWidget(gui.single_test_button, 0, Qt.AlignCenter)
    steps = QVBoxLayout()
    steps.setSpacing(5)
    for number, text in (
        ("1", "Position the sample centrally."),
        ("2", "Close the lid completely."),
        ("3", "Press Start and keep the lid closed."),
    ):
        row = QHBoxLayout()
        badge = QLabel(number, action)
        badge.setObjectName("currentCavity")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(27, 27)
        row.addWidget(badge)
        row.addWidget(_label(text, "helperText", action, True), 1)
        steps.addLayout(row)
    middle.addLayout(steps, 1)
    layout.addLayout(middle, 1)
    note = _label("The single check uses the same four sensors and safety sequence without changing batch progress.", "helperText", action, True)
    layout.addWidget(note)
    body.addWidget(action, 9)

    readings = PremiumCard(page)
    readings_layout = QVBoxLayout(readings)
    readings_layout.setContentsMargins(11, 10, 11, 10)
    head = QHBoxLayout()
    head.addWidget(_label("Sensor readings", "sectionTitle", readings))
    head.addStretch(1)
    gui.status_label_single = StatusPill("Ready", "ready", readings)
    head.addWidget(gui.status_label_single)
    readings_layout.addLayout(head)
    readings_layout.addLayout(_sensor_grid(gui, readings, "single"))
    gui.single_result_detail = _label("Ready for a standalone sample.", "helperText", readings, True)
    readings_layout.addWidget(gui.single_result_detail)
    body.addWidget(readings, 11)
    page_layout.addLayout(body)

    gui.simulate_lid_off_checkbox_single = QCheckBox(page)
    gui.simulate_lid_off_checkbox_single.hide()
    stack.addWidget(page)


def _build_history(gui, stack):
    page, layout = _page(stack)
    top = QHBoxLayout()
    title_box = QVBoxLayout()
    title_box.setSpacing(1)
    title_box.addWidget(_label("LOCAL QUALITY RECORD", "eyebrow", page))
    title_box.addWidget(_label("Recent history", "pageTitle", page))
    top.addLayout(title_box)
    top.addStretch(1)
    gui.tests_counter_label = StatusPill("0 total tests", "info", page)
    top.addWidget(gui.tests_counter_label)
    gui.clear_history_button = _button("Clear history", "danger", page)
    gui.clear_history_button.clicked.connect(gui.clear_history)
    top.addWidget(gui.clear_history_button)
    layout.addLayout(top)

    panel = PremiumCard(page)
    panel_layout = QVBoxLayout(panel)
    panel_layout.setContentsMargins(0, 0, 0, 0)
    panel_layout.setSpacing(0)
    header = QWidget(panel)
    header.setObjectName("historyRow")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(11, 5, 11, 5)
    for text, stretch in (("RESULT / CAVITY", 2), ("SENSOR READINGS · DATE · TIME", 7)):
        label = _label(text, "helperText", header)
        header_layout.addWidget(label, stretch)
    panel_layout.addWidget(header)

    gui.history_scroll = QScrollArea(panel)
    gui.history_scroll.setWidgetResizable(True)
    gui.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    gui.history_container = QWidget(gui.history_scroll)
    gui.history_grid = QGridLayout(gui.history_container)
    gui.history_grid.setContentsMargins(0, 0, 0, 0)
    gui.history_grid.setSpacing(0)
    gui.history_grid.setColumnStretch(0, 1)
    gui.history_scroll.setWidget(gui.history_container)
    panel_layout.addWidget(gui.history_scroll, 1)
    gui.history_footer_label = _label("Showing up to 90 recent records · stored locally", "helperText", panel)
    gui.history_footer_label.setContentsMargins(10, 6, 10, 6)
    panel_layout.addWidget(gui.history_footer_label)
    layout.addWidget(panel, 1)
    gui.history_entries = []
    stack.addWidget(page)


def _threshold_row(gui, name, parent, index):
    row = QHBoxLayout()
    label = QLabel(f"{name} sensor", parent)
    label.setMinimumWidth(88)
    row.addWidget(label)
    field = QLineEdit(parent)
    field.setPlaceholderText("100.0")
    field.setProperty("inputMode", "numeric")
    row.addWidget(field, 1)
    row.addWidget(_label("lx", "helperText", parent))
    gui.threshold_inputs.append(field)
    return row


def _build_calibration(gui, stack):
    page, layout = _page(stack)
    scroll = QScrollArea(page)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    content = QWidget(scroll)
    content_layout = QHBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(10)

    threshold = PremiumCard(content)
    threshold_layout = QVBoxLayout(threshold)
    threshold_layout.setContentsMargins(12, 10, 12, 10)
    threshold_layout.setSpacing(6)
    threshold_layout.addWidget(_label("PROTECTED SETTINGS", "eyebrow", threshold))
    threshold_layout.addWidget(_label("Sensor limits", "pageTitle", threshold))
    threshold_layout.addWidget(_label("PASS requires every channel to be at or below its saved transmitted-light limit.", "helperText", threshold, True))
    gui.threshold_inputs = []
    for index, name in enumerate(gui.sensor_names):
        threshold_layout.addLayout(_threshold_row(gui, name, threshold, index))
    save = _button("Save thresholds", "primary", threshold)
    save.clicked.connect(gui.save_calibration_settings)
    threshold_layout.addWidget(save)
    threshold_layout.addStretch(1)
    content_layout.addWidget(threshold, 9)

    master = PremiumCard(content)
    master_layout = QVBoxLayout(master)
    master_layout.setContentsMargins(12, 10, 12, 10)
    master_layout.setSpacing(5)
    top = QHBoxLayout()
    titles = QVBoxLayout()
    titles.setSpacing(1)
    titles.addWidget(_label("APPROVED REFERENCE", "eyebrow", master))
    titles.addWidget(_label("Master sample", "pageTitle", master))
    top.addLayout(titles)
    top.addStretch(1)
    gui.master_state_pill = StatusPill("Not locked", "warning", master)
    top.addWidget(gui.master_state_pill, 0, Qt.AlignTop)
    master_layout.addLayout(top)

    master_grid = QGridLayout()
    master_grid.setSpacing(5)
    gui.master_reading_labels = []
    for index, name in enumerate(gui.sensor_names):
        cell = QFrame(master)
        cell.setObjectName("sensorCard")
        cell_layout = QVBoxLayout(cell)
        cell_layout.setContentsMargins(7, 4, 7, 4)
        cell_layout.setSpacing(0)
        cell_layout.addWidget(_label(name, "sensorName", cell))
        value = _label("— lx", "sectionTitle", cell)
        cell_layout.addWidget(value)
        gui.master_reading_labels.append(value)
        master_grid.addWidget(cell, index // 2, index % 2)
    master_layout.addLayout(master_grid)

    read = _button("Read master sample", None, master)
    read.clicked.connect(gui.test_master_sample)
    master_layout.addWidget(read)
    gui.calibration_reason_input = QLineEdit(master)
    gui.calibration_reason_input.setPlaceholderText("Reason for calibration update")
    gui.calibration_reason_input.setMaxLength(200)
    master_layout.addWidget(gui.calibration_reason_input)
    gui.calibration_performed_by_input = QLineEdit(master)
    gui.calibration_performed_by_input.setPlaceholderText("Name or employee ID")
    gui.calibration_performed_by_input.setMaxLength(100)
    master_layout.addWidget(gui.calibration_performed_by_input)
    lock_row = QHBoxLayout()
    gui.lock_master_btn = _button("Lock reference", "primary", master)
    gui.lock_master_btn.setEnabled(False)
    gui.lock_master_btn.clicked.connect(gui.lock_master_readings)
    lock_row.addWidget(gui.lock_master_btn)
    gui.update_master_btn = _button("Update", None, master)
    gui.update_master_btn.clicked.connect(gui.update_master_readings)
    lock_row.addWidget(gui.update_master_btn)
    master_layout.addLayout(lock_row)
    verify = _button("Verify locked sample", None, master)
    verify.clicked.connect(gui.verify_master_sample)
    master_layout.addWidget(verify)
    gui.master_status_label = _label("No master readings locked yet.", "helperText", master, True)
    gui.verify_status_label = _label("", "helperText", master, True)
    master_layout.addWidget(gui.master_status_label)
    master_layout.addWidget(gui.verify_status_label)
    content_layout.addWidget(master, 11)
    scroll.setWidget(content)
    layout.addWidget(scroll)
    stack.addWidget(page)
    gui.calibration_tab_index = stack.indexOf(page)


def _field_row(label_text, field, parent):
    row = QHBoxLayout()
    label = QLabel(label_text, parent)
    label.setMinimumWidth(88)
    row.addWidget(label)
    row.addWidget(field, 1)
    return row


def _build_setup(gui, stack):
    page, layout = _page(stack)
    content = QHBoxLayout()
    content.setSpacing(10)

    email = PremiumCard(page)
    email_layout = QVBoxLayout(email)
    email_layout.setContentsMargins(12, 10, 12, 10)
    email_layout.setSpacing(5)
    email_layout.addWidget(_label("PROTECTED CONFIGURATION", "eyebrow", email))
    email_layout.addWidget(_label("Offline settings example", "pageTitle", email))
    email_layout.addWidget(_label("Recipients", "helperText", email))
    gui.email_recipients_input = QTextEdit(email)
    gui.email_recipients_input.setPlaceholderText("One recipient address per line")
    gui.email_recipients_input.setFixedHeight(64)
    email_layout.addWidget(gui.email_recipients_input)
    gui.smtp_server_input = QLineEdit(email)
    gui.smtp_server_input.setPlaceholderText("smtp.example.com")
    email_layout.addLayout(_field_row("SMTP server", gui.smtp_server_input, email))
    gui.smtp_port_input = QLineEdit(email)
    gui.smtp_port_input.setPlaceholderText("587")
    gui.smtp_port_input.setProperty("inputMode", "numeric")
    email_layout.addLayout(_field_row("Port", gui.smtp_port_input, email))
    gui.email_username_input = QLineEdit(email)
    gui.email_username_input.setPlaceholderText("Username")
    email_layout.addLayout(_field_row("Username", gui.email_username_input, email))
    gui.email_password_input = QLineEdit(email)
    gui.email_password_input.setEchoMode(QLineEdit.Password)
    gui.email_password_input.setPlaceholderText("Disabled in offline demo")
    gui.email_password_input.setEnabled(False)
    email_layout.addLayout(_field_row("Password", gui.email_password_input, email))
    email_actions = QHBoxLayout()
    test = _button("Delivery disabled", None, email)
    test.setEnabled(False)
    email_actions.addWidget(test)
    save = _button("Save settings", "primary", email)
    save.clicked.connect(gui.save_email_settings_ui)
    email_actions.addWidget(save)
    email_layout.addLayout(email_actions)
    content.addWidget(email, 11)

    security = PremiumCard(page)
    security_layout = QVBoxLayout(security)
    security_layout.setContentsMargins(12, 10, 12, 10)
    security_layout.setSpacing(7)
    security_layout.addWidget(_label("ACCESS CONTROL", "eyebrow", security))
    security_layout.addWidget(_label("Supervisor password", "pageTitle", security))
    security_layout.addWidget(_label("Demo gate only. Default: demo. Changes last for this session.", "helperText", security, True))
    gui.new_password_input = QLineEdit(security)
    gui.new_password_input.setEchoMode(QLineEdit.Password)
    gui.new_password_input.setPlaceholderText("New password")
    security_layout.addWidget(gui.new_password_input)
    gui.confirm_password_input = QLineEdit(security)
    gui.confirm_password_input.setEchoMode(QLineEdit.Password)
    gui.confirm_password_input.setPlaceholderText("Confirm new password")
    security_layout.addWidget(gui.confirm_password_input)
    change = _button("Change password", "primary", security)
    change.clicked.connect(gui.change_setup_password)
    security_layout.addWidget(change)
    security_layout.addSpacing(4)
    security_layout.addWidget(_label("System status", "sectionTitle", security))
    mode_text = "Mock hardware active" if gui.using_mock_hardware else "Hardware interface active"
    gui.hardware_mode_pill = StatusPill(mode_text, "warning" if gui.using_mock_hardware else "ready", security)
    security_layout.addWidget(gui.hardware_mode_pill)
    security_layout.addWidget(_label("Offline demo. No hardware or email connections are available.", "helperText", security, True))
    security_layout.addStretch(1)
    content.addWidget(security, 9)
    layout.addLayout(content)
    stack.addWidget(page)
    gui.setup_tab_index = stack.indexOf(page)


def build_premium_ui(gui, screensaver_class):
    # Some headless/offscreen Qt builds expose no system font database. Loading a
    # known local system font keeps screenshot tests representative without
    # bundling or downloading a new asset. Normal Raspberry Pi desktops already
    # provide fonts and skip this fallback.
    if not QFontDatabase().families():
        for font_path in (
            r"C:\Windows\Fonts\segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ):
            if os.path.exists(font_path) and QFontDatabase.addApplicationFont(font_path) >= 0:
                break
    gui.setObjectName("applicationRoot")
    gui.setWindowTitle("Light Transmission Tester - Offline Demo")
    gui.setGeometry(100, 100, 800, 480)
    gui.setFixedSize(800, 480)
    gui.sensor_names = ["Front", "Left", "Back", "Right"]

    qss_path = os.path.join(os.path.dirname(__file__), "assets", "styles", "premium.qss")
    try:
        with open(qss_path, "r", encoding="utf-8") as style_file:
            gui.setStyleSheet(style_file.read())
    except OSError as exc:
        gui.logger.error("Could not load premium stylesheet: %s", exc)

    root = QVBoxLayout(gui)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)
    logo_path = os.path.join(os.path.dirname(__file__), "assets/offline-demo.svg")
    gui.app_header = AppHeader(logo_path, gui)
    root.addWidget(gui.app_header)

    gui.tab_widget = QStackedWidget(gui)
    _build_batch(gui, gui.tab_widget)
    _build_single(gui, gui.tab_widget)
    _build_history(gui, gui.tab_widget)
    _build_calibration(gui, gui.tab_widget)
    _build_setup(gui, gui.tab_widget)
    root.addWidget(gui.tab_widget, 1)

    gui.bottom_navigation = BottomNavigation(gui)
    gui.bottom_navigation.pageRequested.connect(gui.tab_widget.setCurrentIndex)
    gui.tab_widget.currentChanged.connect(gui.bottom_navigation.set_active)
    gui.tab_widget.currentChanged.connect(gui.on_tab_changed)
    root.addWidget(gui.bottom_navigation)

    gui.previous_tab_index = 0
    gui.idle_timeout_ms = 30000
    gui.idle_timer = QTimer(gui)
    gui.idle_timer.setInterval(gui.idle_timeout_ms)
    gui.idle_timer.timeout.connect(gui.return_to_main_tab)
    if QApplication.instance():
        QApplication.instance().installEventFilter(gui)
    gui.reset_idle_timer()

    gui.history_file = os.path.join(gui.data_dir, "history.json")
    gui.load_history()
    gui.populate_email_settings_ui()
    gui.populate_calibration_settings_ui()
    gui.update_tests_counter_label()
    gui.setup_virtual_keyboard()

    # Created last so it covers the complete header/page/navigation shell.
    gui.screensaver_overlay = screensaver_class(gui, logo_path)
    gui.screensaver_overlay.dismissed.connect(gui._on_screensaver_dismissed)
    gui.cavity_selector.select(gui.selected_bank, gui.selected_position)
    gui.update_batch_progress_ui()
