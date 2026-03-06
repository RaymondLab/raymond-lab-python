"""A2: Block Analysis — cycle-averaged analysis and block metrics."""

import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QGroupBox,
)
from PySide6.QtCore import Qt

import pyqtgraph as pg

from ..analysis import stubs
from ..themes import LIGHT_THEME, DARK_THEME
from ..widgets.block_navigator import BlockNavigator
from ..widgets.cycle_navigator import CycleNavigator


class A2Screen(QWidget):
    """Workspace Tab: Block Analysis."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._cycle_data = None
        self._metrics = None
        self._cycle_trace_items = []

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
        cycle_label.setStyleSheet(
            "font-size: 10px; font-weight: 700; letter-spacing: 0.06em;"
        )
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

        # Display mode toggle
        self._mode_buttons = {}
        for mode in ["SEM", "All Cycles", "Good Cycles"]:
            btn = QPushButton(mode)
            btn.setCheckable(True)
            btn.setStyleSheet("font-size: 10px; padding: 2px 8px;")
            btn.clicked.connect(lambda _, m=mode: self._on_mode_changed(m))
            self._mode_buttons[mode] = btn
            cycle_layout.addWidget(btn)

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
        self._plot.showGrid(x=True, y=True, alpha=0.1)
        self._plot.addLegend(offset=(10, 10))

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
            val = QLabel("—")
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
        self.state.parameters_changed.connect(self._recompute)
        self.state.session_data_changed.connect(self._on_session_loaded)
        self.state.display_mode_changed.connect(self._sync_mode_buttons)

        # Initial mode
        self._sync_mode_buttons(self.state.display_mode)

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

    def _sync_mode_buttons(self, mode):
        for m, btn in self._mode_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(m == mode)
            btn.blockSignals(False)
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

        cd = self._cycle_data
        mode = self.state.display_mode
        theme = DARK_THEME if self.state.dark_mode else LIGHT_THEME

        # Clear dynamic items
        self._clear_cycle_traces()
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

            for i in range(len(quality)):
                if mode == "Good Cycles" and not quality[i]:
                    continue
                if i == selected:
                    continue  # draw selected last
                pen = pg.mkPen(theme["dataVelocity"], width=1)
                pen.setColor(pg.mkColor(
                    pen.color().red(), pen.color().green(),
                    pen.color().blue(), 50
                ))
                item = self._plot.plot(t, traces[i], pen=pen)
                self._cycle_trace_items.append(item)

            # Draw selected cycle on top
            if 0 <= selected < len(traces):
                show = True
                if mode == "Good Cycles" and not quality[selected]:
                    show = False
                if show:
                    item = self._plot.plot(
                        t, traces[selected],
                        pen=pg.mkPen(theme["dataVelocity"], width=2),
                    )
                    self._cycle_trace_items.append(item)

    def _clear_cycle_traces(self):
        for item in self._cycle_trace_items:
            self._plot.removeItem(item)
        self._cycle_trace_items.clear()

    def retheme(self, theme):
        self._plot.setBackground(theme["bgPlot"])
        self._plot.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
        self._plot.getAxis("left").setPen(pg.mkPen(theme["border"]))
        self._plot.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._plot.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._update_plot()
