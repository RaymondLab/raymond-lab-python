"""BlockNavigator: dual-row block strip with prev/next buttons and label area."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen


class _BlockStrip(QWidget):
    """Custom-painted dual-row block strip (top: type colors, bottom: quality colors)."""

    clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocks = []  # list of dicts: {type, quality_fraction}
        self._selected = 0
        self.setMinimumHeight(26)
        self.setMinimumWidth(100)
        self.setCursor(Qt.PointingHandCursor)

        # Theme colors (defaults to light theme; call set_theme to update)
        self._colors = {
            "blockPrepost": "#0F8A5F",
            "blockTrain": "#CF2C4A",
            "qualGood": "#1A9E50",
            "qualWarn": "#D4930D",
            "qualBad": "#CF2C2C",
            "textPrimary": "#1A2230",
        }

    def set_blocks(self, blocks):
        """Set block data. Each block: dict with 'type' ('pre'|'post'|'train') and 'quality_fraction' (0-1)."""
        self._blocks = blocks
        self.update()

    def set_selected(self, index):
        if 0 <= index < len(self._blocks):
            self._selected = index
            self.update()

    def set_theme(self, colors):
        self._colors = colors
        self.update()

    @property
    def selected(self):
        return self._selected

    def mousePressEvent(self, event):
        if not self._blocks:
            return
        n = len(self._blocks)
        w = self.width()
        gap = 1
        seg_w = max(1, (w - gap * (n - 1)) / n)
        idx = int(event.position().x() / (seg_w + gap))
        idx = max(0, min(idx, n - 1))
        if idx != self._selected:
            self._selected = idx
            self.clicked.emit(idx)
            self.update()

    def paintEvent(self, event):
        if not self._blocks:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        n = len(self._blocks)
        w = self.width()
        gap = 1
        top_h = 13
        bot_h = 9
        seg_w = max(1, (w - gap * (n - 1)) / n)

        c = self._colors
        outline_pen = QPen(QColor(c["textPrimary"]), 2)

        for i, block in enumerate(self._blocks):
            x = int(i * (seg_w + gap))
            sw = int(seg_w)
            is_sel = (i == self._selected)

            # Top row: block type color
            if block.get("type") in ("pre", "post"):
                color = QColor(c["blockPrepost"])
            else:
                color = QColor(c["blockTrain"])

            if not is_sel:
                color.setAlphaF(0.45)
            painter.fillRect(QRect(x, 0, sw, top_h), color)
            if is_sel:
                painter.setPen(outline_pen)
                painter.drawRect(QRect(x, 0, sw - 1, top_h - 1))

            # Bottom row: quality color
            qf = block.get("quality_fraction", 0.5)
            if qf >= 0.4:
                qcolor = QColor(c["qualGood"])
            elif qf >= 0.2:
                qcolor = QColor(c["qualWarn"])
            else:
                qcolor = QColor(c["qualBad"])

            if not is_sel:
                qcolor.setAlphaF(0.45)
            painter.fillRect(QRect(x, top_h + 1, sw, bot_h), qcolor)
            if is_sel:
                painter.setPen(outline_pen)
                painter.drawRect(QRect(x, top_h + 1, sw - 1, bot_h - 1))

        painter.end()


class BlockNavigator(QWidget):
    """Block navigator with prev/next buttons, block strip, and label area."""

    block_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocks = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Prev button
        self._prev_btn = QPushButton("\u25C2")
        self._prev_btn.setFixedWidth(28)
        self._prev_btn.clicked.connect(self._go_prev)
        layout.addWidget(self._prev_btn)

        # Block strip
        self._strip = _BlockStrip()
        self._strip.clicked.connect(self._on_strip_clicked)
        layout.addWidget(self._strip, 1)

        # Next button
        self._next_btn = QPushButton("\u25B8")
        self._next_btn.setFixedWidth(28)
        self._next_btn.clicked.connect(self._go_next)
        layout.addWidget(self._next_btn)

        # Label area
        label_area = QWidget()
        label_layout = QVBoxLayout(label_area)
        label_layout.setContentsMargins(4, 0, 0, 0)
        label_layout.setSpacing(0)

        self._block_label = QLabel("Block 0 / 0")
        self._block_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        label_layout.addWidget(self._block_label)

        self._block_type_label = QLabel("")
        self._block_type_label.setStyleSheet("font-size: 10px;")
        label_layout.addWidget(self._block_type_label)

        label_area.setFixedWidth(120)
        layout.addWidget(label_area)

    def set_blocks(self, blocks):
        """Set block data. Each: dict with 'type', 'quality_fraction', 'label'."""
        self._blocks = blocks
        self._strip.set_blocks(blocks)
        self._update_label()

    def set_selected(self, index):
        if 0 <= index < len(self._blocks):
            self._strip.set_selected(index)
            self._update_label()

    def set_theme(self, colors):
        self._strip.set_theme(colors)

    @property
    def selected_block(self):
        return self._strip.selected

    def _go_prev(self):
        if self._strip.selected > 0:
            idx = self._strip.selected - 1
            self._strip.set_selected(idx)
            self._update_label()
            self.block_selected.emit(idx)

    def _go_next(self):
        if self._strip.selected < len(self._blocks) - 1:
            idx = self._strip.selected + 1
            self._strip.set_selected(idx)
            self._update_label()
            self.block_selected.emit(idx)

    def _on_strip_clicked(self, index):
        self._update_label()
        self.block_selected.emit(index)

    def _update_label(self):
        n = len(self._blocks)
        idx = self._strip.selected
        if n == 0:
            self._block_label.setText("Block 0 / 0")
            self._block_type_label.setText("")
            return
        self._block_label.setText(f"Block {idx + 1} / {n}")
        block = self._blocks[idx]
        label = block.get("label", "")
        btype = block.get("type", "")
        self._block_type_label.setText(f"{label} ({btype})")
