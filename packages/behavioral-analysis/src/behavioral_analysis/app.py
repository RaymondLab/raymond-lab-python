"""Main application window for Behavioral Experiment Analysis."""

import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QStatusBar, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from .state import AppState
from .themes import LIGHT_THEME, DARK_THEME, apply_theme
from .screens.w1_load_review import W1Screen
from .screens.w2_metadata_output import W2Screen
from .screens.a1_signal_explorer import A1Screen
from .screens.a2_block_analysis import A2Screen
from .screens.a3_results_summary import A3Screen
from .screens.s1_settings_panel import S1Panel


# Tab labels and state keys
_TAB_INFO = [
    ("Signal Explorer", "A1"),
    ("Block Analysis", "A2"),
    ("Results Summary", "A3"),
]

# Window title fragments
_WIZARD_TITLES = {
    1: "Step 1 of 2: Load & Review",
    2: "Step 2 of 2: Metadata & Output",
}
_WORKSPACE_TITLES = {
    "A1": "Signal Explorer",
    "A2": "Block Analysis",
    "A3": "Results Summary",
}


class MainWindow(QMainWindow):
    """Primary application window containing wizard and workspace phases."""

    def __init__(self):
        super().__init__()
        self.state = AppState(self)

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

        # Wizard page stack
        self._wizard_stack = QStackedWidget()
        self._w1 = W1Screen(self.state)
        self._w2 = W2Screen(self.state)
        self._wizard_stack.addWidget(self._w1)  # index 0
        self._wizard_stack.addWidget(self._w2)  # index 1
        wiz_layout.addWidget(self._wizard_stack, 1)

        # Wizard button bar
        wiz_btn_bar = QFrame()
        wiz_btn_bar.setStyleSheet("padding: 8px;")
        wiz_btn_layout = QHBoxLayout(wiz_btn_bar)
        wiz_btn_layout.setContentsMargins(16, 8, 16, 8)

        self._skip_btn = QPushButton("Skip to Workspace (dev)")
        self._skip_btn.setStyleSheet("color: #8490A0; font-size: 11px;")
        self._skip_btn.clicked.connect(self._skip_to_workspace)
        wiz_btn_layout.addWidget(self._skip_btn)

        wiz_btn_layout.addStretch()

        self._back_btn = QPushButton("Back")
        self._back_btn.clicked.connect(self._wizard_back)
        wiz_btn_layout.addWidget(self._back_btn)

        self._next_btn = QPushButton("Next \u2192")
        self._next_btn.setProperty("primary", True)
        self._next_btn.setEnabled(False)  # disabled until file loaded
        self._next_btn.clicked.connect(self._wizard_next)
        wiz_btn_layout.addWidget(self._next_btn)

        wiz_layout.addWidget(wiz_btn_bar)
        self._phase_stack.addWidget(self._wizard_widget)  # phase index 0

        # ── Workspace phase ──
        self._workspace_widget = QWidget()
        ws_layout = QVBoxLayout(self._workspace_widget)
        ws_layout.setContentsMargins(0, 0, 0, 0)
        ws_layout.setSpacing(0)

        # Workspace toolbar
        self._toolbar = self._build_toolbar()
        ws_layout.addWidget(self._toolbar)

        # Content area: workspace tabs + settings panel side by side
        content_area = QWidget()
        self._content_layout = QHBoxLayout(content_area)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        self._workspace_stack = QStackedWidget()
        self._a1 = A1Screen(self.state)
        self._a2 = A2Screen(self.state)
        self._a3 = A3Screen(self.state)
        self._workspace_stack.addWidget(self._a1)  # index 0
        self._workspace_stack.addWidget(self._a2)  # index 1
        self._workspace_stack.addWidget(self._a3)  # index 2
        self._content_layout.addWidget(self._workspace_stack, 1)

        # Settings panel
        self._s1 = S1Panel(self.state)
        self._s1.setVisible(False)
        self._content_layout.addWidget(self._s1)

        ws_layout.addWidget(content_area, 1)
        self._phase_stack.addWidget(self._workspace_widget)  # phase index 1

        # ── Status bar (workspace only) ──
        self._status_bar = QStatusBar()
        self._status_left = QLabel("M001 · 2026-01-15")
        self._status_left.setStyleSheet(
            "font-weight: bold; color: white; padding: 2px 8px;"
        )
        self._status_type = QLabel("Standard VOR")
        self._status_type.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-family: monospace; "
            "font-size: 11px; padding: 2px 4px;"
        )
        self._status_params = QLabel("LP:40Hz · SG:30ms · Sac:50°/s")
        self._status_params.setStyleSheet(
            "color: rgba(255,255,255,0.85); font-family: monospace; "
            "font-size: 11px; padding: 2px 8px;"
        )
        self._status_session = QLabel("1000Hz · 62 blocks")
        self._status_session.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-family: monospace; "
            "font-size: 11px; padding: 2px 8px;"
        )
        self._status_bar.addWidget(self._status_left)
        self._status_bar.addWidget(self._status_type)
        self._status_bar.addPermanentWidget(self._status_params)
        self._status_bar.addPermanentWidget(self._status_session)
        self.setStatusBar(self._status_bar)
        self._status_bar.setVisible(False)

        # ── Wire state signals ──
        self.state.phase_changed.connect(self._on_phase_changed)
        self.state.wizard_step_changed.connect(self._on_wizard_step_changed)
        self.state.workspace_tab_changed.connect(self._on_workspace_tab_changed)
        self.state.settings_open_changed.connect(self._on_settings_open_changed)
        self.state.dark_mode_changed.connect(self._on_dark_mode_changed)
        self.state.file_loaded_changed.connect(self._on_file_loaded_changed)
        self.state.session_data_changed.connect(self._on_session_data_changed)
        self.state.parameters_changed.connect(self._update_status_params)

        # ── Keyboard shortcuts ──
        QShortcut(QKeySequence("Ctrl+O"), self, self._shortcut_browse)
        QShortcut(QKeySequence(Qt.Key_Left), self, self._shortcut_prev_block)
        QShortcut(QKeySequence(Qt.Key_Right), self, self._shortcut_next_block)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._shortcut_escape)

        # Initialize UI to match default state
        self._sync_wizard_ui()
        self._update_title()

    # ── Toolbar ──

    def _build_toolbar(self):
        toolbar = QFrame()
        toolbar.setObjectName("workspaceToolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # Left: session info placeholders
        self._tb_mouse_id = QLabel("M001")
        self._tb_mouse_id.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self._tb_mouse_id)

        self._tb_date = QLabel("2026-01-15")
        self._tb_date.setStyleSheet(
            "font-family: monospace; font-size: 11px;"
        )
        layout.addWidget(self._tb_date)

        self._tb_type_badge = QLabel("Standard VOR")
        self._tb_type_badge.setStyleSheet(
            "font-size: 10px; font-weight: 600; padding: 2px 8px; "
            "border-radius: 3px; background-color: #E0EDF5; color: #2E5A74;"
        )
        layout.addWidget(self._tb_type_badge)

        layout.addStretch()

        # Right: New Analysis button
        new_analysis_btn = QPushButton("\u21BA New Analysis")
        new_analysis_btn.clicked.connect(self._new_analysis)
        layout.addWidget(new_analysis_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(24)
        layout.addWidget(sep)

        # Tab buttons
        self._tab_buttons = {}
        for label, key in _TAB_INFO:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setProperty("tabKey", key)
            btn.clicked.connect(lambda checked, k=key: self._on_tab_clicked(k))
            self._tab_buttons[key] = btn
            layout.addWidget(btn)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setFixedHeight(24)
        layout.addWidget(sep2)

        # Gear button
        gear_btn = QPushButton("\u2699")
        gear_btn.setFixedWidth(32)
        gear_btn.setStyleSheet("font-size: 16px;")
        gear_btn.clicked.connect(self._toggle_settings)
        layout.addWidget(gear_btn)

        # Set initial tab selection
        self._sync_tab_buttons()

        return toolbar

    # ── Navigation handlers ──

    def _wizard_back(self):
        if self.state.wizard_step > 1:
            self.state.wizard_step = self.state.wizard_step - 1

    def _wizard_next(self):
        if self.state.wizard_step < 2:
            self.state.wizard_step = self.state.wizard_step + 1

    def _skip_to_workspace(self):
        self.state.phase = "workspace"

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
            self.state.reset_workspace()

    def _on_tab_clicked(self, key):
        self.state.workspace_tab = key

    def _toggle_settings(self):
        self.state.settings_open = not self.state.settings_open

    # ── State change handlers ──

    def _on_phase_changed(self, phase):
        if phase == "wizard":
            self._phase_stack.setCurrentIndex(0)
            self._status_bar.setVisible(False)
            self._sync_wizard_ui()
        else:
            self._phase_stack.setCurrentIndex(1)
            self._status_bar.setVisible(True)
            self._apply_status_bar_style()
            self._sync_tab_buttons()
            self._on_workspace_tab_changed(self.state.workspace_tab)
        self._update_title()

    def _on_wizard_step_changed(self, step):
        self._wizard_stack.setCurrentIndex(step - 1)
        self._sync_wizard_ui()
        self._update_title()

    def _on_workspace_tab_changed(self, tab):
        tab_index = {"A1": 0, "A2": 1, "A3": 2}.get(tab, 0)
        self._workspace_stack.setCurrentIndex(tab_index)
        self._sync_tab_buttons()
        self._update_title()

    def _on_settings_open_changed(self, is_open):
        self._s1.setVisible(is_open)

    def _on_dark_mode_changed(self, dark):
        theme = DARK_THEME if dark else LIGHT_THEME
        apply_theme(QApplication.instance(), theme)
        self._apply_status_bar_style()
        self._sync_tab_buttons()

        # Toolbar badge
        self._tb_type_badge.setStyleSheet(
            f"font-size: 10px; font-weight: 600; padding: 2px 8px; "
            f"border-radius: 3px; background-color: {theme['accentLight']}; "
            f"color: {theme['accentText']};"
        )

        # Toolbar background
        self._toolbar.setStyleSheet(
            f"#workspaceToolbar {{ background-color: {theme['bgTopbar']}; }}"
        )

        # Propagate retheme to screens with pyqtgraph plots
        for screen in (self._w1, self._a1, self._a2, self._a3):
            if hasattr(screen, "retheme"):
                screen.retheme(theme)

        # Block navigator theme colors
        nav_colors = {
            "blockPrepost": theme["blockPrepost"],
            "blockTrain": theme["blockTrain"],
            "qualGood": theme["qualGood"],
            "qualWarn": theme["qualWarn"],
            "qualBad": theme["qualBad"],
            "textPrimary": theme["textPrimary"],
        }
        self._a1._block_nav.set_theme(nav_colors)
        self._a2._block_nav.set_theme(nav_colors)

        # Cycle navigator theme
        cycle_colors = {
            "qualGood": theme["qualGood"],
            "qualBad": theme["qualBad"],
            "qualSelected": theme["qualSelected"],
            "textPrimary": theme["textPrimary"],
        }
        self._a2._cycle_nav.set_theme(cycle_colors)

    # ── Keyboard shortcuts ──

    def _shortcut_browse(self):
        if self.state.phase == "wizard" and self.state.wizard_step == 1:
            self._w1._on_browse()

    def _shortcut_prev_block(self):
        if self.state.phase == "workspace":
            idx = self.state.selected_block
            if idx > 0:
                self.state.selected_block = idx - 1

    def _shortcut_next_block(self):
        if self.state.phase == "workspace":
            session = self.state.session_data
            if session:
                max_idx = session["num_blocks"] - 1
                idx = self.state.selected_block
                if idx < max_idx:
                    self.state.selected_block = idx + 1

    def _shortcut_escape(self):
        if self.state.settings_open:
            self.state.settings_open = False

    # ── UI sync helpers ──

    def _on_file_loaded_changed(self, loaded):
        self._next_btn.setEnabled(loaded)

    def _on_session_data_changed(self, session):
        if session is None:
            return
        md = session.get("metadata_defaults", {})
        self._tb_mouse_id.setText(md.get("subject_id", "—"))
        self._tb_date.setText(md.get("session_date", "—"))
        self._tb_type_badge.setText(session.get("analysis_type", "—"))
        self._status_left.setText(
            f"{md.get('subject_id', '—')} \u00B7 {md.get('session_date', '—')}"
        )
        self._status_type.setText(session.get("analysis_type", "—"))
        sr = session.get("sample_rate", "—")
        nb = session.get("num_blocks", "—")
        self._status_session.setText(f"{sr}Hz \u00B7 {nb} blocks")

    def _update_status_params(self):
        s = self.state
        self._status_params.setText(
            f"LP:{s.lp_cutoff_hz:.0f}Hz \u00B7 SG:{s.sg_window_ms:.0f}ms "
            f"\u00B7 Sac:{s.saccade_threshold:.0f}\u00B0/s"
        )

    def _sync_wizard_ui(self):
        step = self.state.wizard_step
        self._back_btn.setVisible(step > 1)
        self._next_btn.setVisible(step < 2)
        self._next_btn.setEnabled(self.state.file_loaded)

    def _sync_tab_buttons(self):
        current = self.state.workspace_tab
        theme = DARK_THEME if self.state.dark_mode else LIGHT_THEME
        for key, btn in self._tab_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(key == current)
            btn.blockSignals(False)
            if key == current:
                btn.setStyleSheet(
                    f"background-color: {theme['bgTabActive']}; "
                    f"color: {theme['textInverse']}; "
                    "font-weight: bold; border-radius: 3px; padding: 4px 12px;"
                )
            else:
                btn.setStyleSheet(
                    f"background-color: {theme['bgTabInactive']}; "
                    f"color: {theme['textOnTopbar']}; "
                    "border-radius: 3px; padding: 4px 12px;"
                )

    def _update_title(self):
        base = "Behavioral Experiment Analysis"
        if self.state.phase == "wizard":
            suffix = _WIZARD_TITLES.get(self.state.wizard_step, "")
            self.setWindowTitle(f"{base} \u2014 {suffix}")
        else:
            suffix = _WORKSPACE_TITLES.get(self.state.workspace_tab, "")
            self.setWindowTitle(f"{base} \u2014 {suffix}")

    def _apply_status_bar_style(self):
        theme = DARK_THEME if self.state.dark_mode else LIGHT_THEME
        self._status_bar.setStyleSheet(
            f"QStatusBar {{ background-color: {theme['accent']}; }}"
        )


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    apply_theme(app, LIGHT_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
