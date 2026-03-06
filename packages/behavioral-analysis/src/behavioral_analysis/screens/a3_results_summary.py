"""A3: Results Summary — scatter plot, results table, export."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableView, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor

import pyqtgraph as pg

from ..analysis import stubs
from ..themes import LIGHT_THEME, DARK_THEME


_METRIC_OPTIONS = [
    ("Gain", "gain"),
    ("Eye Amplitude", "eye_amp"),
    ("Eye Phase", "eye_phase"),
    ("Good Cycle Fraction", "_good_frac"),
    ("Variance Residual", "var_residual"),
]

_TABLE_COLUMNS = [
    "#", "Label", "Hz", "Eye Amp", "\u00B1SEM",
    "Phase", "\u00B1SEM", "Stim Amp", "Gain",
    "Good Cyc", "VarRes",
]


class _ResultsTableModel(QAbstractTableModel):
    """Table model for results summary."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []

    def set_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(_TABLE_COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return _TABLE_COLUMNS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None
        row = self._data[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return str(row["block_index"] + 1)
            elif col == 1:
                return row["block_label"]
            elif col == 2:
                return f"{row['freq_hz']:.1f}"
            elif col == 3:
                return f"{row['eye_amp']:.2f}"
            elif col == 4:
                return f"{row['eye_amp_sem']:.3f}"
            elif col == 5:
                return f"{row['eye_phase']:.2f}"
            elif col == 6:
                return f"{row['eye_phase_sem']:.2f}"
            elif col == 7:
                return f"{row['stim_amp']:.1f}"
            elif col == 8:
                return f"{row['gain']:.4f}"
            elif col == 9:
                return f"{row['good_cycles']}/{row['total_cycles']}"
            elif col == 10:
                return f"{row['var_residual']:.4f}"

        elif role == Qt.ForegroundRole and col == 1:
            if row["block_type"] in ("pre", "post"):
                return QColor("#0F8A5F")
            return QColor("#CF2C4A")

        elif role == Qt.TextAlignmentRole and col >= 2:
            return Qt.AlignRight | Qt.AlignVCenter

        return None


class A3Screen(QWidget):
    """Workspace Tab: Results Summary."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._results = None
        self._stale = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(6)

        # ── Y-axis selector ──
        selector_row = QHBoxLayout()
        selector_row.addStretch()
        selector_row.addWidget(QLabel("Metric:"))
        self._metric_combo = QComboBox()
        for label, _ in _METRIC_OPTIONS:
            self._metric_combo.addItem(label)
        self._metric_combo.setFixedWidth(180)
        self._metric_combo.currentIndexChanged.connect(self._update_scatter)
        selector_row.addWidget(self._metric_combo)
        layout.addLayout(selector_row)

        # ── Scatter plot ──
        theme = LIGHT_THEME
        self._scatter_plot = pg.PlotWidget()
        self._scatter_plot.setFixedHeight(175)
        self._scatter_plot.setBackground(theme["bgPlot"])
        self._scatter_plot.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
        self._scatter_plot.getAxis("left").setPen(pg.mkPen(theme["border"]))
        self._scatter_plot.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._scatter_plot.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._scatter_plot.showGrid(x=True, y=True, alpha=0.05)
        self._scatter_plot.setLabel("bottom", "Block #")
        legend = self._scatter_plot.addLegend(offset=(-10, 10))
        legend.setBrush(pg.mkBrush(255, 255, 255, 160))
        legend.setPen(pg.mkPen(theme["border"], width=0.5))

        self._prepost_scatter = pg.ScatterPlotItem(
            size=10, pen=pg.mkPen(None),
            brush=pg.mkBrush(theme["blockPrepost"]),
            name="Pre/Post",
        )
        self._prepost_scatter.sigClicked.connect(self._on_scatter_clicked)
        self._scatter_plot.addItem(self._prepost_scatter)

        self._train_scatter = pg.ScatterPlotItem(
            size=7, pen=pg.mkPen(None),
            brush=pg.mkBrush(
                QColor(theme["blockTrain"]).red(),
                QColor(theme["blockTrain"]).green(),
                QColor(theme["blockTrain"]).blue(),
                140,
            ),
            name="Training",
        )
        self._train_scatter.sigClicked.connect(self._on_scatter_clicked)
        self._scatter_plot.addItem(self._train_scatter)

        layout.addWidget(self._scatter_plot)

        # ── Results table ──
        self._table_model = _ResultsTableModel()
        self._table_view = QTableView()
        self._table_view.setModel(self._table_model)
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table_view.verticalHeader().setVisible(False)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self._table_view.setStyleSheet(
            "QTableView { font-family: 'Consolas','SF Mono','Menlo',monospace; "
            "font-size: 11px; }"
        )
        self._table_view.clicked.connect(self._on_table_clicked)
        layout.addWidget(self._table_view, 1)

        # ── Export bar ──
        export_bar = QFrame()
        export_layout = QHBoxLayout(export_bar)
        export_layout.setContentsMargins(0, 4, 0, 0)
        export_layout.addStretch()

        for label, handler in [
            ("Excel", self._export_excel),
            ("Figures", self._export_figures),
            ("Workspace", self._export_workspace),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(handler)
            export_layout.addWidget(btn)

        export_all_btn = QPushButton("Export All")
        export_all_btn.setProperty("primary", True)
        export_all_btn.clicked.connect(self._export_all)
        export_layout.addWidget(export_all_btn)

        layout.addWidget(export_bar)

        # ── Wire state signals ──
        self.state.parameters_changed.connect(self._mark_stale)
        self.state.session_data_changed.connect(self._mark_stale)
        self.state.workspace_tab_changed.connect(self._on_tab_switch)
        self.state.selected_block_changed.connect(self._highlight_row)

    # ── Lazy computation ──

    def _mark_stale(self, *_):
        self._stale = True

    def _on_tab_switch(self, tab):
        if tab == "A3" and self._stale:
            self._recompute()

    def _recompute(self):
        session = self.state.session_data
        if session is None:
            return

        params = self.state.current_params()
        self._results = stubs.compute_all_results(session, params)
        self._stale = False

        self._table_model.set_data(self._results)
        self._update_scatter()
        self._highlight_row(self.state.selected_block)

    def _update_scatter(self):
        if not self._results:
            return

        metric_idx = self._metric_combo.currentIndex()
        _, metric_key = _METRIC_OPTIONS[metric_idx]

        prepost_x, prepost_y = [], []
        train_x, train_y = [], []

        for r in self._results:
            x = r["block_index"] + 1
            if metric_key == "_good_frac":
                y = r["good_cycles"] / max(r["total_cycles"], 1)
            else:
                y = r[metric_key]

            if r["block_type"] in ("pre", "post"):
                prepost_x.append(x)
                prepost_y.append(y)
            else:
                train_x.append(x)
                train_y.append(y)

        self._prepost_scatter.setData(prepost_x, prepost_y)
        self._train_scatter.setData(train_x, train_y)

        self._scatter_plot.setLabel("left", _METRIC_OPTIONS[metric_idx][0])

    def _on_scatter_clicked(self, _, points):
        if points:
            block_num = int(points[0].pos().x())
            self.state.selected_block = block_num - 1

    def _on_table_clicked(self, index):
        row = index.row()
        if self._results and 0 <= row < len(self._results):
            self.state.selected_block = self._results[row]["block_index"]

    def _highlight_row(self, block_index):
        if self._results:
            for i, r in enumerate(self._results):
                if r["block_index"] == block_index:
                    self._table_view.selectRow(i)
                    break

    # ── Export handlers ──

    def _export_excel(self):
        if self._results:
            stubs.export_excel(self._results, self.state.file_path + "_results.xlsx")

    def _export_figures(self):
        if self._results:
            stubs.export_figures(self._results, self.state.file_path + "_figures.pdf")

    def _export_workspace(self):
        if self._results:
            stubs.export_workspace(self._results, self.state.file_path + "_workspace.mat")

    def _export_all(self):
        self._export_excel()
        self._export_figures()
        self._export_workspace()

    def retheme(self, theme):
        self._scatter_plot.setBackground(theme["bgPlot"])
        self._scatter_plot.getAxis("bottom").setPen(pg.mkPen(theme["border"]))
        self._scatter_plot.getAxis("left").setPen(pg.mkPen(theme["border"]))
        self._scatter_plot.getAxis("bottom").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._scatter_plot.getAxis("left").setTextPen(pg.mkPen(theme["textTertiary"]))
        self._update_scatter()
