"""A1: Signal Explorer — calibration, block signals, real-time parameter tuning."""

import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QSplitter, QGroupBox, QLineEdit,
    QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

import pyqtgraph as pg

from ..analysis import stubs
from ..themes import LIGHT_THEME, DARK_THEME
from ..widgets.block_navigator import BlockNavigator
from ..widgets.parameter_slider import ParameterSlider
from ..widgets.badge import Badge


class A1Screen(QWidget):
    """Workspace Tab: Signal Explorer."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._stale = False
        self._saccade_region_pool = []  # pre-allocated LinearRegionItems
        self._saccade_pool_size = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(6)

        # ── Calibration section (collapsible) ──
        self._calib_group = QGroupBox("Calibration")
        self._calib_group.setCheckable(True)
        self._calib_group.setChecked(False)
        self._calib_group.setStyleSheet(
            "QGroupBox { background-color: #EFF4F8; "
            "border: 1px solid rgba(62, 110, 140, 0.25); border-radius: 3px; }"
            "QGroupBox::title { color: #2E5A74; font-weight: 700; "
            "text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; }"
        )
        calib_layout = QVBoxLayout(self._calib_group)
        calib_layout.setContentsMargins(8, 4, 8, 4)
        calib_layout.setSpacing(4)

        # Collapsed summary row (always visible)
        summary_row = QHBoxLayout()
        summary_row.setSpacing(6)
        self._calib_summary = QLabel("No calibration loaded")
        self._calib_summary.setStyleSheet("font-size: 11px;")
        summary_row.addWidget(self._calib_summary)
        self._calib_badge = Badge("pending", variant="neutral")
        summary_row.addWidget(self._calib_badge)
        summary_row.addStretch()
        load_btn = QPushButton("Load File")
        load_btn.setProperty("small", True)
        load_btn.clicked.connect(self._on_load_calibration)
        summary_row.addWidget(load_btn)
        manual_btn = QPushButton("Manual")
        manual_btn.setProperty("small", True)
        summary_row.addWidget(manual_btn)
        calib_layout.addLayout(summary_row)

        # Expanded detail row
        self._calib_detail = QWidget()
        detail_layout = QHBoxLayout(self._calib_detail)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(6)
        self._calib_path = QLineEdit()
        self._calib_path.setReadOnly(True)
        self._calib_path.setPlaceholderText("Calibration file path...")
        detail_layout.addWidget(self._calib_path, 1)
        self._calib_ch1 = QLabel("Ch1: —")
        self._calib_ch1.setStyleSheet("font-family: monospace; font-size: 11px;")
        detail_layout.addWidget(self._calib_ch1)
        self._calib_ch2 = QLabel("Ch2: —")
        self._calib_ch2.setStyleSheet("font-family: monospace; font-size: 11px;")
        detail_layout.addWidget(self._calib_ch2)
        apply_btn = QPushButton("Apply")
        apply_btn.setProperty("primary", True)
        detail_layout.addWidget(apply_btn)
        self._calib_detail.setVisible(False)
        calib_layout.addWidget(self._calib_detail)

        self._calib_group.toggled.connect(self._calib_detail.setVisible)
        layout.addWidget(self._calib_group)

        # ── Block navigator ──
        self._block_nav = BlockNavigator()
        self._block_nav.block_selected.connect(self._on_block_selected)
        layout.addWidget(self._block_nav)

        # ── Signal plots ──
        theme = LIGHT_THEME
        plot_splitter = QSplitter(Qt.Horizontal)

        # Eye Position plot
        self._pos_plot = self._make_plot(theme)
        self._pos_plot.setTitle("Eye Position", size="10pt")
        self._pos_plot.setLabel("left", "Position (deg)")
        self._pos_raw = self._pos_plot.plot(
            pen=pg.mkPen(theme["dataRaw"], width=1), name="Raw"
        )
        self._pos_filtered = self._pos_plot.plot(
            pen=pg.mkPen(theme["dataPosition"], width=2), name="Filtered"
        )
        self._pos_saccade = self._pos_plot.plot(
            pen=pg.mkPen(theme["dataSaccade"], width=1.5), name="Saccade"
        )
        plot_splitter.addWidget(self._pos_plot)

        # Eye Velocity plot
        self._vel_plot = self._make_plot(theme)
        self._vel_plot.setTitle("Eye Velocity", size="10pt")
        self._vel_plot.setLabel("left", "Velocity (deg/s)")
        self._vel_stim = self._vel_plot.plot(
            pen=pg.mkPen(theme["dataStimulus"], width=1, style=Qt.DashLine),
            name="Stimulus",
        )
        self._vel_raw = self._vel_plot.plot(
            pen=pg.mkPen(theme["dataRaw"], width=1), name="Raw"
        )
        self._vel_filtered = self._vel_plot.plot(
            pen=pg.mkPen(theme["dataVelocity"], width=2), name="Filtered"
        )
        self._vel_saccade = self._vel_plot.plot(
            pen=pg.mkPen(theme["dataSaccade"], width=1.5), name="Saccade"
        )
        plot_splitter.addWidget(self._vel_plot)

        # Link x-axes
        self._vel_plot.setXLink(self._pos_plot)

        layout.addWidget(plot_splitter, 1)

        # ── Parameter control bar ──
        param_bar = QFrame()
        param_bar.setObjectName("paramBar")
        param_layout = QHBoxLayout(param_bar)
        param_layout.setContentsMargins(8, 6, 8, 6)
        param_layout.setSpacing(8)

        # Position Filter section
        filter_section = QVBoxLayout()
        filter_section.setSpacing(2)
        filter_header = QLabel("POSITION FILTER")
        filter_header.setObjectName("sectionHeader")
        filter_section.addWidget(filter_header)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(6)
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["Butterworth", "Wavelet"])
        self._filter_combo.setCurrentText(self.state.filter_method)
        self._filter_combo.currentTextChanged.connect(
            lambda v: setattr(self.state, "filter_method", v)
        )
        filter_row.addWidget(self._filter_combo)

        self._lp_slider = ParameterSlider(
            label="LP Cutoff", minimum=1, maximum=100,
            default=self.state.lp_cutoff_hz, step=1, suffix="Hz"
        )
        self._lp_slider.value_changed.connect(
            lambda v: setattr(self.state, "lp_cutoff_hz", v)
        )
        filter_row.addWidget(self._lp_slider, 1)
        filter_section.addLayout(filter_row)
        param_layout.addLayout(filter_section, 1)

        # Divider
        param_layout.addWidget(self._make_divider())

        # Differentiation section
        diff_section = QVBoxLayout()
        diff_section.setSpacing(2)
        diff_header = QLabel("DIFFERENTIATION")
        diff_header.setObjectName("sectionHeader")
        diff_section.addWidget(diff_header)

        self._sg_slider = ParameterSlider(
            label="SG Window", minimum=3, maximum=100,
            default=self.state.sg_window_ms, step=1, suffix="ms"
        )
        self._sg_slider.value_changed.connect(
            lambda v: setattr(self.state, "sg_window_ms", v)
        )
        diff_section.addWidget(self._sg_slider)
        param_layout.addLayout(diff_section, 1)

        # Divider
        param_layout.addWidget(self._make_divider())

        # Saccade Detection section
        sac_section = QVBoxLayout()
        sac_section.setSpacing(2)
        sac_header = QLabel("SACCADE DETECTION")
        sac_header.setObjectName("sectionHeader")
        sac_section.addWidget(sac_header)

        sac_row = QHBoxLayout()
        sac_row.setSpacing(6)
        self._sac_combo = QComboBox()
        self._sac_combo.addItems(["SVT", "STD", "MAD"])
        self._sac_combo.setCurrentText(self.state.saccade_method)
        self._sac_combo.currentTextChanged.connect(
            lambda v: setattr(self.state, "saccade_method", v)
        )
        sac_row.addWidget(self._sac_combo)

        self._sac_slider = ParameterSlider(
            label="Threshold", minimum=5, maximum=200,
            default=self.state.saccade_threshold, step=1, suffix="\u00B0/s"
        )
        self._sac_slider.value_changed.connect(
            lambda v: setattr(self.state, "saccade_threshold", v)
        )
        sac_row.addWidget(self._sac_slider, 1)
        sac_section.addLayout(sac_row)
        param_layout.addLayout(sac_section, 1)

        layout.addWidget(param_bar)

        # ── Wire state signals ──
        self.state.selected_block_changed.connect(self._sync_block_nav)
        self.state.parameters_changed.connect(self._on_params_changed)
        self.state.session_data_changed.connect(self._on_session_loaded)
        self.state.workspace_tab_changed.connect(self._on_tab_switch)

        # Bidirectional sync from state to sliders
        self.state.lp_cutoff_hz_changed.connect(self._sync_lp)
        self.state.sg_window_ms_changed.connect(self._sync_sg)
        self.state.saccade_threshold_changed.connect(self._sync_sac)
        self.state.filter_method_changed.connect(self._sync_filter_method)
        self.state.saccade_method_changed.connect(self._sync_sac_method)

    # ── Visibility-gated recompute ──

    def _on_params_changed(self):
        if self.isVisible():
            self._recompute()
        else:
            self._stale = True

    def _on_tab_switch(self, tab):
        if tab == "A1" and self._stale:
            self._recompute()
            self._stale = False

    # ── Helpers ──

    def _make_plot(self, theme):
        pw = pg.PlotWidget()
        pw.setBackground(theme["bgPlot"])
        pw.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
        pw.getAxis("left").setPen(pg.mkPen(theme["border"]))
        pw.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
        pw.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))
        pw.showGrid(x=True, y=True, alpha=0.05)
        pw.setLabel("bottom", "Time (s)")
        pw.setClipToView(True)
        pw.setDownsampling(mode="peak")
        # Semi-transparent legend background
        legend = pw.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(255, 255, 255, 160))
        legend.setPen(pg.mkPen(theme["border"], width=0.5))
        return pw

    def _make_divider(self):
        d = QFrame()
        d.setFrameShape(QFrame.VLine)
        d.setFixedWidth(1)
        return d

    # ── Actions ──

    def _on_load_calibration(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Calibration File", "",
            "Calibration Files (*.mat *.smr);;All Files (*)",
        )
        if not path:
            return
        self._calib_path.setText(path)
        result = stubs.apply_calibration(self.state.session_data, path)
        self.state.scale_ch1 = result["scale_ch1"]
        self.state.scale_ch2 = result["scale_ch2"]
        self.state.active_channel = result["active_channel"]
        self.state.calibration_loaded = True

        self._calib_summary.setText(
            f"Ch1: {result['scale_ch1']:.4f}  Ch2: {result['scale_ch2']:.4f}  "
            f"Active: {result['active_channel']}"
        )
        self._calib_badge.setText("\u2713 OK")
        self._calib_badge.set_variant("green")
        self._calib_ch1.setText(f"Ch1: {result['scale_ch1']:.4f}")
        self._calib_ch2.setText(f"Ch2: {result['scale_ch2']:.4f}")

    def _on_session_loaded(self, session):
        if session is None:
            return
        blocks = session.get("blocks", [])
        self._block_nav.set_blocks(blocks)
        self._block_nav.set_selected(self.state.selected_block)
        self._recompute()

    def _on_block_selected(self, index):
        self.state.selected_block = index
        self._recompute()

    def _sync_block_nav(self, index):
        self._block_nav.set_selected(index)
        self._recompute()

    def _recompute(self):
        """Recompute and update signal plots for the current block."""
        session = self.state.session_data
        if session is None:
            return

        params = self.state.current_params()
        block_index = self.state.selected_block
        data = stubs.process_block(session, block_index, params)

        # Batch all plot updates to avoid redundant repaints
        self._pos_plot.setUpdatesEnabled(False)
        self._vel_plot.setUpdatesEnabled(False)

        t = data["time"]
        mask = data["saccade_mask"]

        # Position plot
        self._pos_raw.setData(t, data["raw_position"])
        self._pos_filtered.setData(t, data["filtered_position"])

        # Saccade segments on position
        sac_pos = data["filtered_position"].copy()
        sac_pos[~mask] = float("nan")
        self._pos_saccade.setData(t, sac_pos, connect="finite")

        # Velocity plot
        self._vel_stim.setData(t, data["stimulus"])
        self._vel_raw.setData(t, data["raw_velocity"])
        self._vel_filtered.setData(t, data["filtered_velocity"])

        sac_vel = data["filtered_velocity"].copy()
        sac_vel[~mask] = float("nan")
        self._vel_saccade.setData(t, sac_vel, connect="finite")

        # Saccade region shading (reuse pooled items)
        theme = DARK_THEME if self.state.dark_mode else LIGHT_THEME
        sac_color = QColor(theme["dataSaccade"])
        sac_color.setAlphaF(0.07)
        sac_brush = pg.mkBrush(sac_color)

        # Find contiguous saccade regions
        diff = np.diff(mask.astype(int))
        starts = np.where(diff == 1)[0] + 1
        ends = np.where(diff == -1)[0] + 1
        if mask[0]:
            starts = np.concatenate([[0], starts])
        if mask[-1]:
            ends = np.concatenate([ends, [len(mask)]])

        num_regions = len(starts)
        needed = num_regions * 2  # 2 plots per region

        # Grow pool if needed
        while len(self._saccade_region_pool) < needed:
            pw = self._pos_plot if len(self._saccade_region_pool) % 2 == 0 else self._vel_plot
            region = pg.LinearRegionItem(values=[0, 0], movable=False, brush=sac_brush)
            region.setZValue(-5)
            region.setVisible(False)
            pw.addItem(region)
            self._saccade_region_pool.append((pw, region))

        # Update visible regions
        idx = 0
        for s, e in zip(starts, ends):
            vals = [t[s], t[min(e, len(t) - 1)]]
            for pw_idx in range(2):
                _, region = self._saccade_region_pool[idx]
                region.setRegion(vals)
                region.setBrush(sac_brush)
                region.setVisible(True)
                idx += 1

        # Hide unused pool items
        for i in range(idx, len(self._saccade_region_pool)):
            self._saccade_region_pool[i][1].setVisible(False)
        self._saccade_pool_size = idx

        # Re-enable painting and trigger single repaint
        self._pos_plot.setUpdatesEnabled(True)
        self._vel_plot.setUpdatesEnabled(True)

    # ── Bidirectional sync ──

    def _sync_lp(self, value):
        self._lp_slider.set_value(value)

    def _sync_sg(self, value):
        self._sg_slider.set_value(value)

    def _sync_sac(self, value):
        self._sac_slider.set_value(value)

    def _sync_filter_method(self, value):
        self._filter_combo.blockSignals(True)
        self._filter_combo.setCurrentText(value)
        self._filter_combo.blockSignals(False)

    def _sync_sac_method(self, value):
        self._sac_combo.blockSignals(True)
        self._sac_combo.setCurrentText(value)
        self._sac_combo.blockSignals(False)

    def retheme(self, theme):
        """Update plot styling when theme changes — no data recomputation."""
        for pw in (self._pos_plot, self._vel_plot):
            pw.setBackground(theme["bgPlot"])
            pw.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
            pw.getAxis("left").setPen(pg.mkPen(theme["border"]))
            pw.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
            pw.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))

        # Update trace pen colors
        self._pos_raw.setPen(pg.mkPen(theme["dataRaw"], width=1))
        self._pos_filtered.setPen(pg.mkPen(theme["dataPosition"], width=2))
        self._pos_saccade.setPen(pg.mkPen(theme["dataSaccade"], width=1.5))
        self._vel_stim.setPen(pg.mkPen(theme["dataStimulus"], width=1, style=Qt.DashLine))
        self._vel_raw.setPen(pg.mkPen(theme["dataRaw"], width=1))
        self._vel_filtered.setPen(pg.mkPen(theme["dataVelocity"], width=2))
        self._vel_saccade.setPen(pg.mkPen(theme["dataSaccade"], width=1.5))

        # Update saccade region brush colors in-place
        sac_color = QColor(theme["dataSaccade"])
        sac_color.setAlphaF(0.07)
        sac_brush = pg.mkBrush(sac_color)
        for i in range(self._saccade_pool_size):
            self._saccade_region_pool[i][1].setBrush(sac_brush)

        # Update calibration section tinting
        self._calib_group.setStyleSheet(
            f"QGroupBox {{ background-color: {theme['bgCalibration']}; "
            f"border: 1px solid rgba(62, 110, 140, 0.25); border-radius: 3px; }}"
            f"QGroupBox::title {{ color: {theme['accentText']}; font-weight: 700; "
            f"text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; }}"
        )
