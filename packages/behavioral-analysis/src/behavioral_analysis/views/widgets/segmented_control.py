"""SegmentedControl: a group of adjacent buttons styled as a single segmented strip."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal


class SegmentedControl(QWidget):
    """Horizontal segmented button group with shared border radius."""

    selection_changed = Signal(str)  # emits the key of the selected segment

    def __init__(self, items=None, parent=None):
        super().__init__(parent)
        self._buttons = {}  # key -> QPushButton
        self._keys = []
        self._selected = None

        # Theme defaults (light)
        self._active_bg = "#3E6E8C"
        self._active_fg = "#FFFFFF"
        self._inactive_bg = "#FFFFFF"
        self._inactive_fg = "#8490A0"
        self._border = "#CDD4DC"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if items:
            for label, key in items:
                self.add_segment(label, key)
            self._rebuild_stylesheet()

    def add_segment(self, label, key):
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.clicked.connect(lambda _, k=key: self._on_clicked(k))
        self.layout().addWidget(btn)
        self._buttons[key] = btn
        self._keys.append(key)

        # Assign position-based object names for CSS targeting
        self._update_object_names()

        if self._selected is None:
            self._selected = key
            btn.setChecked(True)

    def set_selected(self, key):
        if key in self._buttons and key != self._selected:
            self._selected = key
            for k, btn in self._buttons.items():
                btn.blockSignals(True)
                btn.setChecked(k == key)
                btn.blockSignals(False)

    def set_theme(self, active_bg, active_fg, inactive_bg, inactive_fg, border):
        self._active_bg = active_bg
        self._active_fg = active_fg
        self._inactive_bg = inactive_bg
        self._inactive_fg = inactive_fg
        self._border = border
        self._rebuild_stylesheet()

    @property
    def selected(self):
        return self._selected

    def _on_clicked(self, key):
        if key != self._selected:
            self._selected = key
            for k, btn in self._buttons.items():
                btn.blockSignals(True)
                btn.setChecked(k == key)
                btn.blockSignals(False)
            self.selection_changed.emit(key)

    def _update_object_names(self):
        n = len(self._keys)
        for i, key in enumerate(self._keys):
            btn = self._buttons[key]
            if n == 1:
                btn.setObjectName("segSolo")
            elif i == 0:
                btn.setObjectName("segFirst")
            elif i == n - 1:
                btn.setObjectName("segLast")
            else:
                btn.setObjectName("segMid")

    def _rebuild_stylesheet(self):
        """Set one stylesheet on the container — avoids per-button setStyleSheet."""
        a_bg = self._active_bg
        a_fg = self._active_fg
        i_bg = self._inactive_bg
        i_fg = self._inactive_fg
        bd = self._border

        base = (
            f"font-size: 11px; padding: 5px 18px; "
            f"border: 1px solid {bd};"
        )

        self.setStyleSheet(f"""
            QPushButton {{
                {base}
                background-color: {i_bg}; color: {i_fg}; font-weight: normal;
                border-radius: 0; border-right: none;
            }}
            QPushButton:checked {{
                background-color: {a_bg}; color: {a_fg}; font-weight: bold;
            }}
            QPushButton#segSolo {{
                border-radius: 3px; border-right: 1px solid {bd};
            }}
            QPushButton#segFirst {{
                border-top-left-radius: 3px; border-bottom-left-radius: 3px;
            }}
            QPushButton#segLast {{
                border-top-right-radius: 3px; border-bottom-right-radius: 3px;
                border-right: 1px solid {bd};
            }}
        """)
