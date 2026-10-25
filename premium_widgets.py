"""Reusable native PyQt5 widgets for the premium touchscreen interface.

These widgets are deliberately presentation-only. Hardware, persistence, result
evaluation, access control, and reporting remain owned by :class:`BottleTesterGUI`.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


def repolish(widget: QWidget) -> None:
    """Refresh QSS after changing a dynamic property."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


class PremiumCard(QFrame):
    def __init__(self, parent=None, object_name="premiumCard"):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setAttribute(Qt.WA_StyledBackground, True)


class AppHeader(QFrame):
    def __init__(self, logo_path: str, parent=None):
        super().__init__(parent)
        self.setObjectName("appHeader")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(10)

        icon = QLabel("QA", self)
        icon.setObjectName("appIcon")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFixedSize(36, 36)
        layout.addWidget(icon)

        titles = QVBoxLayout()
        titles.setContentsMargins(0, 0, 0, 0)
        titles.setSpacing(2)
        title = QLabel("Light Transmission Tester", self)
        title.setObjectName("appTitle")
        subtitle = QLabel("SYNTHETIC DATA  ·  OFFLINE DEMO", self)
        subtitle.setObjectName("appSubtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        layout.addLayout(titles)
        layout.addStretch(1)

        self.system_state = QLabel("SYSTEM READY", self)
        self.system_state.setObjectName("systemState")
        self.system_state.setProperty("state", "ready")
        self.system_state.setAlignment(Qt.AlignCenter)
        self.system_state.setMinimumWidth(112)
        layout.addWidget(self.system_state)

        logo = QLabel(self)
        logo.setObjectName("headerLogo")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(70, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setFixedSize(76, 40)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

    def set_system_state(self, text: str, state: str = "ready") -> None:
        self.system_state.setText(text)
        self.system_state.setProperty("state", state)
        repolish(self.system_state)


class StatusPill(QLabel):
    def __init__(self, text="Ready", state="neutral", parent=None):
        super().__init__(text, parent)
        self.setObjectName("statusPill")
        self.setAlignment(Qt.AlignCenter)
        self.setProperty("state", state)
        self.setMinimumHeight(26)

    def set_state(self, text: str, state: str) -> None:
        self.setText(text)
        self.setProperty("state", state)
        repolish(self)


class SensorCard(PremiumCard):
    def __init__(self, name: str, parent=None):
        super().__init__(parent, "sensorCard")
        self.setProperty("state", "idle")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 7, 9, 7)
        layout.setSpacing(1)

        top = QHBoxLayout()
        top.setSpacing(4)
        name_label = QLabel(name, self)
        name_label.setObjectName("sensorName")
        top.addWidget(name_label)
        top.addStretch(1)
        self.dot = QLabel(self)
        self.dot.setObjectName("sensorDot")
        self.dot.setFixedSize(8, 8)
        top.addWidget(self.dot)
        layout.addLayout(top)

        value_row = QHBoxLayout()
        value_row.setSpacing(3)
        self.value_label = QLabel("—", self)
        self.value_label.setObjectName("sensorValue")
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        unit = QLabel("lx", self)
        unit.setObjectName("sensorUnit")
        unit.setAlignment(Qt.AlignBottom)
        value_row.addWidget(self.value_label)
        value_row.addWidget(unit)
        value_row.addStretch(1)
        layout.addLayout(value_row)

        self.meter = QProgressBar(self)
        self.meter.setObjectName("sensorMeter")
        self.meter.setTextVisible(False)
        self.meter.setRange(0, 100)
        self.meter.setValue(0)
        self.meter.setFixedHeight(5)
        layout.addWidget(self.meter)

    def set_reading(self, value=None, state="idle", text=None, limit=200.0) -> None:
        self.setProperty("state", state)
        self.dot.setProperty("state", state)
        self.meter.setProperty("state", state)
        if text is not None:
            self.value_label.setText(text)
        elif value is None:
            self.value_label.setText("—")
        else:
            self.value_label.setText(f"{value:.1f}")
        if value is None:
            self.meter.setValue(0)
        else:
            scale = max(float(limit) * 1.25, 1.0)
            self.meter.setValue(max(3, min(100, int(value / scale * 100))))
        repolish(self)
        repolish(self.dot)
        repolish(self.meter)


class CavitySelector(PremiumCard):
    selectionChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent, "cavitySelector")
        self.buttons = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 7, 9, 7)
        layout.setSpacing(5)

        heading = QHBoxLayout()
        label = QLabel("CAVITY SELECTOR", self)
        label.setObjectName("selectorHeading")
        self.current_label = QLabel("A2", self)
        self.current_label.setObjectName("currentCavity")
        heading.addWidget(label)
        heading.addStretch(1)
        heading.addWidget(self.current_label)
        layout.addLayout(heading)

        self.bank_group = QButtonGroup(self)
        self.bank_group.setExclusive(True)
        bank_row = QHBoxLayout()
        bank_row.setSpacing(4)
        bank_title = QLabel("BANK", self)
        bank_title.setObjectName("selectorLabel")
        bank_title.setFixedWidth(38)
        bank_row.addWidget(bank_title)
        for value in "ABC":
            button = self._choice(value)
            self.bank_group.addButton(button)
            bank_row.addWidget(button)
        layout.addLayout(bank_row)

        self.position_group = QButtonGroup(self)
        self.position_group.setExclusive(True)
        position_row = QHBoxLayout()
        position_row.setSpacing(4)
        position_title = QLabel("POS", self)
        position_title.setObjectName("selectorLabel")
        position_title.setFixedWidth(38)
        position_row.addWidget(position_title)
        for value in "234567":
            button = self._choice(value)
            self.position_group.addButton(button)
            position_row.addWidget(button)
        layout.addLayout(position_row)

        self.buttons["A"].setChecked(True)
        self.buttons["2"].setChecked(True)
        for button in self.buttons.values():
            button.toggled.connect(self._emit_selection)

    def _choice(self, value: str) -> QPushButton:
        button = QPushButton(value, self)
        button.setObjectName("choiceButton")
        button.setCheckable(True)
        button.setMinimumSize(34, 32)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.buttons[value] = button
        return button

    def selection(self):
        bank = next((v for v in "ABC" if self.buttons[v].isChecked()), "A")
        position = next((v for v in "234567" if self.buttons[v].isChecked()), "2")
        return bank, position

    def select(self, bank: str, position: str) -> None:
        if bank in "ABC" and position in "234567":
            self.buttons[bank].setChecked(True)
            self.buttons[position].setChecked(True)
            self._emit_selection()

    def _emit_selection(self, _checked=True) -> None:
        bank, position = self.selection()
        self.current_label.setText(f"{bank}{position}")
        self.selectionChanged.emit(bank, position)


class BottomNavigation(QFrame):
    pageRequested = pyqtSignal(int)

    LABELS = ("Batch", "Single", "History", "Calibration", "Setup")
    GLYPHS = ("B", "S", "H", "C", "S")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("bottomNavigation")
        self.setFixedHeight(58)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 5, 9, 6)
        layout.setSpacing(4)
        self.buttons = []
        for index, (label, glyph) in enumerate(zip(self.LABELS, self.GLYPHS)):
            suffix = " [LOCK]" if index in (3, 4) else ""
            button = QPushButton(f"{glyph}\n{label}{suffix}", self)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setProperty("protected", index in (3, 4))
            button.setMinimumHeight(46)
            button.clicked.connect(lambda _checked=False, i=index: self.pageRequested.emit(i))
            layout.addWidget(button, 1)
            self.buttons.append(button)
        self.set_active(0)

    def set_active(self, index: int) -> None:
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)

    def set_navigation_enabled(self, enabled: bool) -> None:
        for button in self.buttons:
            button.setEnabled(enabled)
