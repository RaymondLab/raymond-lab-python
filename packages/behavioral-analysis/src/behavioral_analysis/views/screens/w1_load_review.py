"""W1: Load & Review — load experiment file, review session/block structure."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QSplitter, QTableView,
    QHeaderView, QFileDialog, QAbstractItemView, QStyledItemDelegate,
)
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor

import pyqtgraph as pg

from ...themes import THEME

_ANALYSIS_TYPES = ["Standard VOR", "OKR", "VOR Cancellation", "Custom"]

_CHANNEL_LABELS = {
    "HTVEL": "Drum Command Velocity",
    "HHVEL": "Chair Command Velocity",
    "htvel": "Drum Feedback Velocity",
    "hhvel": "Chair Feedback Velocity",
    "htpos": "Drum Command Position",
    "hhpos": "Chair Command Position",
    "hepos1": "Eye Position Ch1",
    "hepos2": "Eye Position Ch2",
}


class _LabelDelegate(QStyledItemDelegate):
    """Delegate that makes block label cells editable."""

    def createEditor(self, parent, option, index):
        if index.column() == 1:
            return super().createEditor(parent, option, index)
        return None


class W1Screen(QWidget):
    """Wizard Step 1: Load & Review."""

    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Control bar ──
        ctrl = QFrame()
        ctrl.setObjectName("w1ControlBar")
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(12, 10, 12, 10)
        ctrl_layout.setSpacing(10)

        _lbl_style = (
            f"font-size: {THEME['fontXs']}; font-weight: 700; "
            f"letter-spacing: 0.04em; color: {THEME['textOnTopbar']};"
        )

        # Browse button
        self._browse_btn = QPushButton("Browse")
        self._browse_btn.setFixedHeight(42)
        self._browse_btn.clicked.connect(self._on_browse)
        ctrl_layout.addWidget(self._browse_btn)

        # Experiment File column
        file_col = QVBoxLayout()
        file_col.setSpacing(2)
        self._file_label = QLabel("EXPERIMENT FILE")
        self._file_label.setStyleSheet(_lbl_style)
        file_col.addWidget(self._file_label)
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText("Select .smr / .smrx / .mat file...")
        file_col.addWidget(self._path_edit)
        ctrl_layout.addLayout(file_col, 1)

        # Analysis Type column
        type_col = QVBoxLayout()
        type_col.setSpacing(2)
        type_label = QLabel("ANALYSIS TYPE")
        type_label.setStyleSheet(_lbl_style)
        type_col.addWidget(type_label)
        self._type_combo = QComboBox()
        self._type_combo.setFixedWidth(155)
        self._type_combo.setStyleSheet(
            f"QComboBox {{ background-color: {THEME['bgInput']}; "
            f"border: 1px solid {THEME['border']}; "
            f"color: {THEME['textPrimary']}; }}"
        )
        self._type_combo.addItems(_ANALYSIS_TYPES)
        self._type_combo.currentTextChanged.connect(
            lambda v: self.vm.set_analysis_type(v)
        )
        type_col.addWidget(self._type_combo)
        ctrl_layout.addLayout(type_col)

        # Next button
        self._next_btn = QPushButton("Next \u2192")
        self._next_btn.setProperty("primary", True)
        self._next_btn.setFixedHeight(42)
        self._next_btn.setEnabled(False)
        self._next_btn.clicked.connect(lambda: self.vm.go_to_wizard_step(2))
        ctrl_layout.addWidget(self._next_btn)

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
            lbl.setStyleSheet(f"font-size: {THEME['fontSm']}; font-weight: 600;")
            summary_layout.addWidget(lbl)
            self._summary_labels[key] = lbl
        summary_layout.addStretch()
        self._summary_bar.setVisible(False)
        layout.addWidget(self._summary_bar)

        # ── Main area ──
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

        # Plot 1: Drum velocity
        p1_header = self._make_plot_header("HTVEL")
        plots_layout.addWidget(p1_header)
        pw1 = self._make_plot_widget()
        self._plot1_curve = pw1.plot(pen=pg.mkPen(THEME["textPrimary"], width=1))
        self._plots.append(pw1)
        plots_layout.addWidget(pw1, 1)

        # Plot 2: Chair velocity
        p2_header = self._make_plot_header("HHVEL")
        plots_layout.addWidget(p2_header)
        pw2 = self._make_plot_widget()
        self._plot2_curve = pw2.plot(pen=pg.mkPen(THEME["textPrimary"], width=1))
        self._plots.append(pw2)
        plots_layout.addWidget(pw2, 1)

        # Plot 3: Raw eye position
        p3_header = QWidget()
        p3h_layout = QHBoxLayout(p3_header)
        p3h_layout.setContentsMargins(0, 2, 0, 0)
        p3h_layout.setSpacing(4)
        sec3 = QLabel("RAW EYE POS \u2014 UNCAL")
        sec3.setStyleSheet(f"font-size: {THEME['fontXs']}; font-weight: 700;")
        p3h_layout.addWidget(sec3)
        h1_lbl = QLabel("\u2501 h1")
        h1_lbl.setStyleSheet(
            f"font-size: {THEME['fontXs']}; font-weight: 700; "
            f"color: {THEME['dataPosition']};"
        )
        p3h_layout.addWidget(h1_lbl)
        h2_lbl = QLabel("\u2501 h2")
        h2_lbl.setStyleSheet(
            f"font-size: {THEME['fontXs']}; font-weight: 700; "
            f"color: {THEME['dataVelocity']};"
        )
        p3h_layout.addWidget(h2_lbl)
        p3h_layout.addStretch()
        plots_layout.addWidget(p3_header)

        pw3 = self._make_plot_widget()
        pw3.setLabel("bottom", "Time (s)")
        self._plot3_curve1 = pw3.plot(
            pen=pg.mkPen(THEME["dataPosition"], width=1), name="hepos1"
        )
        self._plot3_curve2 = pw3.plot(
            pen=pg.mkPen(THEME["dataVelocity"], width=1), name="hepos2"
        )
        self._plots.append(pw3)
        plots_layout.addWidget(pw3, 1)

        pw2.setXLink(pw1)
        pw3.setXLink(pw1)

        self._loaded_widget.addWidget(plots_widget)

        # -- Right: block table --
        self._block_table = QTableView()
        self._block_table.setFixedWidth(170)
        self._block_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._block_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._block_table.verticalHeader().setVisible(False)
        self._block_table.horizontalHeader().setStretchLastSection(True)
        self._block_table.clicked.connect(self._on_table_row_clicked)

        self._label_delegate = _LabelDelegate(self._block_table)
        self._block_table.setItemDelegateForColumn(1, self._label_delegate)

        self._table_model = QStandardItemModel()
        self._table_model.setHorizontalHeaderLabels(["#", "Label", "Hz"])
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

        self._table_model.dataChanged.connect(self._on_label_edited)

        self._loaded_widget.addWidget(self._block_table)
        self._loaded_widget.setVisible(False)

        main_layout.addWidget(self._empty_state)
        main_layout.addWidget(self._loaded_widget)

        layout.addWidget(self._main_stack, 1)

        # Block region overlays
        self._block_regions = []

        # ── Wire VM signals ──
        self.vm.file_loaded.connect(self._on_file_loaded)
        self.vm.session_info_changed.connect(self._populate_ui)

    # ── Helpers ──

    def _make_plot_header(self, channel):
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 2, 0, 0)
        h_layout.setSpacing(6)
        sec = QLabel("CH:")
        sec.setStyleSheet(f"font-size: {THEME['fontXs']}; font-weight: 700;")
        h_layout.addWidget(sec)
        combo = QComboBox()
        combo.setFixedWidth(80)
        combo.addItems(["HTVEL", "HHVEL", "htvel", "hhvel", "htpos", "hhpos"])
        combo.setCurrentText(channel)
        combo.view().setMinimumWidth(180)
        h_layout.addWidget(combo)
        desc = QLabel(_CHANNEL_LABELS.get(channel, channel))
        desc.setStyleSheet(
            f"font-size: {THEME['fontSm']}; color: {THEME['textSecondary']};"
        )
        combo.currentTextChanged.connect(
            lambda ch, d=desc: d.setText(_CHANNEL_LABELS.get(ch, ch))
        )
        h_layout.addWidget(desc)
        h_layout.addStretch()
        return header

    def _make_plot_widget(self):
        pw = pg.PlotWidget()
        pw.setBackground(THEME["bgPlot"])
        pw.getAxis("bottom").setPen(pg.mkPen(THEME["border"]))
        pw.getAxis("left").setPen(pg.mkPen(THEME["border"]))
        pw.getAxis("bottom").setTextPen(pg.mkPen(THEME["textTertiary"]))
        pw.getAxis("left").setTextPen(pg.mkPen(THEME["textTertiary"]))
        pw.showGrid(x=True, y=True, alpha=0.1)
        pw.setMouseEnabled(x=True, y=False)
        pw.setClipToView(True)
        pw.setDownsampling(mode="peak")
        return pw

    def trigger_browse(self):
        """Public method for keyboard shortcut."""
        self._on_browse()

    # ── Actions ──

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Experiment File",
            "",
            "Spike2 Files (*.smr *.smrx);;MATLAB Files (*.mat);;All Files (*)",
        )
        if path:
            self.vm.load_file(path)

    def _on_file_loaded(self):
        self._path_edit.setText(self.vm.data.file_path)
        self._next_btn.setEnabled(True)

    def _populate_ui(self):
        data = self.vm.data
        if not data.is_loaded:
            return

        session = data.raw

        # File metadata — append to the "EXPERIMENT FILE" label
        fi = session["file_info"]
        info = (
            f"Ch {fi['num_channels']}  \u00B7  "
            f"{fi['file_size_mb']} MB  \u00B7  "
            f"{fi['file_date']}  \u00B7  "
            f"{fi['file_format']}"
        )
        self._file_label.setText(f"EXPERIMENT FILE \u2014 {info}")

        # Session summary
        blocks = data.blocks
        pre_post = sum(1 for b in blocks if b.block_type in ("pre", "post"))
        training = sum(1 for b in blocks if b.block_type == "train")
        self._summary_labels["Duration"].setText(
            f"Duration: {data.duration:.0f}s"
        )
        self._summary_labels["Blocks"].setText(f"Blocks: {data.num_blocks}")
        self._summary_labels["Pre/Post"].setText(f"Pre/Post: {pre_post}")
        self._summary_labels["Pre/Post"].setStyleSheet(
            f"font-size: {THEME['fontSm']}; font-weight: 600; "
            f"color: {THEME['blockPrepost']};"
        )
        self._summary_labels["Training"].setText(f"Training: {training}")
        self._summary_labels["Training"].setStyleSheet(
            f"font-size: {THEME['fontSm']}; font-weight: 600; "
            f"color: {THEME['blockTrain']};"
        )
        self._summary_labels["Freq"].setText(
            f"Freq: {blocks[0].freq_hz} Hz" if blocks else "Freq: \u2014"
        )
        self._summary_labels["Sample Rate"].setText(
            f"Rate: {data.sample_rate} Hz"
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
            color = THEME["blockPrepost"] if block.block_type in ("pre", "post") else THEME["blockTrain"]
            qc = QColor(color)
            for pw in self._plots:
                region = pg.LinearRegionItem(
                    values=[block.start_time, block.end_time],
                    movable=False,
                    brush=pg.mkBrush(qc.red(), qc.green(), qc.blue(), 35),
                )
                region.setZValue(-10)
                pw.addItem(region)
                self._block_regions.append((pw, region))

        # Block table
        self._table_model.removeRows(0, self._table_model.rowCount())
        for block in blocks:
            num_item = QStandardItem(str(block.index + 1))
            num_item.setEditable(False)
            label_item = QStandardItem(block.label)
            label_item.setEditable(True)
            hz_item = QStandardItem(str(block.freq_hz))
            hz_item.setEditable(False)

            if block.block_type in ("pre", "post"):
                label_item.setForeground(QColor(THEME["blockPrepost"]))
            else:
                label_item.setForeground(QColor(THEME["blockTrain"]))

            self._table_model.appendRow([num_item, label_item, hz_item])

    def _clear_block_regions(self):
        for pw, region in self._block_regions:
            pw.removeItem(region)
        self._block_regions.clear()

    def _on_table_row_clicked(self, index: QModelIndex):
        row = index.row()
        blocks = self.vm.blocks
        if 0 <= row < len(blocks):
            block = blocks[row]
            padding = (block.end_time - block.start_time) * 0.5
            for pw in self._plots:
                pw.setXRange(
                    block.start_time - padding,
                    block.end_time + padding,
                    padding=0,
                )
            self.vm.select_block(row)

    def _on_label_edited(self, top_left, bottom_right, roles):
        if top_left.column() == 1:
            row = top_left.row()
            new_label = self._table_model.data(top_left, Qt.DisplayRole)
            if new_label:
                self.vm.update_block_label(row, new_label)
