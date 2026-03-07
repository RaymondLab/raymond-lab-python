"""Main application window for Behavioral Experiment Analysis."""

import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from ..themes import THEME, apply_theme
from ..viewmodels.analysis_viewmodel import AnalysisViewModel
from .screens.w1_load_review import W1Screen
from .screens.w2_metadata_output import W2Screen
from .screens.w3_signal_explorer import W3Screen
from .screens.a1_block_analysis import A1Screen
from .screens.a2_results_summary import A2Screen
from .widgets.segmented_control import SegmentedControl
from .widgets.badge import Badge


_TAB_INFO = [
    ("Block Analysis", "A1"),
    ("Results Summary", "A2"),
]

_WIZARD_TITLES = {
    1: "Step 1 of 3: Load & Review",
    2: "Step 2 of 3: Metadata & Output",
    3: "Step 3 of 3: Signal Explorer",
}
_WORKSPACE_TITLES = {
    "A1": "Block Analysis",
    "A2": "Results Summary",
}


class AnalysisWindow(QMainWindow):
    """Primary application window containing wizard and workspace phases."""

    def __init__(self):
        super().__init__()
        self.vm = AnalysisViewModel(self)

        self.setWindowTitle("Behavioral Experiment Analysis")
        self.resize(1280, 800)
        self.setMinimumSize(1024, 600)

        # ── Central stacked widget: page 0 = wizard, page 1 = workspace ──
        self._phase_stack = QStackedWidget()
        self.setCentralWidget(self._phase_stack)

        # ── Wizard phase ──
        self._wizard_widget = QWidget()
        wiz_layout = QVBoxLayout(self._wizard_widget)
        wiz_layout.setContentsMargins(0, 0, 0, 0)
        wiz_layout.setSpacing(0)

        self._wizard_stack = QStackedWidget()
        self._w1 = W1Screen(self.vm)
        self._w2 = W2Screen(self.vm)
        self._w3 = W3Screen(self.vm)
        self._wizard_stack.addWidget(self._w1)   # index 0
        self._wizard_stack.addWidget(self._w2)   # index 1
        self._wizard_stack.addWidget(self._w3)   # index 2
        wiz_layout.addWidget(self._wizard_stack, 1)

        self._phase_stack.addWidget(self._wizard_widget)  # phase index 0

        # ── Workspace phase ──
        self._workspace_widget = QWidget()
        ws_layout = QVBoxLayout(self._workspace_widget)
        ws_layout.setContentsMargins(0, 0, 0, 0)
        ws_layout.setSpacing(0)

        # Workspace toolbar
        self._toolbar = self._build_toolbar()
        ws_layout.addWidget(self._toolbar)

        # Workspace content
        self._workspace_stack = QStackedWidget()
        self._a1 = A1Screen(self.vm)
        self._a2 = A2Screen(self.vm)
        self._workspace_stack.addWidget(self._a1)  # index 0
        self._workspace_stack.addWidget(self._a2)  # index 1
        ws_layout.addWidget(self._workspace_stack, 1)

        # ── Status bar ──
        self._status_bar = QFrame()
        self._status_bar.setFixedHeight(24)
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(12, 0, 12, 0)
        status_layout.setSpacing(16)

        self._status_left = QLabel("\u2014")
        self._status_type = QLabel("\u2014")
        self._status_session = QLabel("\u2014")

        status_layout.addWidget(self._status_left)
        status_layout.addWidget(self._status_type)
        status_layout.addStretch()
        status_layout.addWidget(self._status_session)

        self._status_bar.setVisible(False)
        ws_layout.addWidget(self._status_bar)

        self._phase_stack.addWidget(self._workspace_widget)  # phase index 1

        # ── Wire VM signals ──
        self.vm.phase_changed.connect(self._on_phase_changed)
        self.vm.wizard_step_changed.connect(self._on_wizard_step_changed)
        self.vm.workspace_tab_changed.connect(self._on_workspace_tab_changed)
        self.vm.session_info_changed.connect(self._update_session_info)
        self.vm.message_requested.connect(
            lambda t, m: QMessageBox.information(self, t, m)
        )

        # ── Keyboard shortcuts ──
        QShortcut(QKeySequence("Ctrl+O"), self, self._shortcut_browse)
        QShortcut(QKeySequence(Qt.Key_Left), self, self._shortcut_prev_block)
        QShortcut(QKeySequence(Qt.Key_Right), self, self._shortcut_next_block)

        # Initialize
        self._update_title()
        self._apply_toolbar_styles()

    # ── Toolbar ──

    def _build_toolbar(self):
        toolbar = QFrame()
        toolbar.setObjectName("workspaceToolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        self._tb_mouse_id = QLabel("\u2014")
        layout.addWidget(self._tb_mouse_id)

        self._tb_date = QLabel("\u2014")
        layout.addWidget(self._tb_date)

        self._tb_type_badge = Badge("Standard VOR", variant="accent")
        layout.addWidget(self._tb_type_badge)

        layout.addStretch()

        self._back_to_w3_btn = QPushButton("\u2190 Back to Signal Explorer")
        self._back_to_w3_btn.setObjectName("toolbarGhostBtn")
        self._back_to_w3_btn.clicked.connect(self._back_to_signal_explorer)
        layout.addWidget(self._back_to_w3_btn)

        self._new_analysis_btn = QPushButton("\u21BA New Analysis")
        self._new_analysis_btn.setObjectName("toolbarGhostBtn")
        self._new_analysis_btn.clicked.connect(self._new_analysis)
        layout.addWidget(self._new_analysis_btn)

        self._tab_control = SegmentedControl(
            [(label, key) for label, key in _TAB_INFO]
        )
        self._tab_control.selection_changed.connect(
            lambda key: self.vm.switch_tab(key)
        )
        layout.addWidget(self._tab_control)

        return toolbar

    # ── Navigation handlers ──

    def _back_to_signal_explorer(self):
        self.vm.return_to_signal_explorer()

    def _new_analysis(self):
        reply = QMessageBox.question(
            self,
            "New Analysis",
            "Return to the setup wizard?\n\n"
            "This will reset all workspace state.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.vm.new_analysis()

    # ── State change handlers ──

    def _on_phase_changed(self, phase):
        if phase == "wizard":
            self._phase_stack.setCurrentIndex(0)
            self._status_bar.setVisible(False)
        else:
            self._phase_stack.setCurrentIndex(1)
            self._status_bar.setVisible(True)
            self._tab_control.set_selected(self.vm.workspace_tab)
            self._on_workspace_tab_changed(self.vm.workspace_tab)
        self._update_title()

    def _on_wizard_step_changed(self, step):
        self._wizard_stack.setCurrentIndex(step - 1)
        self._update_title()

    def _on_workspace_tab_changed(self, tab):
        tab_index = {"A1": 0, "A2": 1}.get(tab, 0)
        self._workspace_stack.setCurrentIndex(tab_index)
        self._tab_control.set_selected(tab)
        self._update_title()

    # ── Keyboard shortcuts ──

    def _shortcut_browse(self):
        if self.vm.phase == "wizard" and self.vm.wizard_step == 1:
            self._w1.trigger_browse()

    def _shortcut_prev_block(self):
        if self.vm.phase == "workspace":
            idx = self.vm.selected_block
            if idx > 0:
                self.vm.select_block(idx - 1)

    def _shortcut_next_block(self):
        if self.vm.phase == "workspace" and self.vm.is_file_loaded:
            max_idx = self.vm.data.num_blocks - 1
            idx = self.vm.selected_block
            if idx < max_idx:
                self.vm.select_block(idx + 1)

    # ── UI sync helpers ──

    def _update_session_info(self):
        data = self.vm.data
        if not data.is_loaded:
            return
        md = data.raw.get("metadata_defaults", {})
        dash = "\u2014"
        subject = md.get("subject_id", dash)
        date = md.get("session_date", dash)
        atype = data.raw.get("analysis_type", dash)
        self._tb_mouse_id.setText(subject)
        self._tb_date.setText(date)
        self._tb_type_badge.setText(atype)
        self._status_left.setText(f"{subject} \u00B7 {date}")
        self._status_type.setText(atype)
        sr = data.raw.get("sample_rate", dash)
        nb = data.raw.get("num_blocks", dash)
        self._status_session.setText(f"{sr}Hz \u00B7 {nb} blocks")

    def _update_title(self):
        base = "Behavioral Experiment Analysis"
        if self.vm.phase == "wizard":
            suffix = _WIZARD_TITLES.get(self.vm.wizard_step, "")
            self.setWindowTitle(f"{base} \u2014 {suffix}")
        else:
            suffix = _WORKSPACE_TITLES.get(self.vm.workspace_tab, "")
            self.setWindowTitle(f"{base} \u2014 {suffix}")

    def _apply_toolbar_styles(self):
        t = THEME
        self._toolbar.setStyleSheet(
            f"#workspaceToolbar {{ background-color: {t['bgTopbar']}; "
            f"border-bottom: 1px solid {t['border']}; }}"
        )
        self._tb_mouse_id.setStyleSheet(
            f"font-weight: bold; font-size: {t['fontLg']}; "
            f"color: {t['textInverse']};"
        )
        self._tb_date.setStyleSheet(
            f"font-family: {t['fontMono']}; "
            f"font-size: {t['fontSm']}; color: {t['textOnTopbar']};"
        )
        ghost_btn_style = (
            f"QPushButton {{ background: transparent; border: none; "
            f"color: {t['textOnTopbar']}; font-size: {t['fontSm']}; "
            f"padding: 4px 10px; }}"
            f"QPushButton:hover {{ color: {t['textInverse']}; }}"
        )
        self._back_to_w3_btn.setStyleSheet(ghost_btn_style)
        self._new_analysis_btn.setStyleSheet(ghost_btn_style)
        self._tab_control.set_theme(
            active_bg=t["bgTabActive"],
            active_fg=t["textInverse"],
            inactive_bg=t["bgTabInactive"],
            inactive_fg=t["textOnTopbar"],
            border=t["border"],
        )
        self._status_bar.setStyleSheet(
            f"background-color: {t['accentDark']};"
        )
        self._status_left.setStyleSheet(
            f"font-weight: 600; font-size: {t['fontSm']}; "
            f"color: {t['textInverse']};"
        )
        self._status_type.setStyleSheet(
            f"font-size: {t['fontSm']}; font-family: {t['fontMono']}; "
            f"color: rgba(255,255,255,0.7);"
        )
        self._status_session.setStyleSheet(
            f"font-size: {t['fontSm']}; font-family: {t['fontMono']}; "
            f"color: rgba(255,255,255,0.5);"
        )


def main():
    """Application entry point."""
    import pyqtgraph as pg_module
    pg_module.setConfigOptions(antialias=False, useOpenGL=False)

    app = QApplication(sys.argv)
    apply_theme(app)

    window = AnalysisWindow()
    window.show()

    sys.exit(app.exec())
