"""A2: Block Analysis — cycle-averaged analysis and block metrics."""

import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSplitter, QGroupBox,
)
from PySide6.QtCore import Qt

import pyqtgraph as pg

from ..analysis import stubs
from ..themes import LIGHT_THEME, DARK_THEME
from ..widgets.block_navigator import BlockNavigator
from ..widgets.cycle_navigator import CycleNavigator
from ..widgets.segmented_control import SegmentedControl


class A2Screen(QWidget):
    """Workspace Tab: Block Analysis."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._cycle_data = None
        self._metrics = None
        self._cycle_trace_pool = []  # pre-allocated PlotDataItems for cycle traces
        self._cycle_pool_used = 0
        self._stale = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(6)

        # ── Block navigator ──
        self._block_nav = BlockNavigator()
        self._block_nav.block_selected.connect(self._on_block_selected)
        layout.addWidget(self._block_nav)

        # ── Cycle row: navigator + legend + display mode ──
        cycle_row = QFrame()
        cycle_layout = QHBoxLayout(cycle_row)
        cycle_layout.setContentsMargins(0, 0, 0, 0)
        cycle_layout.setSpacing(8)

        cycle_label = QLabel("CYCLES:")
        cycle_label.setObjectName("sectionHeader")
        cycle_layout.addWidget(cycle_label)

        self._cycle_nav = CycleNavigator()
        self._cycle_nav.setFixedHeight(18)
        self._cycle_nav.cycle_selected.connect(self._on_cycle_selected)
        cycle_layout.addWidget(self._cycle_nav, 1)

        # Legend
        for color, text in [("#1A9E50", "good"), ("#CF2C2C", "saccade"), ("#2D5FD4", "selected")]:
            dot = QLabel("\u25A0")
            dot.setStyleSheet(f"color: {color}; font-size: 8px;")
            cycle_layout.addWidget(dot)
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 9px;")
            cycle_layout.addWidget(lbl)

        # Display mode segmented control
        self._mode_control = SegmentedControl([
            ("SEM", "SEM"),
            ("All Cycles", "All Cycles"),
            ("Good Cycles", "Good Cycles"),
        ])
        self._mode_control.selection_changed.connect(self._on_mode_changed)
        cycle_layout.addWidget(self._mode_control)

        layout.addWidget(cycle_row)

        # ── Main area: plot + metrics card ──
        main_splitter = QSplitter(Qt.Horizontal)

        # Cycle-average plot
        theme = LIGHT_THEME
        self._plot = pg.PlotWidget()
        self._plot.setBackground(theme["bgPlot"])
        self._plot.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
        self._plot.getAxis("left").setPen(pg.mkPen(theme["border"]))
        self._plot.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._plot.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._plot.showGrid(x=True, y=True, alpha=0.05)
        self._plot.setClipToView(True)
        self._plot.setDownsampling(mode="peak")
        self._plot.setLabel("bottom", "Time (s)")
        self._plot.setLabel("left", "Eye Position (deg)")

        # Semi-transparent legend background
        legend = self._plot.addLegend(offset=(10, 10))
        legend.setBrush(pg.mkBrush(255, 255, 255, 160))
        legend.setPen(pg.mkPen(theme["border"], width=0.5))

        # Persistent trace items for SEM mode
        self._stim_curve = self._plot.plot(
            pen=pg.mkPen(theme["dataStimulus"], width=1, style=Qt.DashLine),
            name="Stimulus",
        )
        self._avg_curve = self._plot.plot(
            pen=pg.mkPen(theme["dataVelocity"], width=2), name="Average"
        )
        self._fit_curve = self._plot.plot(
            pen=pg.mkPen(theme["dataFit"], width=1.5), name="Fit"
        )
        self._sem_fill = None  # FillBetweenItem added dynamically

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
            lbl.setStyleSheet("font-size: 11px;")
            row.addWidget(lbl)
            row.addStretch()
            val = QLabel("\u2014")
            val.setStyleSheet(
                "font-family: 'Consolas','SF Mono','Menlo',monospace; "
                "font-size: 11px; font-weight: 600;"
            )
            val.setAlignment(Qt.AlignRight)
            row.addWidget(val)
            metrics_layout.addLayout(row)
            self._metric_labels[key] = val

        metrics_layout.addStretch()
        main_splitter.addWidget(metrics_widget)

        layout.addWidget(main_splitter, 1)

        # ── Wire state signals ──
        self.state.selected_block_changed.connect(self._sync_block)
        self.state.parameters_changed.connect(self._on_params_changed)
        self.state.session_data_changed.connect(self._on_session_loaded)
        self.state.display_mode_changed.connect(self._sync_mode)
        self.state.workspace_tab_changed.connect(self._on_tab_switch)

        # Initial mode
        self._sync_mode(self.state.display_mode)

    # ── Visibility-gated recompute ──

    def _on_params_changed(self):
        if self.isVisible():
            self._recompute()
        else:
            self._stale = True

    def _on_tab_switch(self, tab):
        if tab == "A2" and self._stale:
            self._recompute()
            self._stale = False

    # ── Actions ──

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

    def _sync_block(self, index):
        self._block_nav.set_selected(index)
        self._recompute()

    def _on_cycle_selected(self, index):
        self.state.selected_cycle = index
        self._update_plot()

    def _on_mode_changed(self, mode):
        self.state.display_mode = mode

    def _sync_mode(self, mode):
        self._mode_control.set_selected(mode)
        self._update_plot()

    def _recompute(self):
        session = self.state.session_data
        if session is None:
            return

        params = self.state.current_params()
        block_index = self.state.selected_block

        self._cycle_data = stubs.compute_cycle_analysis(
            session, block_index, params
        )
        self._metrics = stubs.compute_block_metrics(
            session, block_index, params
        )

        # Update cycle navigator
        quality = self._cycle_data.get("cycle_quality", [])
        self._cycle_nav.set_cycle_data(quality)
        sel = min(self.state.selected_cycle, max(0, len(quality) - 1))
        self._cycle_nav.set_selected(sel)

        # Update metrics card
        m = self._metrics
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
        blocks = session.get("blocks", [])
        if block_index < len(blocks):
            b = blocks[block_index]
            self._plot.setTitle(
                f"Block {block_index + 1} ({b['label']})", size="10pt"
            )

        self._update_plot()

    def _update_plot(self):
        if self._cycle_data is None:
            return

        self._plot.setUpdatesEnabled(False)

        cd = self._cycle_data
        mode = self.state.display_mode
        theme = DARK_THEME if self.state.dark_mode else LIGHT_THEME

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

            # SEM fill
            upper = cd["cycle_average"] + cd["cycle_sem"]
            lower = cd["cycle_average"] - cd["cycle_sem"]
            upper_curve = pg.PlotDataItem(t, upper)
            lower_curve = pg.PlotDataItem(t, lower)
            sem_color = pg.mkBrush(
                pg.mkColor(theme["dataSem"]).red(),
                pg.mkColor(theme["dataSem"]).green(),
                pg.mkColor(theme["dataSem"]).blue(),
                80,
            )
            self._sem_fill = pg.FillBetweenItem(upper_curve, lower_curve, brush=sem_color)
            self._sem_fill.setZValue(-5)
            self._plot.addItem(self._sem_fill)

        else:
            # All Cycles or Good Cycles mode
            self._stim_curve.setData(t, cd["stimulus_trace"])
            self._avg_curve.setData(t, cd["cycle_average"])
            self._fit_curve.setData(t, cd["cycle_fit"])

            quality = cd["cycle_quality"]
            selected = self.state.selected_cycle
            traces = cd["cycle_traces"]

            faded_pen = pg.mkPen(theme["dataVelocity"], width=1)
            faded_pen.setColor(pg.mkColor(
                faded_pen.color().red(), faded_pen.color().green(),
                faded_pen.color().blue(), 50
            ))
            selected_pen = pg.mkPen(theme["dataVelocity"], width=2)

            pool_idx = 0
            for i in range(len(quality)):
                if mode == "Good Cycles" and not quality[i]:
                    continue
                pen = selected_pen if i == selected else faded_pen
                item = self._get_cycle_trace_item(pool_idx)
                item.setData(t, traces[i])
                item.setPen(pen)
                item.setVisible(True)
                # Move selected trace to top by setting higher Z
                item.setZValue(10 if i == selected else 0)
                pool_idx += 1

            # Hide unused pool items
            for j in range(pool_idx, len(self._cycle_trace_pool)):
                self._cycle_trace_pool[j].setVisible(False)
            self._cycle_pool_used = pool_idx

        self._plot.setUpdatesEnabled(True)

    def _get_cycle_trace_item(self, idx):
        """Get or create a PlotDataItem from the pool."""
        while idx >= len(self._cycle_trace_pool):
            item = pg.PlotDataItem()
            item.setVisible(False)
            self._plot.addItem(item)
            self._cycle_trace_pool.append(item)
        return self._cycle_trace_pool[idx]

    def retheme(self, theme):
        self._plot.setBackground(theme["bgPlot"])
        self._plot.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
        self._plot.getAxis("left").setPen(pg.mkPen(theme["border"]))
        self._plot.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._plot.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))

        # Update mode control theme
        self._mode_control.set_theme(
            active_bg=theme["accent"],
            active_fg=theme["textInverse"],
            inactive_bg=theme["bgPanel"],
            inactive_fg=theme["textTertiary"],
            border=theme["border"],
        )

        self._update_plot()
