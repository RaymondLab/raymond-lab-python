"""FlowLayout: a layout that wraps widgets to the next line when width is exceeded."""

from PySide6.QtWidgets import QLayout, QSizePolicy
from PySide6.QtCore import Qt, QRect, QSize


class FlowLayout(QLayout):
    """Layout that arranges widgets horizontally, wrapping to the next row."""

    def __init__(self, parent=None, h_spacing=7, v_spacing=7):
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items = []

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0

        for item in self._items:
            w = item.sizeHint().width()
            h = item.sizeHint().height()

            if x + w > effective.right() + 1 and line_height > 0:
                x = effective.x()
                y += line_height + self._v_spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(x, y, w, h))

            x += w + self._h_spacing
            line_height = max(line_height, h)

        return y + line_height - rect.y() + m.bottom()
