"""W2: Metadata & Output — metadata form, output config, launch analysis."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QGroupBox, QScrollArea,
    QFileDialog, QProgressDialog,
)
from PySide6.QtCore import Qt, QTimer

from ..widgets.badge import Badge
from ..widgets.flow_layout import FlowLayout


# Metadata field definitions: (key, label, required, auto_key, widget_type, width, options)
# auto_key: key in session metadata_defaults that auto-populates this field (or None)
_FIELDS = {
    "Subject Information": [
        ("subject_id", "Mouse ID", True, "subject_id", "line", 125, None),
        ("species", "Species", False, "species", "line", 105, None),
        ("strain", "Strain", True, None, "combo", 110, ["C57BL/6J", "C57BL/6N", "BALB/c", "Other"]),
        ("sex", "Sex", True, None, "combo", 75, ["Male", "Female"]),
        ("age", "Age", False, None, "line", 70, None),
        ("weight_g", "Wt (g)", False, None, "line", 65, None),
        ("genotype", "Genotype", True, None, "combo", 90, ["WT", "Het", "Hom", "Other"]),
    ],
    "Session Information": [
        ("session_date", "Date", True, "session_date", "line", 110, None),
        ("session_start_time", "Start", True, "session_start_time", "line", 90, None),
        ("experimenter", "Experimenter", True, None, "combo", 130, ["Select...", "Dr. Smith", "Dr. Jones", "Other"]),
        ("lab", "Lab", False, "lab", "line", 125, None),
        ("institution", "Institution", False, "institution", "line", 145, None),
        ("experiment_description", "Description", False, None, "line", 200, None),
    ],
    "Experiment Details": [
        ("cohort", "Cohort", True, None, "line", 105, None),
        ("subject_condition", "Condition", True, None, "combo", 90, ["WT", "KO", "Het", "Control"]),
        ("task_condition", "Task", True, "task_condition", "combo", 120, ["Std VOR", "OKR", "VORD", "Custom"]),
        ("stimulus_frequency_hz", "Freq", True, "stimulus_frequency_hz", "line", 70, None),
        ("magnet_eye", "Eye", False, None, "combo", 72, ["Right", "Left"]),
    ],
    "Device Information": [
        ("rig_id", "Rig", False, None, "combo", 85, ["Rig 1", "Rig 2", "Rig 3"]),
        ("recording_system", "Rec System", False, "recording_system", "line", 185, None),
        ("eye_tracking_system", "Eye Track", False, "eye_tracking_system", "line", 165, None),
        ("sampling_rate_hz", "Rate", True, "sampling_rate_hz", "line", 100, None),
    ],
}


class W2Screen(QWidget):
    """Wizard Step 2: Metadata & Output."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._field_widgets = {}  # key -> widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Control bar (includes Back, Save To, remaining counter, Start) ──
        ctrl = QFrame()
        ctrl.setObjectName("w1ControlBar")
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(12, 8, 12, 8)
        ctrl_layout.setSpacing(8)

        self._back_btn = QPushButton("\u2190 Back")
        self._back_btn.clicked.connect(self._on_back)
        ctrl_layout.addWidget(self._back_btn)

        save_label = QLabel("SAVE TO:")
        save_label.setStyleSheet(
            "font-size: 10px; font-weight: 700; letter-spacing: 0.06em;"
        )
        ctrl_layout.addWidget(save_label)

        save_browse = QPushButton("Browse")
        save_browse.setProperty("small", True)
        save_browse.clicked.connect(self._on_save_browse)
        ctrl_layout.addWidget(save_browse)

        self._save_path = QLineEdit()
        self._save_path.setPlaceholderText("Output directory...")
        self._save_path.setFixedWidth(240)
        ctrl_layout.addWidget(self._save_path)

        ctrl_layout.addStretch()

        self._remaining_label = QLabel()
        self._remaining_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #CF2C2C;"
        )
        ctrl_layout.addWidget(self._remaining_label)

        self._start_btn = QPushButton("Start Analysis")
        self._start_btn.setProperty("primary", True)
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._on_start)
        ctrl_layout.addWidget(self._start_btn)

        layout.addWidget(ctrl)

        # ── Metadata form (scrollable) ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)

        for section_title, fields in _FIELDS.items():
            group = QGroupBox(section_title)
            group_inner = QVBoxLayout(group)
            group_inner.setContentsMargins(8, 10, 8, 6)

            flow = FlowLayout(h_spacing=7, v_spacing=7)

            for key, label, required, auto_key, wtype, width, options in fields:
                field_container = QWidget()
                field_layout = QVBoxLayout(field_container)
                field_layout.setContentsMargins(0, 0, 0, 0)
                field_layout.setSpacing(2)

                # Label row
                label_row = QHBoxLayout()
                label_row.setContentsMargins(0, 0, 0, 0)
                label_row.setSpacing(3)

                if required:
                    label_text = f"<span style='color:#3E6E8C;font-weight:800;'>*</span> {label}"
                else:
                    label_text = label

                lbl = QLabel(label_text)
                lbl.setStyleSheet("font-size: 11px; font-weight: 600;")
                label_row.addWidget(lbl)

                if auto_key:
                    badge = Badge("auto", variant="green")
                    label_row.addWidget(badge)

                label_row.addStretch()
                field_layout.addLayout(label_row)

                # Input widget
                if wtype == "combo":
                    widget = QComboBox()
                    widget.setFixedWidth(width)
                    if options:
                        widget.addItems(options)
                    widget.currentTextChanged.connect(
                        lambda *_: self._update_remaining()
                    )
                else:
                    widget = QLineEdit()
                    widget.setFixedWidth(width)
                    widget.textChanged.connect(
                        lambda *_: self._update_remaining()
                    )

                field_layout.addWidget(widget)
                field_container.setFixedWidth(width + 10)
                flow.addWidget(field_container)
                self._field_widgets[key] = (widget, wtype, required, auto_key)

            group_inner.addLayout(flow)
            form_layout.addWidget(group)

        form_layout.addStretch()
        scroll.setWidget(form_widget)
        layout.addWidget(scroll, 1)

        # Listen for session data to auto-populate
        self.state.session_data_changed.connect(self._on_session_loaded)

        # Initial update
        self._update_remaining()

    def _on_back(self):
        self.state.wizard_step = 1

    def _on_session_loaded(self, session_data):
        """Auto-populate fields from session metadata_defaults."""
        if session_data is None:
            return
        defaults = session_data.get("metadata_defaults", {})
        for key, (widget, wtype, required, auto_key) in self._field_widgets.items():
            if auto_key and auto_key in defaults:
                value = defaults[auto_key]
                if wtype == "combo":
                    idx = widget.findText(value)
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
                    else:
                        widget.addItem(value)
                        widget.setCurrentText(value)
                else:
                    widget.setText(str(value))
        self._update_remaining()

    def _get_field_value(self, key):
        widget, wtype, _, _ = self._field_widgets[key]
        if wtype == "combo":
            text = widget.currentText()
            return text if text and text != "Select..." else ""
        return widget.text().strip()

    def _update_remaining(self):
        count = 0
        for key, (widget, wtype, required, auto_key) in self._field_widgets.items():
            if required and not self._get_field_value(key):
                count += 1

        if count > 0:
            self._remaining_label.setText(
                f"{count} required field{'s' if count != 1 else ''} remaining"
            )
            self._remaining_label.setStyleSheet(
                "font-size: 11px; font-weight: 600; color: #CF2C2C;"
            )
            self._start_btn.setEnabled(False)
        else:
            self._remaining_label.setText("\u2713 All fields complete")
            self._remaining_label.setStyleSheet(
                "font-size: 11px; font-weight: 600; color: #1A9E50;"
            )
            self._start_btn.setEnabled(True)

    def _on_save_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self._save_path.setText(path)

    def _on_start(self):
        # Collect metadata into state
        metadata = {}
        for key in self._field_widgets:
            metadata[key] = self._get_field_value(key)
        self.state.metadata = metadata

        # Show progress dialog
        progress = QProgressDialog(
            "Processing...\nSegmenting blocks, preparing workspace...",
            None, 0, 0, self
        )
        progress.setWindowTitle("Preparing Analysis")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        # Simulate processing delay then transition
        QTimer.singleShot(1200, lambda: self._finish_start(progress))

    def _finish_start(self, progress):
        progress.close()
        self.state.phase = "workspace"
