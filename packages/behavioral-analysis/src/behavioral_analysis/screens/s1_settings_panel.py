"""S1: Settings Panel — slide-out drawer with parameter controls."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QFrame, QComboBox, QScrollArea,
)
from PySide6.QtCore import Qt

from ..widgets.parameter_slider import ParameterSlider


class S1Panel(QWidget):
    """Settings slide-out panel (265px wide) with full parameter controls."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.setFixedWidth(265)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Left border (themed via QSS #settingsPanel)
        self.setObjectName("settingsPanel")

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        title = QLabel("\u2699 Settings")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("font-size: 14px; border: none;")
        close_btn.clicked.connect(lambda: setattr(self.state, "settings_open", False))
        header_layout.addWidget(close_btn)
        outer.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        outer.addWidget(sep)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # ── Position Filter ──
        layout.addWidget(self._section_label("POSITION FILTER"))

        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        filter_row.addWidget(QLabel("Method:"))
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["Butterworth", "Wavelet"])
        self._filter_combo.setCurrentText(state.filter_method)
        self._filter_combo.currentTextChanged.connect(
            lambda v: setattr(self.state, "filter_method", v)
        )
        filter_row.addWidget(self._filter_combo)
        layout.addLayout(filter_row)

        self._lp_slider = ParameterSlider(
            label="LP Cutoff", minimum=1, maximum=100,
            default=state.lp_cutoff_hz, step=1, suffix="Hz"
        )
        self._lp_slider.value_changed.connect(
            lambda v: setattr(self.state, "lp_cutoff_hz", v)
        )
        layout.addWidget(self._lp_slider)

        layout.addWidget(self._separator())

        # ── Differentiation ──
        layout.addWidget(self._section_label("DIFFERENTIATION"))

        self._sg_slider = ParameterSlider(
            label="SG Window", minimum=3, maximum=100,
            default=state.sg_window_ms, step=1, suffix="ms"
        )
        self._sg_slider.value_changed.connect(
            lambda v: setattr(self.state, "sg_window_ms", v)
        )
        layout.addWidget(self._sg_slider)

        layout.addWidget(self._separator())

        # ── Saccade Detection ──
        layout.addWidget(self._section_label("SACCADE DETECTION"))

        sac_row = QHBoxLayout()
        sac_row.setSpacing(4)
        sac_row.addWidget(QLabel("Method:"))
        self._sac_combo = QComboBox()
        self._sac_combo.addItems(["SVT", "STD", "MAD"])
        self._sac_combo.setCurrentText(state.saccade_method)
        self._sac_combo.currentTextChanged.connect(
            lambda v: setattr(self.state, "saccade_method", v)
        )
        sac_row.addWidget(self._sac_combo)
        layout.addLayout(sac_row)

        self._sac_slider = ParameterSlider(
            label="Threshold", minimum=5, maximum=200,
            default=state.saccade_threshold, step=1, suffix="\u00B0/s"
        )
        self._sac_slider.value_changed.connect(
            lambda v: setattr(self.state, "saccade_threshold", v)
        )
        layout.addWidget(self._sac_slider)

        self._min_dur_slider = ParameterSlider(
            label="Min Dur", minimum=1, maximum=50,
            default=state.saccade_min_dur_ms, step=1, suffix="ms"
        )
        self._min_dur_slider.value_changed.connect(
            lambda v: setattr(self.state, "saccade_min_dur_ms", v)
        )
        layout.addWidget(self._min_dur_slider)

        self._padding_slider = ParameterSlider(
            label="Padding", minimum=0, maximum=20,
            default=state.saccade_padding_ms, step=1, suffix="ms"
        )
        self._padding_slider.value_changed.connect(
            lambda v: setattr(self.state, "saccade_padding_ms", v)
        )
        layout.addWidget(self._padding_slider)

        layout.addWidget(self._separator())

        # ── Eye Channel ──
        layout.addWidget(self._section_label("EYE CHANNEL"))
        ch_row = QHBoxLayout()
        ch_row.setSpacing(4)
        ch_row.addWidget(QLabel("Active:"))
        self._channel_combo = QComboBox()
        self._channel_combo.addItems(["Auto", "Ch1", "Ch2"])
        self._channel_combo.setCurrentText(state.active_channel)
        self._channel_combo.currentTextChanged.connect(
            lambda v: setattr(self.state, "active_channel", v)
        )
        ch_row.addWidget(self._channel_combo)
        layout.addLayout(ch_row)

        layout.addWidget(self._separator())

        # ── Appearance ──
        layout.addWidget(self._section_label("APPEARANCE"))
        self._dark_mode_cb = QCheckBox("Dark Theme")
        self._dark_mode_cb.setChecked(state.dark_mode)
        self._dark_mode_cb.toggled.connect(
            lambda v: setattr(self.state, "dark_mode", v)
        )
        layout.addWidget(self._dark_mode_cb)

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # Footer
        footer_sep = QFrame()
        footer_sep.setFrameShape(QFrame.HLine)
        outer.addWidget(footer_sep)

        footer = QFrame()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 6, 12, 6)
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset)
        footer_layout.addWidget(reset_btn)
        outer.addWidget(footer)

        # ── Wire bidirectional sync from state ──
        self.state.lp_cutoff_hz_changed.connect(self._sync_lp)
        self.state.sg_window_ms_changed.connect(self._sync_sg)
        self.state.saccade_threshold_changed.connect(self._sync_sac)
        self.state.saccade_min_dur_ms_changed.connect(self._sync_min_dur)
        self.state.saccade_padding_ms_changed.connect(self._sync_padding)
        self.state.filter_method_changed.connect(self._sync_filter_method)
        self.state.saccade_method_changed.connect(self._sync_sac_method)
        self.state.active_channel_changed.connect(self._sync_channel)
        self.state.dark_mode_changed.connect(self._sync_dark_mode)

    # ── Helpers ──

    def _section_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("sectionHeader")
        return lbl

    def _separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        return sep

    # ── Actions ──

    def _on_reset(self):
        self.state.reset_parameters()

    # ── Bidirectional sync ──

    def _sync_lp(self, v):
        self._lp_slider.set_value(v)

    def _sync_sg(self, v):
        self._sg_slider.set_value(v)

    def _sync_sac(self, v):
        self._sac_slider.set_value(v)

    def _sync_min_dur(self, v):
        self._min_dur_slider.set_value(v)

    def _sync_padding(self, v):
        self._padding_slider.set_value(v)

    def _sync_filter_method(self, v):
        self._filter_combo.blockSignals(True)
        self._filter_combo.setCurrentText(v)
        self._filter_combo.blockSignals(False)

    def _sync_sac_method(self, v):
        self._sac_combo.blockSignals(True)
        self._sac_combo.setCurrentText(v)
        self._sac_combo.blockSignals(False)

    def _sync_channel(self, v):
        self._channel_combo.blockSignals(True)
        self._channel_combo.setCurrentText(v)
        self._channel_combo.blockSignals(False)

    def _sync_dark_mode(self, v):
        self._dark_mode_cb.blockSignals(True)
        self._dark_mode_cb.setChecked(v)
        self._dark_mode_cb.blockSignals(False)
