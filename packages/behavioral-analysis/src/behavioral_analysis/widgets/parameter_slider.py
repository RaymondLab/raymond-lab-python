"""ParameterSlider: composite label + slider + value display with debounced signal."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider
from PySide6.QtCore import Qt, Signal, QTimer


class ParameterSlider(QWidget):
    """Composite slider with label, QSlider, and monospace value display.

    The slider operates on integer steps internally. Use `minimum`, `maximum`,
    and `step` to define the range. The `value` property and `value_changed`
    signal use float values.
    """

    value_changed = Signal(float)

    def __init__(
        self,
        label="",
        minimum=0.0,
        maximum=100.0,
        default=50.0,
        step=1.0,
        suffix="",
        decimals=0,
        parent=None,
    ):
        super().__init__(parent)
        self._min = minimum
        self._max = maximum
        self._step = step
        self._suffix = suffix
        self._decimals = decimals

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Label (right-aligned, 72px min)
        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._label.setMinimumWidth(72)
        self._label.setStyleSheet("font-size: 11px; font-weight: 600;")
        layout.addWidget(self._label)

        # Slider
        self._slider = QSlider(Qt.Horizontal)
        num_steps = int(round((maximum - minimum) / step))
        self._slider.setMinimum(0)
        self._slider.setMaximum(num_steps)
        self._slider.setValue(self._float_to_step(default))
        self._slider.valueChanged.connect(self._on_slider_moved)
        layout.addWidget(self._slider, 1)

        # Value display (monospace, 52px min)
        self._value_display = QLabel(self._format_value(default))
        self._value_display.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._value_display.setMinimumWidth(52)
        self._value_display.setStyleSheet(
            "font-family: 'Consolas', 'SF Mono', 'Menlo', monospace; "
            "font-size: 11px; font-weight: 600;"
        )
        layout.addWidget(self._value_display)

        # Debounce timer (80ms)
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(80)
        self._debounce.timeout.connect(self._emit_value)

        self._pending_value = default

    @property
    def value(self):
        return self._step_to_float(self._slider.value())

    def set_value(self, val):
        """Set the slider value programmatically (no signal emitted)."""
        self._slider.blockSignals(True)
        self._slider.setValue(self._float_to_step(val))
        self._value_display.setText(self._format_value(val))
        self._slider.blockSignals(False)

    def _float_to_step(self, val):
        return int(round((val - self._min) / self._step))

    def _step_to_float(self, step_val):
        return self._min + step_val * self._step

    def _format_value(self, val):
        if self._decimals == 0:
            text = f"{int(round(val))}"
        else:
            text = f"{val:.{self._decimals}f}"
        if self._suffix:
            text += f" {self._suffix}"
        return text

    def _on_slider_moved(self, step_val):
        val = self._step_to_float(step_val)
        self._value_display.setText(self._format_value(val))
        self._pending_value = val
        self._debounce.start()

    def _emit_value(self):
        self.value_changed.emit(self._pending_value)
