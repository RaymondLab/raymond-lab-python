"""W2: Metadata & Output — metadata form, output config, navigate to W3."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QGroupBox, QScrollArea,
    QFileDialog,
)
from PySide6.QtCore import Qt

from ...themes import THEME
from ...models.session_model import METADATA_FIELD_DEFS, REQUIRED_METADATA_FIELDS
from ..widgets.badge import Badge
from ..widgets.flow_layout import FlowLayout

_BORDER_MISSING = f"border: 1.5px solid {THEME['qualBad']}; border-radius: 3px;"
_BORDER_NORMAL = "border: 1px solid #CBD5E1; border-radius: 3px;"


class W2Screen(QWidget):
    """Wizard Step 2: Metadata & Output."""

    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self._field_widgets = {}  # key -> (widget, wtype, required)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Control bar ──
        ctrl = QFrame()
        ctrl.setObjectName("w1ControlBar")
        ctrl_layout = QHBoxLayout(ctrl)
        ctrl_layout.setContentsMargins(12, 14, 12, 18)
        ctrl_layout.setSpacing(8)

        self._back_btn = QPushButton("\u2190 Back")
        self._back_btn.clicked.connect(lambda: self.vm.go_to_wizard_step(1))
        ctrl_layout.addWidget(self._back_btn)

        ctrl_layout.addStretch()

        self._remaining_label = QLabel()
        self._remaining_label.setStyleSheet(
            f"font-size: {THEME['fontSm']}; font-weight: 600; "
            f"color: {THEME['qualBad']};"
        )
        ctrl_layout.addWidget(self._remaining_label)

        self._next_btn = QPushButton("Next \u2192")
        self._next_btn.setProperty("primary", True)
        self._next_btn.setEnabled(False)
        self._next_btn.clicked.connect(lambda: self.vm.go_to_wizard_step(3))
        ctrl_layout.addWidget(self._next_btn)

        layout.addWidget(ctrl)

        # ── Metadata form (scrollable) ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(8)

        # Output directory group
        output_group = QGroupBox("Output")
        output_inner = QHBoxLayout(output_group)
        output_inner.setContentsMargins(8, 10, 8, 6)
        output_inner.setSpacing(7)

        save_browse = QPushButton("Browse")
        save_browse.setProperty("small", True)
        save_browse.setFixedHeight(42)
        save_browse.clicked.connect(self._on_save_browse)
        output_inner.addWidget(save_browse)

        # Label + field column (matches metadata field layout)
        save_col = QVBoxLayout()
        save_col.setContentsMargins(0, 0, 0, 0)
        save_col.setSpacing(2)

        save_label = QLabel("Save To")
        save_label.setStyleSheet(
            f"font-size: {THEME['fontSm']}; font-weight: 600; "
            f"background-color: {THEME['bgApp']};"
        )
        save_col.addWidget(save_label)

        self._save_path = QLineEdit()
        self._save_path.setPlaceholderText("Output directory...")
        save_col.addWidget(self._save_path)

        output_inner.addLayout(save_col, 1)

        form_layout.addWidget(output_group)

        for section_title, fields in METADATA_FIELD_DEFS.items():
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
                    accent = THEME["accent"]
                    label_text = (
                        f"<span style='color:{accent};font-weight:800;'>*</span> "
                        f"{label}"
                    )
                else:
                    label_text = label

                lbl = QLabel(label_text)
                lbl.setStyleSheet(
                    f"font-size: {THEME['fontSm']}; font-weight: 600;"
                )
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
                        lambda val, k=key: self._on_field_changed(k, val)
                    )
                else:
                    widget = QLineEdit()
                    widget.setFixedWidth(width)
                    widget.textChanged.connect(
                        lambda val, k=key: self._on_field_changed(k, val)
                    )

                field_layout.addWidget(widget)
                field_container.setFixedWidth(width + 10)
                flow.addWidget(field_container)
                self._field_widgets[key] = (widget, wtype, required)

            group_inner.addLayout(flow)
            form_layout.addWidget(group)

        form_layout.addStretch()
        scroll.setWidget(form_widget)
        layout.addWidget(scroll, 1)

        # ── Wire VM signals ──
        self.vm.file_loaded.connect(self._on_session_loaded)
        self.vm.remaining_fields_changed.connect(self._on_remaining_changed)

        # Push initial combo values into metadata (addItems may not fire
        # currentTextChanged reliably across PySide6 versions)
        self._sync_all_widget_values()
        self._on_remaining_changed(self.vm.data.metadata.count_remaining())

    def _sync_all_widget_values(self):
        """Push every widget's current value into metadata."""
        for key, (widget, wtype, _required) in self._field_widgets.items():
            if wtype == "combo":
                val = widget.currentText()
            else:
                val = widget.text()
            if val:
                self.vm.data.metadata.set(key, val)

    def _on_field_changed(self, key, value):
        self.vm.update_metadata_field(key, value)

    def _on_session_loaded(self):
        """Auto-populate fields from session metadata_defaults."""
        metadata = self.vm.data.metadata
        for key, (widget, wtype, _required) in self._field_widgets.items():
            val = metadata.get(key)
            if val:
                if wtype == "combo":
                    idx = widget.findText(val)
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
                    else:
                        widget.addItem(val)
                        widget.setCurrentText(val)
                else:
                    widget.setText(val)
        # Force a full sync after auto-populate in case signals were missed
        self._sync_all_widget_values()
        count = self.vm.data.metadata.count_remaining()
        self.vm.remaining_fields_changed.emit(count)

    def _on_remaining_changed(self, count):
        if count > 0:
            self._remaining_label.setText(
                f"{count} required field{'s' if count != 1 else ''} remaining"
            )
            self._remaining_label.setStyleSheet(
                f"font-size: {THEME['fontSm']}; font-weight: 600; "
                f"color: {THEME['qualBad']};"
            )
            self._next_btn.setEnabled(False)
        else:
            self._remaining_label.setText("\u2713 All fields complete")
            self._remaining_label.setStyleSheet(
                f"font-size: {THEME['fontSm']}; font-weight: 600; "
                f"color: {THEME['qualGood']};"
            )
            self._next_btn.setEnabled(True)
        self._update_field_styles()

    def _update_field_styles(self):
        """Highlight required fields that are still missing a valid value."""
        metadata = self.vm.data.metadata
        for key, (widget, wtype, required) in self._field_widgets.items():
            if not required:
                continue
            val = metadata.get(key)
            is_missing = not val or val == "Select..."
            border = _BORDER_MISSING if is_missing else _BORDER_NORMAL
            if wtype == "combo":
                widget.setStyleSheet(f"QComboBox {{ {border} }}")
            else:
                widget.setStyleSheet(f"QLineEdit {{ {border} }}")

    def _on_save_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self._save_path.setText(path)
