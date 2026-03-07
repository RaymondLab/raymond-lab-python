"""W3: Signal Explorer — calibration, block signals, real-time parameter tuning."""

import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QSplitter, QGroupBox, QLineEdit,
    QFileDialog, QDoubleSpinBox, QSpinBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

import pyqtgraph as pg

from ...themes import THEME
from ..widgets.block_navigator import BlockNavigator
from ..widgets.badge import Badge


class W3Screen(QWidget):
    """Wizard Step 3: Signal Explorer — calibration + parameter tuning."""

    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self._updating_view = False
        self._saccade_region_pool = []
        self._saccade_pool_used = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(6)

        # ── Control bar ──
        ctrl = QFrame()
        ctrl.setObjectName("w1ControlBar")
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(12, 14, 12, 18)
        ctrl_layout.setSpacing(8)

        back_btn = QPushButton("\u2190 Back")
        back_btn.clicked.connect(lambda: self.vm.go_to_wizard_step(2))
        ctrl_layout.addWidget(back_btn)

        ctrl_layout.addStretch()

        start_btn = QPushButton("Start Analysis \u2192")
        start_btn.setProperty("primary", True)
        start_btn.clicked.connect(lambda: self.vm.start_analysis())
        ctrl_layout.addWidget(start_btn)

        layout.addWidget(ctrl)

        # ── Calibration section ──
        self._calib_group = QGroupBox("Calibration")
        self._calib_group.setStyleSheet(
            f"QGroupBox {{ background-color: {THEME['bgCalibration']}; "
            f"border: 1px solid rgba(62, 110, 140, 0.25); border-radius: 3px; }}"
            f"QGroupBox::title {{ color: {THEME['accentText']}; font-weight: 700; "
            f"text-transform: uppercase; font-size: {THEME['fontXs']}; "
            f"letter-spacing: 0.05em; }}"
        )
        calib_layout = QHBoxLayout(self._calib_group)
        calib_layout.setContentsMargins(8, 4, 8, 4)
        calib_layout.setSpacing(6)

        load_btn = QPushButton("Load File")
        load_btn.setProperty("small", True)
        load_btn.clicked.connect(self._on_load_calibration)
        calib_layout.addWidget(load_btn)
        manual_btn = QPushButton("Manual")
        manual_btn.setProperty("small", True)
        calib_layout.addWidget(manual_btn)

        self._calib_badge = Badge("pending", variant="neutral")
        calib_layout.addWidget(self._calib_badge)

        self._calib_summary = QLabel("No calibration loaded")
        self._calib_summary.setStyleSheet(f"font-size: {THEME['fontSm']};")
        calib_layout.addWidget(self._calib_summary)

        self._calib_path = QLineEdit()
        self._calib_path.setReadOnly(True)
        self._calib_path.setPlaceholderText("Calibration file path...")
        self._calib_path.setVisible(False)
        calib_layout.addWidget(self._calib_path, 1)

        calib_layout.addStretch()
        layout.addWidget(self._calib_group)

        # ── Block navigator ──
        self._block_nav = BlockNavigator()
        self._block_nav.block_selected.connect(lambda i: self.vm.select_block(i))
        layout.addWidget(self._block_nav)

        # ── Signal plots ──
        plot_splitter = QSplitter(Qt.Horizontal)

        # Eye Position plot
        self._pos_plot = self._make_plot()
        self._pos_plot.setTitle("Eye Position", size="10pt")
        self._pos_plot.setLabel("left", "Position (deg)")
        self._pos_raw = self._pos_plot.plot(
            pen=pg.mkPen(THEME["dataRaw"], width=1), name="Raw"
        )
        self._pos_filtered = self._pos_plot.plot(
            pen=pg.mkPen(THEME["dataPosition"], width=2), name="Filtered"
        )
        self._pos_saccade = self._pos_plot.plot(
            pen=pg.mkPen(THEME["dataSaccade"], width=1.5), name="Saccade"
        )
        plot_splitter.addWidget(self._pos_plot)

        # Eye Velocity plot
        self._vel_plot = self._make_plot()
        self._vel_plot.setTitle("Eye Velocity", size="10pt")
        self._vel_plot.setLabel("left", "Velocity (deg/s)")
        self._vel_stim = self._vel_plot.plot(
            pen=pg.mkPen(THEME["dataStimulus"], width=1, style=Qt.DashLine),
            name="Stimulus",
        )
        self._vel_raw = self._vel_plot.plot(
            pen=pg.mkPen(THEME["dataRaw"], width=1), name="Raw"
        )
        self._vel_filtered = self._vel_plot.plot(
            pen=pg.mkPen(THEME["dataVelocity"], width=2), name="Filtered"
        )
        self._vel_saccade = self._vel_plot.plot(
            pen=pg.mkPen(THEME["dataSaccade"], width=1.5), name="Saccade"
        )
        plot_splitter.addWidget(self._vel_plot)

        self._vel_plot.setXLink(self._pos_plot)
        layout.addWidget(plot_splitter, 1)

        # ── Parameter control bar ──
        param_bar = QFrame()
        param_bar.setObjectName("paramBar")
        param_bar.setStyleSheet(
            f"#paramBar {{ background-color: {THEME['accentDark']}; "
            f"border: 1px solid {THEME['accentDark']}; border-radius: 3px; }}"
            f"#paramBar QLabel {{ color: {THEME['textOnTopbar']}; }}"
            f"#paramBar QLabel#sectionHeader {{ color: rgba(255,255,255,0.5); }}"
            f"#paramBar QComboBox {{ background-color: {THEME['bgInput']}; "
            f"border: 1px solid rgba(255,255,255,0.15); "
            f"color: {THEME['textPrimary']}; }}"
            f"#paramBar QDoubleSpinBox, #paramBar QSpinBox {{ "
            f"background-color: {THEME['bgInput']}; "
            f"border: 1px solid rgba(255,255,255,0.15); "
            f"color: {THEME['textPrimary']}; border-radius: 3px; "
            f"padding: 2px 4px; font-size: 11px; }}"
            f"#paramBar QPushButton {{ background-color: transparent; "
            f"border: 1px solid rgba(255,255,255,0.2); "
            f"color: {THEME['textOnTopbar']}; }}"
            f"#paramBar QPushButton:hover {{ border-color: rgba(255,255,255,0.4); "
            f"color: {THEME['textInverse']}; }}"
            f"#paramBar QFrame {{ color: rgba(255,255,255,0.6); }}"
        )
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
        self._filter_combo.view().setMinimumWidth(120)
        self._filter_combo.currentTextChanged.connect(
            lambda v: self._on_combo_changed("filter_method", v)
        )
        filter_row.addWidget(self._filter_combo)

        lp_label = QLabel("LP Cutoff")
        lp_label.setObjectName("sectionHeader")
        filter_row.addWidget(lp_label)
        self._lp_spin = QDoubleSpinBox()
        self._lp_spin.setRange(4.0, 250.0)
        self._lp_spin.setValue(11.0)
        self._lp_spin.setDecimals(1)
        self._lp_spin.setSingleStep(1.0)
        self._lp_spin.setSuffix(" Hz")
        self._lp_spin.setFixedWidth(90)
        self._lp_spin.valueChanged.connect(
            lambda v: self._on_spin_changed("lp_cutoff", v)
        )
        filter_row.addWidget(self._lp_spin)
        filter_section.addLayout(filter_row)
        param_layout.addLayout(filter_section)

        self._add_divider(param_layout)

        # Differentiation section
        diff_section = QVBoxLayout()
        diff_section.setSpacing(2)
        diff_header = QLabel("DIFFERENTIATION")
        diff_header.setObjectName("sectionHeader")
        diff_section.addWidget(diff_header)

        sg_row = QHBoxLayout()
        sg_row.setSpacing(6)
        sg_label = QLabel("SG Window")
        sg_label.setObjectName("sectionHeader")
        sg_row.addWidget(sg_label)
        self._sg_spin = QSpinBox()
        self._sg_spin.setRange(3, 31)
        self._sg_spin.setValue(11)
        self._sg_spin.setSingleStep(2)
        self._sg_spin.setSuffix(" ms")
        self._sg_spin.setFixedWidth(80)
        self._sg_spin.valueChanged.connect(
            lambda v: self._on_spin_changed("sg_window", self._enforce_odd(v))
        )
        sg_row.addWidget(self._sg_spin)
        diff_section.addLayout(sg_row)
        param_layout.addLayout(diff_section)

        self._add_divider(param_layout)

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
        self._sac_combo.view().setMinimumWidth(60)
        self._sac_combo.currentTextChanged.connect(
            lambda v: self._on_combo_changed("saccade_method", v)
        )
        sac_row.addWidget(self._sac_combo)

        thresh_label = QLabel("Threshold")
        thresh_label.setObjectName("sectionHeader")
        sac_row.addWidget(thresh_label)
        self._thresh_spin = QDoubleSpinBox()
        self._thresh_spin.setRange(1.0, 99999.0)
        self._thresh_spin.setValue(1000.0)
        self._thresh_spin.setDecimals(1)
        self._thresh_spin.setSingleStep(10.0)
        self._thresh_spin.setSuffix(" \u00B0/s")
        self._thresh_spin.setFixedWidth(110)
        self._thresh_spin.valueChanged.connect(
            lambda v: self._on_spin_changed("saccade_threshold", v)
        )
        sac_row.addWidget(self._thresh_spin)

        mindur_label = QLabel("Min Dur")
        mindur_label.setObjectName("sectionHeader")
        sac_row.addWidget(mindur_label)
        self._min_dur_spin = QSpinBox()
        self._min_dur_spin.setRange(1, 1000)
        self._min_dur_spin.setValue(10)
        self._min_dur_spin.setSingleStep(1)
        self._min_dur_spin.setSuffix(" ms")
        self._min_dur_spin.setFixedWidth(80)
        self._min_dur_spin.valueChanged.connect(
            lambda v: self._on_spin_changed("saccade_min_dur", v)
        )
        sac_row.addWidget(self._min_dur_spin)

        pad_label = QLabel("Padding")
        pad_label.setObjectName("sectionHeader")
        sac_row.addWidget(pad_label)
        self._padding_spin = QSpinBox()
        self._padding_spin.setRange(1, 1000)
        self._padding_spin.setValue(5)
        self._padding_spin.setSingleStep(1)
        self._padding_spin.setSuffix(" ms")
        self._padding_spin.setFixedWidth(80)
        self._padding_spin.valueChanged.connect(
            lambda v: self._on_spin_changed("saccade_padding", v)
        )
        sac_row.addWidget(self._padding_spin)

        sac_section.addLayout(sac_row)
        param_layout.addLayout(sac_section)

        self._add_divider(param_layout)

        # Eye Channel section
        eye_section = QVBoxLayout()
        eye_section.setSpacing(2)
        eye_header = QLabel("EYE CHANNEL")
        eye_header.setObjectName("sectionHeader")
        eye_section.addWidget(eye_header)

        self._eye_combo = QComboBox()
        self._eye_combo.addItems(["Auto", "Ch1", "Ch2"])
        self._eye_combo.currentTextChanged.connect(
            lambda v: self._on_combo_changed("eye_channel", v)
        )
        eye_section.addWidget(self._eye_combo)
        param_layout.addLayout(eye_section)

        self._add_divider(param_layout)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._on_reset)
        param_layout.addWidget(reset_btn)

        layout.addWidget(param_bar)

        # ── Wire VM signals ──
        self.vm.session_info_changed.connect(self._on_session_loaded)
        self.vm.selected_block_changed.connect(self._on_block_changed)
        self.vm.block_signals_recomputed.connect(self._refresh_plots)
        self.vm.params_changed.connect(self._refresh_param_display)
        self.vm.calibration_changed.connect(self._refresh_calibration)
        self.vm.filter_method_changed.connect(self._on_filter_method_changed)

    # ── Helpers ──

    def _make_plot(self):
        pw = pg.PlotWidget()
        pw.setBackground(THEME["bgPlot"])
        pw.getAxis("bottom").setPen(pg.mkPen(THEME["border"]))
        pw.getAxis("left").setPen(pg.mkPen(THEME["border"]))
        pw.getAxis("bottom").setTextPen(pg.mkPen(THEME["textTertiary"]))
        pw.getAxis("left").setTextPen(pg.mkPen(THEME["textTertiary"]))
        pw.showGrid(x=True, y=True, alpha=0.05)
        pw.setLabel("bottom", "Time (s)")
        pw.setClipToView(True)
        pw.setDownsampling(mode="peak")
        legend = pw.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(255, 255, 255, 160))
        legend.setPen(pg.mkPen(THEME["border"], width=0.5))
        return pw

    def _add_divider(self, layout, pad=6):
        """Add a 1px vertical divider with horizontal padding to a layout."""
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy
        layout.addItem(QSpacerItem(pad, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        d = QFrame()
        d.setFrameShape(QFrame.VLine)
        d.setFixedWidth(1)
        layout.addWidget(d)
        layout.addItem(QSpacerItem(pad, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))

    # ── Combo guard ──

    def _on_combo_changed(self, param_name, value):
        if self._updating_view:
            return
        if param_name == "filter_method":
            self.vm.set_filter_method(value)
        elif param_name == "saccade_method":
            self.vm.set_saccade_method(value)
        elif param_name == "eye_channel":
            self.vm.set_eye_channel(value)

    # ── Spin guard ──

    def _on_spin_changed(self, param_name, value):
        if self._updating_view:
            return
        if param_name == "lp_cutoff":
            self.vm.set_lp_cutoff(value)
        elif param_name == "sg_window":
            self.vm.set_sg_window(value)
        elif param_name == "saccade_threshold":
            self.vm.set_saccade_threshold(value)
        elif param_name == "saccade_min_dur":
            self.vm.set_saccade_min_dur(value)
        elif param_name == "saccade_padding":
            self.vm.set_saccade_padding(value)

    def _enforce_odd(self, value):
        """Ensure SG window is odd; snap even values up."""
        if value % 2 == 0:
            corrected = value + 1
            self._sg_spin.blockSignals(True)
            self._sg_spin.setValue(corrected)
            self._sg_spin.blockSignals(False)
            return corrected
        return value

    # ── Actions ──

    def _on_load_calibration(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Calibration File", "",
            "Calibration Files (*.mat *.smr);;All Files (*)",
        )
        if path:
            self.vm.load_calibration_file(path)

    def _on_session_loaded(self):
        if not self.vm.is_file_loaded:
            return
        blocks = self.vm.data.raw.get("blocks", [])
        self._block_nav.set_blocks(blocks)
        self._block_nav.set_selected(self.vm.selected_block)

    def _on_block_changed(self, index):
        self._block_nav.set_selected(index)

    def _on_reset(self):
        self.vm.reset_params_to_defaults()

    def _on_filter_method_changed(self, method):
        self._updating_view = True
        self._filter_combo.setCurrentText(method)
        self._updating_view = False

    # ── Refresh from VM ──

    def _refresh_param_display(self):
        """Sync spinbox/combo values from VM params using _updating_view guard."""
        self._updating_view = True
        p = self.vm.params
        self._lp_spin.setValue(p.lp_cutoff_hz)
        self._sg_spin.setValue(int(p.sg_window_ms))
        self._thresh_spin.setValue(p.saccade_threshold)
        self._min_dur_spin.setValue(int(p.saccade_min_dur_ms))
        self._padding_spin.setValue(int(p.saccade_padding_ms))
        self._filter_combo.setCurrentText(p.filter_method)
        self._sac_combo.setCurrentText(p.saccade_method)
        self._eye_combo.setCurrentText(p.eye_channel)
        self._updating_view = False

    def _refresh_calibration(self):
        cal = self.vm.calibration
        if cal.is_loaded:
            self._calib_summary.setText(
                f"Ch1: {cal.scale_ch1:.4f}  Ch2: {cal.scale_ch2:.4f}  "
                f"Active: {cal.active_channel}"
            )
            self._calib_badge.setText("\u2713 OK")
            self._calib_badge.set_variant("green")
            if cal.file_path:
                self._calib_path.setText(cal.file_path)
                self._calib_path.setVisible(True)
            else:
                self._calib_path.setVisible(False)

    def _refresh_plots(self):
        """Update signal plots from cached VM data."""
        data = self.vm.data.current_block_signals
        if data is None:
            return

        self._pos_plot.setUpdatesEnabled(False)
        self._vel_plot.setUpdatesEnabled(False)

        t = data["time"]
        mask = data["saccade_mask"]

        # Position plot
        self._pos_raw.setData(t, data["raw_position"])
        self._pos_filtered.setData(t, data["filtered_position"])

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

        # Saccade region shading
        sac_color = QColor(THEME["dataSaccade"])
        sac_color.setAlphaF(0.07)
        sac_brush = pg.mkBrush(sac_color)

        diff = np.diff(mask.astype(int))
        starts = np.where(diff == 1)[0] + 1
        ends = np.where(diff == -1)[0] + 1
        if mask[0]:
            starts = np.concatenate([[0], starts])
        if mask[-1]:
            ends = np.concatenate([ends, [len(mask)]])

        num_regions = len(starts)
        needed = num_regions * 2

        # Grow pool if needed
        while len(self._saccade_region_pool) < needed:
            pw = self._pos_plot if len(self._saccade_region_pool) % 2 == 0 else self._vel_plot
            region = pg.LinearRegionItem(values=[0, 0], movable=False, brush=sac_brush)
            region.setZValue(-5)
            region.setVisible(False)
            pw.addItem(region)
            self._saccade_region_pool.append((pw, region))

        idx = 0
        for s, e in zip(starts, ends):
            vals = [t[s], t[min(e, len(t) - 1)]]
            for _ in range(2):
                _, region = self._saccade_region_pool[idx]
                region.setRegion(vals)
                region.setBrush(sac_brush)
                region.setVisible(True)
                idx += 1

        for i in range(idx, len(self._saccade_region_pool)):
            self._saccade_region_pool[i][1].setVisible(False)
        self._saccade_pool_used = idx

        self._pos_plot.setUpdatesEnabled(True)
        self._vel_plot.setUpdatesEnabled(True)
