"""Main application window for Behavioral Experiment Analysis."""

import sys

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFrame,
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
from .widgets.segmented_control import SegmentedControl
from .widgets.badge import Badge


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

        # ── Status bar (custom QFrame for precise layout control) ──
        self._status_bar = QFrame()
        self._status_bar.setFixedHeight(24)
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(12, 0, 12, 0)
        status_layout.setSpacing(16)

        self._status_left = QLabel("M001 \u00B7 2026-01-15")
        self._status_type = QLabel("Standard VOR")
        self._status_params = QLabel("LP:40Hz \u00B7 SG:30ms \u00B7 Sac:50\u00B0/s")
        self._status_session = QLabel("1000Hz \u00B7 62 blocks")

        status_layout.addWidget(self._status_left)
        status_layout.addWidget(self._status_type)
        status_layout.addStretch()
        status_layout.addWidget(self._status_params)
        status_layout.addWidget(self._status_session)

        self._status_bar.setVisible(False)
        ws_layout.addWidget(self._status_bar)

        self._phase_stack.addWidget(self._workspace_widget)  # phase index 1

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
        self._update_title()
        self._apply_theme_styles(LIGHT_THEME)

    # ── Toolbar ──

    def _build_toolbar(self):
        toolbar = QFrame()
        toolbar.setObjectName("workspaceToolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Left: session info
        self._tb_mouse_id = QLabel("M001")
        layout.addWidget(self._tb_mouse_id)

        self._tb_date = QLabel("2026-01-15")
        layout.addWidget(self._tb_date)

        self._tb_type_badge = Badge("Standard VOR", variant="accent")
        layout.addWidget(self._tb_type_badge)

        layout.addStretch()

        # Right: New Analysis button (ghost style)
        self._new_analysis_btn = QPushButton("\u21BA New Analysis")
        self._new_analysis_btn.setObjectName("toolbarGhostBtn")
        self._new_analysis_btn.clicked.connect(self._new_analysis)
        layout.addWidget(self._new_analysis_btn)

        # Tab segmented control
        self._tab_control = SegmentedControl(
            [(label, key) for label, key in _TAB_INFO]
        )
        self._tab_control.selection_changed.connect(self._on_tab_clicked)
        layout.addWidget(self._tab_control)

        # Gear button
        self._gear_btn = QPushButton("\u2699")
        self._gear_btn.setObjectName("gearBtn")
        self._gear_btn.setFixedSize(30, 30)
        self._gear_btn.clicked.connect(self._toggle_settings)
        layout.addWidget(self._gear_btn)

        return toolbar

    # ── Navigation handlers ──

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
        else:
            self._phase_stack.setCurrentIndex(1)
            self._status_bar.setVisible(True)
            self._tab_control.set_selected(self.state.workspace_tab)
            self._on_workspace_tab_changed(self.state.workspace_tab)
        self._update_title()
        theme = DARK_THEME if self.state.dark_mode else LIGHT_THEME
        self._apply_theme_styles(theme)

    def _on_wizard_step_changed(self, step):
        self._wizard_stack.setCurrentIndex(step - 1)
        self._update_title()

    def _on_workspace_tab_changed(self, tab):
        tab_index = {"A1": 0, "A2": 1, "A3": 2}.get(tab, 0)
        self._workspace_stack.setCurrentIndex(tab_index)
        self._tab_control.set_selected(tab)
        self._update_title()

    def _on_settings_open_changed(self, is_open):
        self._s1.setMaximumWidth(16777215 if is_open else 265)
        self._s1.setVisible(is_open)
        self._update_gear_style()

    def _on_dark_mode_changed(self, dark):
        theme = DARK_THEME if dark else LIGHT_THEME

        # Suppress repaints during bulk style changes
        self.setUpdatesEnabled(False)

        apply_theme(QApplication.instance(), theme)
        self._apply_theme_styles(theme)

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

        self.setUpdatesEnabled(True)

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
        self._w1.update_next_enabled(loaded)

    def _on_session_data_changed(self, session):
        if session is None:
            return
        dash = "\u2014"
        md = session.get("metadata_defaults", {})
        subject = md.get("subject_id", dash)
        date = md.get("session_date", dash)
        atype = session.get("analysis_type", dash)
        self._tb_mouse_id.setText(subject)
        self._tb_date.setText(date)
        self._tb_type_badge.setText(atype)
        self._status_left.setText(f"{subject} \u00B7 {date}")
        self._status_type.setText(atype)
        sr = session.get("sample_rate", dash)
        nb = session.get("num_blocks", dash)
        self._status_session.setText(f"{sr}Hz \u00B7 {nb} blocks")

    def _update_status_params(self):
        s = self.state
        self._status_params.setText(
            f"LP:{s.lp_cutoff_hz:.0f}Hz \u00B7 SG:{s.sg_window_ms:.0f}ms "
            f"\u00B7 Sac:{s.saccade_threshold:.0f}\u00B0/s"
        )

    def _update_title(self):
        base = "Behavioral Experiment Analysis"
        if self.state.phase == "wizard":
            suffix = _WIZARD_TITLES.get(self.state.wizard_step, "")
            self.setWindowTitle(f"{base} \u2014 {suffix}")
        else:
            suffix = _WORKSPACE_TITLES.get(self.state.workspace_tab, "")
            self.setWindowTitle(f"{base} \u2014 {suffix}")

    def _apply_theme_styles(self, theme):
        """Apply theme-dependent inline styles to toolbar, status bar, etc."""
        t = theme

        # Toolbar background
        self._toolbar.setStyleSheet(
            f"#workspaceToolbar {{ background-color: {t['bgTopbar']}; "
            f"border-bottom: 1px solid {t['border']}; }}"
        )

        # Toolbar labels (light on dark)
        self._tb_mouse_id.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {t['textInverse']};"
        )
        self._tb_date.setStyleSheet(
            f"font-family: 'Consolas','SF Mono','Menlo',monospace; "
            f"font-size: 11px; color: {t['textOnTopbar']};"
        )
        self._tb_type_badge.set_dark(self.state.dark_mode)

        # New Analysis ghost button
        self._new_analysis_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; "
            f"color: {t['textOnTopbar']}; font-size: 11px; padding: 4px 10px; }}"
            f"QPushButton:hover {{ color: {t['textInverse']}; }}"
        )

        # Tab control colors
        self._tab_control.set_theme(
            active_bg=t["bgTabActive"],
            active_fg=t["textInverse"],
            inactive_bg=t["bgTabInactive"],
            inactive_fg=t["textOnTopbar"],
            border=t["border"],
        )

        # Gear button
        self._update_gear_style()

        # Status bar (muted accent background)
        self._status_bar.setStyleSheet(
            f"background-color: {t['accentDark']};"
        )
        self._status_left.setStyleSheet(
            f"font-weight: 600; font-size: 11px; color: {t['textInverse']};"
        )
        self._status_type.setStyleSheet(
            f"font-size: 11px; font-family: 'Consolas','SF Mono','Menlo',monospace; "
            f"color: rgba(255,255,255,0.7);"
        )
        self._status_params.setStyleSheet(
            f"font-size: 11px; font-family: 'Consolas','SF Mono','Menlo',monospace; "
            f"color: rgba(255,255,255,0.85);"
        )
        self._status_session.setStyleSheet(
            f"font-size: 11px; font-family: 'Consolas','SF Mono','Menlo',monospace; "
            f"color: rgba(255,255,255,0.5);"
        )

    def _update_gear_style(self):
        t = DARK_THEME if self.state.dark_mode else LIGHT_THEME
        is_open = self.state.settings_open
        if is_open:
            self._gear_btn.setStyleSheet(
                f"QPushButton {{ font-size: 16px; border: 1px solid {t['accent']}; "
                f"border-radius: 3px; background-color: {t['accentLight']}; "
                f"color: {t['accent']}; }}"
            )
        else:
            self._gear_btn.setStyleSheet(
                f"QPushButton {{ font-size: 16px; border: 1px solid {t['border']}; "
                f"border-radius: 3px; background-color: transparent; "
                f"color: {t['textOnTopbar']}; }}"
                f"QPushButton:hover {{ border-color: {t['accent']}; "
                f"color: {t['textInverse']}; }}"
            )


def main():
    """Application entry point."""
    import pyqtgraph as pg
    pg.setConfigOptions(antialias=False, useOpenGL=False)

    app = QApplication(sys.argv)
    apply_theme(app, LIGHT_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
