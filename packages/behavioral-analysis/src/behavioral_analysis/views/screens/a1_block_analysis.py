"""A1: Block Analysis — cycle-averaged analysis and block metrics."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSplitter, QGroupBox,
)
from PySide6.QtCore import Qt

import pyqtgraph as pg

from ...themes import THEME
from ..widgets.block_navigator import BlockNavigator
from ..widgets.cycle_navigator import CycleNavigator
from ..widgets.segmented_control import SegmentedControl


class A1Screen(QWidget):
    """Workspace Tab: Block Analysis."""

    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self._cycle_trace_pool = []
        self._cycle_pool_used = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(6)

        # ── Block navigator ──
        self._block_nav = BlockNavigator()
        self._block_nav.block_selected.connect(lambda i: self.vm.select_block(i))
        layout.addWidget(self._block_nav)

        # ── Cycle row ──
        cycle_row = QFrame()
        cycle_layout = QHBoxLayout(cycle_row)
        cycle_layout.setContentsMargins(0, 0, 0, 0)
        cycle_layout.setSpacing(8)

        cycle_label = QLabel("CYCLES:")
        cycle_label.setObjectName("sectionHeader")
        cycle_layout.addWidget(cycle_label)

        self._cycle_nav = CycleNavigator()
        self._cycle_nav.setFixedHeight(18)
        self._cycle_nav.cycle_selected.connect(lambda i: self.vm.select_cycle(i))
        cycle_layout.addWidget(self._cycle_nav, 1)

        # Legend
        for color, text in [
            (THEME["qualGood"], "good"),
            (THEME["qualBad"], "saccade"),
            (THEME["qualSelected"], "selected"),
        ]:
            dot = QLabel("\u25A0")
            dot.setStyleSheet(f"color: {color}; font-size: 8px;")
            cycle_layout.addWidget(dot)
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-size: {THEME['fontXs']};")
            cycle_layout.addWidget(lbl)

        # Display mode
        self._mode_control = SegmentedControl([
            ("SEM", "SEM"),
            ("All Cycles", "All Cycles"),
            ("Good Cycles", "Good Cycles"),
        ])
        self._mode_control.selection_changed.connect(
            lambda m: self.vm.set_display_mode(m)
        )
        cycle_layout.addWidget(self._mode_control)

        layout.addWidget(cycle_row)

        # ── Main area: plot + metrics card ──
        main_splitter = QSplitter(Qt.Horizontal)

        # Cycle-average plot
        self._plot = pg.PlotWidget()
        self._plot.setBackground(THEME["bgPlot"])
        self._plot.getAxis("bottom").setPen(pg.mkPen(THEME["border"]))
        self._plot.getAxis("left").setPen(pg.mkPen(THEME["border"]))
        self._plot.getAxis("bottom").setTextPen(pg.mkPen(THEME["textTertiary"]))
        self._plot.getAxis("left").setTextPen(pg.mkPen(THEME["textTertiary"]))
        self._plot.showGrid(x=True, y=True, alpha=0.05)
        self._plot.setClipToView(True)
        self._plot.setDownsampling(mode="peak")
        self._plot.setLabel("bottom", "Time (s)")
        self._plot.setLabel("left", "Eye Position (deg)")

        legend = self._plot.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(255, 255, 255, 160))
        legend.setPen(pg.mkPen(THEME["border"], width=0.5))

        self._stim_curve = self._plot.plot(
            pen=pg.mkPen(THEME["dataStimulus"], width=1, style=Qt.DashLine),
            name="Stimulus",
        )
        self._avg_curve = self._plot.plot(
            pen=pg.mkPen(THEME["dataVelocity"], width=2), name="Average"
        )
        self._fit_curve = self._plot.plot(
            pen=pg.mkPen(THEME["dataFit"], width=1.5), name="Fit"
        )
        self._sem_fill = None

        main_splitter.addWidget(self._plot)

        # Metrics card
        metrics_widget = QGroupBox("Block Metrics")
        metrics_widget.setFixedWidth(168)
        metrics_layout = QVBoxLayout(metrics_widget)
        metrics_layout.setContentsMargins(8, 8, 8, 8)
        metrics_layout.setSpacing(4)

        self._metric_labels = {}
        for key, label in [
            ("gain", "Gain"),
            ("eye_amp", "Eye Amp"),
            ("eye_amp_sem", "  \u00B1 SEM"),
            ("eye_phase", "Phase"),
            ("eye_phase_sem", "  \u00B1 SEM"),
            ("stim_amp", "Stim Amp"),
            ("freq_hz", "Freq"),
            ("good_cycles", "Good Cycles"),
            ("var_residual", "Var Residual"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: {THEME['fontSm']};")
            row.addWidget(lbl)
            row.addStretch()
            val = QLabel("\u2014")
            val.setStyleSheet(
                f"font-family: {THEME['fontMono']}; "
                f"font-size: {THEME['fontSm']}; font-weight: 600;"
            )
            val.setAlignment(Qt.AlignRight)
            row.addWidget(val)
            metrics_layout.addLayout(row)
            self._metric_labels[key] = val

        metrics_layout.addStretch()
        main_splitter.addWidget(metrics_widget)

        layout.addWidget(main_splitter, 1)

        # ── Wire VM signals ──
        self.vm.selected_block_changed.connect(self._on_block_changed)
        self.vm.block_signals_recomputed.connect(self._refresh)
        self.vm.selected_cycle_changed.connect(
            lambda i: self._cycle_nav.set_selected(i)
        )
        self.vm.display_mode_changed.connect(self._on_mode_changed)
        self.vm.session_info_changed.connect(self._on_session_loaded)

    # ── Handlers ──

    def _on_session_loaded(self):
        if not self.vm.is_file_loaded:
            return
        blocks = self.vm.data.raw.get("blocks", [])
        self._block_nav.set_blocks(blocks)
        self._block_nav.set_selected(self.vm.selected_block)

    def _on_block_changed(self, index):
        self._block_nav.set_selected(index)

    def _on_mode_changed(self, mode):
        self._mode_control.set_selected(mode)
        self._update_plot()

    def _refresh(self):
        """Refresh cycle data, metrics, and plot from cached VM data."""
        cd = self.vm.data.current_cycle_data
        m = self.vm.data.current_block_metrics
        if cd is None or m is None:
            return

        # Update cycle navigator
        quality = cd.get("cycle_quality", [])
        self._cycle_nav.set_cycle_data(quality)
        sel = min(self.vm.selected_cycle, max(0, len(quality) - 1))
        self._cycle_nav.set_selected(sel)

        # Update metrics card
        self._metric_labels["gain"].setText(f"{m['gain']:.4f}")
        self._metric_labels["eye_amp"].setText(f"{m['eye_amp']:.2f}")
        self._metric_labels["eye_amp_sem"].setText(f"{m['eye_amp_sem']:.3f}")
        self._metric_labels["eye_phase"].setText(f"{m['eye_phase']:.2f}\u00B0")
        self._metric_labels["eye_phase_sem"].setText(f"{m['eye_phase_sem']:.2f}\u00B0")
        self._metric_labels["stim_amp"].setText(f"{m['stim_amp']:.1f}")
        self._metric_labels["freq_hz"].setText(f"{m['freq_hz']:.1f} Hz")
        self._metric_labels["good_cycles"].setText(
            f"{m['good_cycles']}/{m['total_cycles']}"
        )
        self._metric_labels["var_residual"].setText(f"{m['var_residual']:.4f}")

        # Update plot title
        blocks = self.vm.data.raw.get("blocks", [])
        bi = self.vm.selected_block
        if bi < len(blocks):
            b = blocks[bi]
            self._plot.setTitle(
                f"Block {bi + 1} ({b['label']})", size="10pt"
            )

        self._update_plot()

    def _update_plot(self):
        cd = self.vm.data.current_cycle_data
        if cd is None:
            return

        self._plot.setUpdatesEnabled(False)

        mode = self.vm.data.display_mode

        # Hide cycle trace pool items
        for j in range(self._cycle_pool_used):
            self._cycle_trace_pool[j].setVisible(False)
        self._cycle_pool_used = 0

        if self._sem_fill is not None:
            self._plot.removeItem(self._sem_fill)
            self._sem_fill = None

        t = cd["cycle_time"]

        if mode == "SEM":
            self._stim_curve.setData(t, cd["stimulus_trace"])
            self._avg_curve.setData(t, cd["cycle_average"])
            self._fit_curve.setData(t, cd["cycle_fit"])

            upper = cd["cycle_average"] + cd["cycle_sem"]
            lower = cd["cycle_average"] - cd["cycle_sem"]
            upper_curve = pg.PlotDataItem(t, upper)
            lower_curve = pg.PlotDataItem(t, lower)
            sem_color = pg.mkBrush(
                pg.mkColor(THEME["dataSem"]).red(),
                pg.mkColor(THEME["dataSem"]).green(),
                pg.mkColor(THEME["dataSem"]).blue(),
                80,
            )
            self._sem_fill = pg.FillBetweenItem(
                upper_curve, lower_curve, brush=sem_color
            )
            self._sem_fill.setZValue(-5)
            self._plot.addItem(self._sem_fill)
        else:
            self._stim_curve.setData(t, cd["stimulus_trace"])
            self._avg_curve.setData(t, cd["cycle_average"])
            self._fit_curve.setData(t, cd["cycle_fit"])

            quality = cd["cycle_quality"]
            selected = self.vm.selected_cycle
            traces = cd["cycle_traces"]

            faded_pen = pg.mkPen(THEME["dataVelocity"], width=1)
            faded_pen.setColor(pg.mkColor(
                faded_pen.color().red(), faded_pen.color().green(),
                faded_pen.color().blue(), 50
            ))
            selected_pen = pg.mkPen(THEME["dataVelocity"], width=2)

            pool_idx = 0
            for i in range(len(quality)):
                if mode == "Good Cycles" and not quality[i]:
                    continue
                pen = selected_pen if i == selected else faded_pen
                item = self._get_cycle_trace_item(pool_idx)
                item.setData(t, traces[i])
                item.setPen(pen)
                item.setVisible(True)
                item.setZValue(10 if i == selected else 0)
                pool_idx += 1

            for j in range(pool_idx, len(self._cycle_trace_pool)):
                self._cycle_trace_pool[j].setVisible(False)
            self._cycle_pool_used = pool_idx

        self._plot.setUpdatesEnabled(True)

    def _get_cycle_trace_item(self, idx):
        while idx >= len(self._cycle_trace_pool):
            item = pg.PlotDataItem()
            item.setVisible(False)
            self._plot.addItem(item)
            self._cycle_trace_pool.append(item)
        return self._cycle_trace_pool[idx]
