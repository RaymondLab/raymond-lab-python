"""CycleNavigator: horizontal row of clickable cycle segments."""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen


class CycleNavigator(QWidget):
    """Horizontal cycle segment strip. Click to select a cycle."""

    cycle_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cycle_data = []  # list of bools: True = good, False = saccade-detected
        self._selected = 0
        self.setMinimumHeight(18)
        self.setMinimumWidth(60)
        self.setCursor(Qt.PointingHandCursor)

        self._colors = {
            "qualGood": "#1A9E50",
            "qualBad": "#CF2C2C",
            "qualSelected": "#2D5FD4",
            "textPrimary": "#1A2230",
        }

    def set_cycle_data(self, data):
        """Set cycle data as list of bools (True=good, False=bad)."""
        self._cycle_data = data
        if self._selected >= len(data):
            self._selected = max(0, len(data) - 1)
        self.update()

    def set_selected(self, index):
        if 0 <= index < len(self._cycle_data):
            self._selected = index
            self.update()

    def set_theme(self, colors):
        self._colors = colors
        self.update()

    @property
    def selected_cycle(self):
        return self._selected

    def mousePressEvent(self, event):
        if not self._cycle_data:
            return
        n = len(self._cycle_data)
        gap = 1
        seg_w = max(1, (self.width() - gap * (n - 1)) / n)
        idx = int(event.position().x() / (seg_w + gap))
        idx = max(0, min(idx, n - 1))
        if idx != self._selected:
            self._selected = idx
            self.cycle_selected.emit(idx)
            self.update()

    def paintEvent(self, event):
        if not self._cycle_data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        n = len(self._cycle_data)
        w = self.width()
        h = self.height()
        gap = 1
        seg_w = max(1, (w - gap * (n - 1)) / n)
        c = self._colors
        outline_pen = QPen(QColor(c["textPrimary"]), 2)

        for i, is_good in enumerate(self._cycle_data):
            x = int(i * (seg_w + gap))
            sw = int(seg_w)
            is_sel = (i == self._selected)

            if is_sel:
                color = QColor(c["qualSelected"])
            elif is_good:
                color = QColor(c["qualGood"])
            else:
                color = QColor(c["qualBad"])

            if not is_sel:
                color.setAlphaF(0.55)

            painter.fillRect(QRect(x, 0, sw, h), color)
            if is_sel:
                painter.setPen(outline_pen)
                painter.drawRect(QRect(x, 0, sw - 1, h - 1))

        painter.end()
