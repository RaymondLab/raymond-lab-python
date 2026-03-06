"""W1: Load & Review — load experiment file, review session/block structure."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QSplitter, QTableView,
    QHeaderView, QFileDialog, QAbstractItemView,
)
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor

import pyqtgraph as pg

from ..analysis import stubs
from ..themes import LIGHT_THEME, DARK_THEME


_ANALYSIS_TYPES = ["Standard VOR", "OKR", "VOR Cancellation", "Custom"]


class W1Screen(QWidget):
    """Wizard Step 1: Load & Review."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._session = None
        self._block_regions = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Control bar ──
        ctrl = QFrame()
        ctrl.setObjectName("w1ControlBar")
        ctrl_layout = QVBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(12, 8, 12, 8)
        ctrl_layout.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self._browse_btn = QPushButton("Browse")
        self._browse_btn.clicked.connect(self._on_browse)
        row1.addWidget(self._browse_btn)

        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText("Select .smr / .smrx / .mat file...")
        row1.addWidget(self._path_edit, 1)

        self._type_combo = QComboBox()
        self._type_combo.setFixedWidth(155)
        self._type_combo.addItems(_ANALYSIS_TYPES)
        self._type_combo.setCurrentText(self.state.analysis_type)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        row1.addWidget(self._type_combo)

        ctrl_layout.addLayout(row1)

        # File metadata row (hidden until loaded)
        self._meta_row = QLabel()
        self._meta_row.setStyleSheet(
            "font-family: 'Consolas','SF Mono','Menlo',monospace; font-size: 11px;"
        )
        self._meta_row.setVisible(False)
        ctrl_layout.addWidget(self._meta_row)

        layout.addWidget(ctrl)

        # ── Session summary bar ──
        self._summary_bar = QFrame()
        self._summary_bar.setObjectName("w1SummaryBar")
        summary_layout = QHBoxLayout(self._summary_bar)
        summary_layout.setContentsMargins(10, 5, 10, 5)
        summary_layout.setSpacing(12)
        self._summary_labels = {}
        for key in ["Duration", "Blocks", "Pre/Post", "Training", "Freq", "Sample Rate"]:
            lbl = QLabel(f"{key}: \u2014")
            lbl.setStyleSheet("font-size: 11px; font-weight: 600;")
            summary_layout.addWidget(lbl)
            self._summary_labels[key] = lbl
        summary_layout.addStretch()
        self._summary_bar.setVisible(False)
        layout.addWidget(self._summary_bar)

        # ── Main area (plots + table) or empty state ──
        self._main_stack = QWidget()
        main_layout = QVBoxLayout(self._main_stack)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Empty state
        self._empty_state = QWidget()
        empty_layout = QVBoxLayout(self._empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        icon_lbl = QLabel("\U0001F4C2")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 32px; opacity: 0.3;")
        empty_layout.addWidget(icon_lbl)
        hint = QLabel("Click <b>Browse</b> to load an experiment file")
        hint.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(hint)

        # Loaded state: splitter with plots and table
        self._loaded_widget = QSplitter(Qt.Horizontal)

        # -- Left: timeline plots --
        plots_widget = QWidget()
        plots_layout = QVBoxLayout(plots_widget)
        plots_layout.setContentsMargins(0, 0, 0, 0)
        plots_layout.setSpacing(3)

        self._plots = []
        theme = LIGHT_THEME

        # Plot 1: Drum velocity (htvel)
        p1_header = self._make_plot_header("HTVEL", "Drum Vel")
        plots_layout.addWidget(p1_header)
        pw1 = self._make_plot_widget(theme)
        self._plot1_curve = pw1.plot(pen=pg.mkPen(theme["textPrimary"], width=1))
        self._plots.append(pw1)
        plots_layout.addWidget(pw1, 1)

        # Plot 2: Chair velocity (hhvel)
        p2_header = self._make_plot_header("HHVEL", "Chair Vel")
        plots_layout.addWidget(p2_header)
        pw2 = self._make_plot_widget(theme)
        self._plot2_curve = pw2.plot(pen=pg.mkPen(theme["textPrimary"], width=1))
        self._plots.append(pw2)
        plots_layout.addWidget(pw2, 1)

        # Plot 3: Raw eye position (hepos1 + hepos2)
        p3_header = QWidget()
        p3h_layout = QHBoxLayout(p3_header)
        p3h_layout.setContentsMargins(0, 2, 0, 0)
        p3h_layout.setSpacing(4)
        sec3 = QLabel("RAW EYE POS \u2014 UNCAL")
        sec3.setStyleSheet("font-size: 10px; font-weight: 700;")
        p3h_layout.addWidget(sec3)
        h1_lbl = QLabel("\u2501 h1")
        h1_lbl.setStyleSheet(f"font-size: 9px; font-weight: 700; color: {theme['dataPosition']};")
        p3h_layout.addWidget(h1_lbl)
        h2_lbl = QLabel("\u2501 h2")
        h2_lbl.setStyleSheet(f"font-size: 9px; font-weight: 700; color: {theme['dataVelocity']};")
        p3h_layout.addWidget(h2_lbl)
        p3h_layout.addStretch()
        plots_layout.addWidget(p3_header)

        pw3 = self._make_plot_widget(theme)
        self._plot3_curve1 = pw3.plot(
            pen=pg.mkPen(theme["dataPosition"], width=1), name="hepos1"
        )
        self._plot3_curve2 = pw3.plot(
            pen=pg.mkPen(theme["dataVelocity"], width=1), name="hepos2"
        )
        self._plots.append(pw3)
        plots_layout.addWidget(pw3, 1)

        # Link x-axes
        pw2.setXLink(pw1)
        pw3.setXLink(pw1)

        self._loaded_widget.addWidget(plots_widget)

        # -- Right: block table --
        self._block_table = QTableView()
        self._block_table.setFixedWidth(195)
        self._block_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._block_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._block_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._block_table.verticalHeader().setVisible(False)
        self._block_table.horizontalHeader().setStretchLastSection(True)
        self._block_table.clicked.connect(self._on_table_row_clicked)

        self._table_model = QStandardItemModel()
        self._table_model.setHorizontalHeaderLabels(["#", "Label", "Hz", "\u2713"])
        self._block_table.setModel(self._table_model)
        self._block_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self._block_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self._block_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        self._block_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents
        )

        self._loaded_widget.addWidget(self._block_table)
        self._loaded_widget.setVisible(False)

        main_layout.addWidget(self._empty_state)
        main_layout.addWidget(self._loaded_widget)

        layout.addWidget(self._main_stack, 1)

    # ── Helpers ──

    def _make_plot_header(self, channel, description):
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 2, 0, 0)
        h_layout.setSpacing(4)
        sec = QLabel("CH:")
        sec.setStyleSheet("font-size: 10px; font-weight: 700;")
        h_layout.addWidget(sec)
        combo = QComboBox()
        combo.setFixedWidth(80)
        combo.addItems(["HTVEL", "HHVEL", "htpos", "hhpos"])
        combo.setCurrentText(channel)
        h_layout.addWidget(combo)
        desc = QLabel(description)
        desc.setStyleSheet("font-size: 9px;")
        h_layout.addWidget(desc)
        h_layout.addStretch()
        return header

    def _make_plot_widget(self, theme):
        pw = pg.PlotWidget()
        pw.setBackground(theme["bgPlot"])
        pw.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
        pw.getAxis("left").setPen(pg.mkPen(theme["border"]))
        pw.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
        pw.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))
        pw.showGrid(x=True, y=True, alpha=0.1)
        pw.setMouseEnabled(x=True, y=False)
        return pw

    # ── Actions ──

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Experiment File",
            "",
            "Spike2 Files (*.smr *.smrx);;MATLAB Files (*.mat);;All Files (*)",
        )
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path):
        """Load file at path (used by browse and programmatic loads)."""
        self._path_edit.setText(path)
        self.state.file_path = path

        self._session = stubs.load_experiment_file(path)
        self.state.session_data = self._session
        self.state.file_loaded = True
        self.state.analysis_type = self._type_combo.currentText()

        self._populate_ui()

    def _on_type_changed(self, text):
        self.state.analysis_type = text

    def _populate_ui(self):
        session = self._session
        if session is None:
            return

        theme = DARK_THEME if self.state.dark_mode else LIGHT_THEME

        # File metadata row
        fi = session["file_info"]
        self._meta_row.setText(
            f"Ch {fi['num_channels']}    "
            f"Size {fi['file_size_mb']} MB    "
            f"Date {fi['file_date']}    "
            f"Fmt {fi['file_format']}"
        )
        self._meta_row.setVisible(True)

        # Session summary
        blocks = session["blocks"]
        pre_post = sum(1 for b in blocks if b["type"] in ("pre", "post"))
        training = sum(1 for b in blocks if b["type"] == "train")
        self._summary_labels["Duration"].setText(
            f"Duration: {session['duration']:.0f}s"
        )
        self._summary_labels["Blocks"].setText(
            f"Blocks: {session['num_blocks']}"
        )
        self._summary_labels["Pre/Post"].setText(f"Pre/Post: {pre_post}")
        self._summary_labels["Pre/Post"].setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {theme['blockPrepost']};"
        )
        self._summary_labels["Training"].setText(f"Training: {training}")
        self._summary_labels["Training"].setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {theme['blockTrain']};"
        )
        self._summary_labels["Freq"].setText(
            f"Freq: {blocks[0]['freq_hz']} Hz"
        )
        self._summary_labels["Sample Rate"].setText(
            f"Rate: {session['sample_rate']} Hz"
        )
        self._summary_bar.setVisible(True)

        # Switch to loaded state
        self._empty_state.setVisible(False)
        self._loaded_widget.setVisible(True)

        # Timeline plots
        tl = session["timelines"]
        t = tl["time"]
        self._plot1_curve.setData(t, tl["HTVEL"])
        self._plot2_curve.setData(t, tl["HHVEL"])
        self._plot3_curve1.setData(t, tl["hepos1"])
        self._plot3_curve2.setData(t, tl["hepos2"])

        # Block region overlays
        self._clear_block_regions()
        for block in blocks:
            for pw in self._plots:
                color = theme["blockPrepost"] if block["type"] in ("pre", "post") else theme["blockTrain"]
                qc = QColor(color)
                region = pg.LinearRegionItem(
                    values=[block["start_time"], block["end_time"]],
                    movable=False,
                    brush=pg.mkBrush(qc.red(), qc.green(), qc.blue(), 35),
                )
                region.setZValue(-10)
                pw.addItem(region)
                self._block_regions.append((pw, region))

        # Block table
        self._table_model.removeRows(0, self._table_model.rowCount())
        for block in blocks:
            row_items = [
                QStandardItem(str(block["index"] + 1)),
                QStandardItem(block["label"]),
                QStandardItem(str(block["freq_hz"])),
                QStandardItem("\u2611"),
            ]
            if block["type"] in ("pre", "post"):
                row_items[1].setForeground(QColor(theme["blockPrepost"]))
            else:
                row_items[1].setForeground(QColor(theme["blockTrain"]))
            self._table_model.appendRow(row_items)

    def _clear_block_regions(self):
        for pw, region in self._block_regions:
            pw.removeItem(region)
        self._block_regions.clear()

    def _on_table_row_clicked(self, index: QModelIndex):
        row = index.row()
        if self._session is None:
            return
        blocks = self._session["blocks"]
        if 0 <= row < len(blocks):
            block = blocks[row]
            center = (block["start_time"] + block["end_time"]) / 2
            span = block["end_time"] - block["start_time"]
            padding = span * 0.5
            for pw in self._plots:
                pw.setXRange(
                    block["start_time"] - padding,
                    block["end_time"] + padding,
                    padding=0,
                )
            self.state.selected_block = row

    def retheme(self, theme):
        """Update plot styling when theme changes."""
        for pw in self._plots:
            pw.setBackground(theme["bgPlot"])
            pw.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
            pw.getAxis("left").setPen(pg.mkPen(theme["border"]))
            pw.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
            pw.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))
        if self._session:
            self._populate_ui()
