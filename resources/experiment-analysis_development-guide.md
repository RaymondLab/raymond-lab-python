# Behavioral Experiment Analysis GUI — Development Guide

**Prototype reference:** `experiment-analysis_prototype.jsx`
**Architecture:** MVVM (Model–View–ViewModel)
**Target implementation:** Python 3.10+, PySide6, pyqtgraph
**Target platforms:** Windows 11 (primary), macOS (secondary)

---

## Table of Contents

1. [Application Overview](#1-application-overview)
2. [Navigation Architecture](#2-navigation-architecture)
3. [MVVM Architecture](#3-mvvm-architecture)
4. [Model Layer](#4-model-layer)
5. [ViewModel Layer](#5-viewmodel-layer)
6. [View Layer](#6-view-layer)
7. [Design System](#7-design-system)
8. [Screen Specifications](#8-screen-specifications)
9. [Shared View Components](#9-shared-view-components)
10. [Data Flow & Recomputation](#10-data-flow--recomputation)
11. [PySide6 Implementation Notes](#11-pyside6-implementation-notes)
12. [Prototype-to-Qt Component Adaptation](#12-prototype-to-qt-component-adaptation)
13. [Performance & Responsiveness](#13-performance--responsiveness)
14. [Maintainability for a Solo Developer](#14-maintainability-for-a-solo-developer)

---

## 1. Application Overview

This application replaces the existing MATLAB-based "Gain Analysis App" and "OKR NDD Analysis App" with a single, unified tool for analyzing behavioral experiment data (VOR, OKR, and related paradigms). It loads Spike2 recording files, guides the researcher through metadata entry for NWB/BIDS compliance, and provides an interactive workspace for signal exploration, cycle-averaged block analysis, and results export.

### Key Design Principles

- **Wizard for setup, workspace for analysis.** The first two screens are linear and guided; the remaining three are freely navigable tabs with real-time parameter feedback.
- **Real-time parameter tuning.** Adjusting filter cutoffs, differentiation windows, and saccade thresholds immediately updates all signal plots — no "re-run" button.
- **Calibration lives where its effects are visible.** Calibration loading/entry is in the Signal Explorer (A1), not in a separate setup step, so the researcher can instantly verify correctness.
- **Metadata is gated but not blocking.** The "Start Analysis" button is disabled until all required NWB/BIDS metadata fields are filled, but the form auto-populates whatever it can from the loaded file.
- **Non-technical users.** All interactions are GUI-based. No command-line usage. Tooltips for technical parameters.

---

## 2. Navigation Architecture

### Phase A — Setup Wizard (2 steps, linear)

```
W1: Load & Review  ──Next──►  W2: Metadata & Output  ──Start Analysis──►  [Workspace]
                    ◄──Back──
```

- "Next" on W1 is disabled until a file is loaded AND an analysis type is selected.
- "Start Analysis" on W2 is disabled until all required metadata fields have valid inputs.
- Clicking "Start Analysis" saves `_metadata.json`, shows a progress dialog, then transitions to the workspace.

### Phase B — Analysis Workspace (3 tabs, non-linear)

```
A1: Signal Explorer  ◄──►  A2: Block Analysis  ◄──►  A3: Results Summary
                              S1: Settings Panel (slide-out drawer)
```

- Three tabs freely navigable via a tab bar in the workspace toolbar.
- S1 is toggled by a gear icon button, overlays the right side without replacing the active tab.
- "↺ New Analysis" returns to W1 after confirmation dialog, resetting workspace state.

### Window Structure

- **Title bar:** Application name + contextual subtitle (current wizard step or workspace tab). Updated via `QMainWindow.setWindowTitle()`.
- **Workspace toolbar** (workspace phase only): Mouse ID, session date, analysis type badge | "↺ New Analysis" button, tab bar, gear icon.
- **Status bar** (workspace phase only): Accent-colored background. Left: experiment ID + analysis type. Right: live parameter values + session info.

---

## 3. MVVM Architecture

The application uses the **Model–View–ViewModel** pattern, following the same structure as the reference `test_abfconverter.py`. This separates concerns cleanly: the Model holds pure data, the ViewModel owns all logic and state transitions, and the View handles only UI construction and rendering.

```
┌─────────────────────────────────────────────────────┐
│                       VIEW                          │
│  QMainWindow, screen widgets, pyqtgraph PlotWidgets │
│                                                     │
│  • Builds UI layout                                 │
│  • Connects to ViewModel signals for updates        │
│  • Calls ViewModel methods on user interaction      │
│  • NEVER modifies Model directly                    │
└─────────────────┬───────────────────────────────────┘
                  │  calls methods ↓    ↑ emits signals
┌─────────────────▼───────────────────────────────────┐
│                    VIEW MODEL                       │
│            AnalysisViewModel(QObject)                │
│                                                     │
│  • Owns the Model instance                          │
│  • Exposes @property accessors for View to read     │
│  • Contains all business logic (filtering,          │
│    saccade detection, cycle analysis, validation)   │
│  • Emits Qt Signals when state changes              │
│  • Single source of truth for all shared state      │
└─────────────────┬───────────────────────────────────┘
                  │  reads/writes ↕
┌─────────────────▼───────────────────────────────────┐
│                      MODEL                          │
│          Pure Python dataclasses                     │
│                                                     │
│  • No Qt dependencies                               │
│  • SessionModel, BlockData, CalibrationData,        │
│    AnalysisParams, MetadataFields                   │
│  • Serializable to/from _metadata.json              │
└─────────────────────────────────────────────────────┘
```

### Why MVVM for this application

- **Shared state across multiple views.** Analysis parameters (LP cutoff, SG window, saccade threshold) are displayed and editable in A1's parameter bar, S1's settings panel, and shown in the status bar. With MVVM, all three views simply observe the same ViewModel signal — no `QSignalBlocker` needed.
- **Block selection sync.** `selected_block` is used by A1 (signal plots), A2 (cycle plot), and the block navigator in both. One ViewModel signal, multiple observers.
- **Recomputation cascade is business logic.** When a parameter changes, the sequence (refilter → rederive velocity → re-detect saccades → update metrics) belongs in the ViewModel, not in any view widget.
- **Testable.** The ViewModel and Model can be unit-tested without instantiating any Qt widgets or pyqtgraph plots.

---

## 4. Model Layer

Pure Python dataclasses. No Qt imports. These represent the data at rest.

```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import numpy as np


@dataclass
class ChannelData:
    """Raw channel data from a Spike2 file."""
    name: str                       # e.g., "htvel", "hhvel", "hepos1"
    data: np.ndarray                # 1D array of samples
    sample_rate: float              # Hz
    channel_type: str               # "waveform", "realwave", "event_level", "marker", "textmark"


@dataclass
class BlockInfo:
    """Detected block boundaries and metadata."""
    index: int                      # 0-based block index
    label: str                      # "VORD", "OKR", "VOR", etc.
    start_time: float               # seconds
    end_time: float                 # seconds
    frequency: float                # detected stimulus frequency (Hz)
    included: bool = True           # whether to include in analysis


@dataclass
class CalibrationData:
    """Calibration scaling factors."""
    source: str = "none"            # "file", "manual", "none"
    file_path: str = ""
    scale_ch1: Optional[float] = None
    scale_ch2: Optional[float] = None
    active_channel: str = "Auto"    # "Auto", "Ch1", "Ch2"


@dataclass
class AnalysisParams:
    """All tunable analysis parameters."""
    # Position filter
    filter_method: str = "Butterworth"
    lp_cutoff_hz: float = 40.0
    # Wavelet params (used when filter_method == "Wavelet")
    wavelet_level: int = 5
    wavelet_name: str = "sym4"
    wavelet_method: str = "BlockJS"

    # Differentiation
    sg_window_ms: float = 30.0

    # Saccade detection
    saccade_method: str = "SVT"
    saccade_threshold: float = 50.0
    saccade_min_dur_ms: float = 10.0
    saccade_padding_ms: float = 5.0

    # Eye channel
    eye_channel: str = "Auto"       # "Auto", "Ch1", "Ch2"


@dataclass
class BlockResults:
    """Computed results for a single block."""
    block_index: int
    gain: float
    eye_amp: float
    eye_amp_sem: float
    eye_phase: float
    eye_phase_sem: float
    stim_amp: float
    good_cycles: int
    total_cycles: int
    variance_residual: float
    cycle_quality: List[bool]       # True = good, False = saccade-detected


@dataclass
class MetadataFields:
    """NWB/BIDS metadata. Required fields marked in comments."""
    # Subject
    subject_id: str = ""            # required
    species: str = "Mus musculus"
    strain: str = ""                # required
    sex: str = ""                   # required
    age: str = ""
    weight_g: str = ""
    genotype: str = ""              # required

    # Session
    session_date: str = ""          # required (auto)
    session_start_time: str = ""    # required (auto)
    experimenter: str = ""          # required
    lab: str = "Raymond Lab"
    institution: str = "Stanford University"
    experiment_description: str = ""

    # Experiment
    cohort: str = ""                # required
    subject_condition: str = ""     # required
    task_condition: str = ""        # required (auto)
    stimulus_frequency_hz: str = "" # required (auto)
    magnet_eye: str = ""
    notes: str = ""

    # Device
    rig_id: str = ""
    recording_system: str = "CED Power1401 + Spike2"
    eye_tracking_system: str = "Magnetic (HMC1512)"
    sampling_rate_hz: str = ""      # required (auto)

    REQUIRED_FIELDS = [
        "subject_id", "strain", "sex", "genotype",
        "session_date", "session_start_time", "experimenter",
        "cohort", "subject_condition", "task_condition",
        "stimulus_frequency_hz", "sampling_rate_hz",
    ]

    def count_remaining(self) -> int:
        return sum(1 for f in self.REQUIRED_FIELDS if not getattr(self, f).strip())

    def is_complete(self) -> bool:
        return self.count_remaining() == 0


@dataclass
class SessionModel:
    """Top-level model containing all experiment data."""
    # File
    file_path: str = ""
    file_loaded: bool = False
    analysis_type: str = "Standard VOR"

    # Parsed data
    channels: List[ChannelData] = field(default_factory=list)
    blocks: List[BlockInfo] = field(default_factory=list)
    sample_rate: float = 0.0
    duration: float = 0.0

    # Calibration
    calibration: CalibrationData = field(default_factory=CalibrationData)

    # Parameters
    params: AnalysisParams = field(default_factory=AnalysisParams)

    # Results (per-block)
    block_results: List[BlockResults] = field(default_factory=list)

    # Processed signals for the currently selected block (cached)
    current_block_index: int = 0
    current_raw_position: Optional[np.ndarray] = None
    current_filtered_position: Optional[np.ndarray] = None
    current_raw_velocity: Optional[np.ndarray] = None
    current_filtered_velocity: Optional[np.ndarray] = None
    current_saccade_mask: Optional[np.ndarray] = None
    current_stimulus: Optional[np.ndarray] = None

    # Metadata
    metadata: MetadataFields = field(default_factory=MetadataFields)

    # Appearance
    dark_mode: bool = False

    # Output
    output_path: str = ""
```

---

## 5. ViewModel Layer

A single `AnalysisViewModel(QObject)` class that owns the `SessionModel` and exposes all state changes as Qt Signals. Follows the same pattern as the reference `NwbViewModel`.

```python
from PySide6.QtCore import QObject, Signal


class AnalysisViewModel(QObject):
    """Single source of truth for all application state."""

    # ── Navigation signals ──
    phase_changed = Signal(str)              # "wizard" or "workspace"
    wizard_step_changed = Signal(int)        # 1 or 2
    workspace_tab_changed = Signal(str)      # "A1", "A2", "A3"
    settings_toggled = Signal(bool)          # open/closed
    loading_started = Signal()
    loading_finished = Signal()

    # ── File & session signals ──
    file_loaded = Signal()                   # file successfully parsed
    session_info_changed = Signal()          # blocks, duration, channels updated
    block_structure_changed = Signal()       # block labels/inclusion edited
    analysis_type_changed = Signal(str)

    # ── Calibration signals ──
    calibration_changed = Signal()           # new calibration applied or cleared

    # ── Parameter signals ──
    params_changed = Signal()                # any analysis parameter changed
    filter_method_changed = Signal(str)      # triggers param UI swap

    # ── Selection signals ──
    selected_block_changed = Signal(int)     # block index
    selected_cycle_changed = Signal(int)     # cycle index (A2 only)
    display_mode_changed = Signal(str)       # "SEM", "All Cycles", "Good Cycles"

    # ── Computation signals ──
    block_signals_recomputed = Signal()      # filtered traces + saccades updated
    block_results_updated = Signal(int)      # metrics recomputed for block index
    all_results_stale = Signal()             # A3 needs refresh

    # ── Metadata signals ──
    metadata_changed = Signal()
    remaining_fields_changed = Signal(int)

    # ── Export signals ──
    export_completed = Signal(str)

    # ── Appearance signals ──
    theme_changed = Signal(bool)             # True = dark

    # ── Dialog request signals (View handles presentation) ──
    message_requested = Signal(str, str)     # title, message

    def __init__(self):
        super().__init__()
        self._data = SessionModel()

    # ═══════════════════════════════════════════════
    # PROPERTY ACCESSORS (View reads these)
    # ═══════════════════════════════════════════════

    @property
    def data(self) -> SessionModel:
        return self._data

    @property
    def is_file_loaded(self) -> bool:
        return self._data.file_loaded

    @property
    def analysis_type(self) -> str:
        return self._data.analysis_type

    @property
    def blocks(self) -> list:
        return self._data.blocks

    @property
    def selected_block(self) -> int:
        return self._data.current_block_index

    @property
    def params(self) -> AnalysisParams:
        return self._data.params

    @property
    def calibration(self) -> CalibrationData:
        return self._data.calibration

    @property
    def metadata(self) -> MetadataFields:
        return self._data.metadata

    @property
    def block_results(self) -> list:
        return self._data.block_results

    @property
    def is_dark(self) -> bool:
        return self._data.dark_mode

    # ═══════════════════════════════════════════════
    # NAVIGATION LOGIC
    # ═══════════════════════════════════════════════

    def go_to_wizard_step(self, step: int):
        self.wizard_step_changed.emit(step)

    def start_analysis(self):
        self._save_metadata_json()
        self.loading_started.emit()
        self._prepare_workspace()
        self.loading_finished.emit()
        self.phase_changed.emit("workspace")
        self.workspace_tab_changed.emit("A1")

    def switch_tab(self, tab: str):
        if tab == "A3":
            self._ensure_all_results_computed()
        self.workspace_tab_changed.emit(tab)

    def new_analysis(self):
        self._data = SessionModel()
        self.phase_changed.emit("wizard")
        self.wizard_step_changed.emit(1)

    def toggle_settings(self):
        # View tracks open/close state; VM just emits the toggle
        self.settings_toggled.emit(True)

    # ═══════════════════════════════════════════════
    # FILE LOADING
    # ═══════════════════════════════════════════════

    def load_file(self, path: str):
        self._data.file_path = path
        # ... parsing logic (channels, blocks, sample_rate, duration) ...
        self._data.file_loaded = True
        self._auto_populate_metadata()
        self.file_loaded.emit()
        self.session_info_changed.emit()

    def set_analysis_type(self, analysis_type: str):
        self._data.analysis_type = analysis_type
        self._apply_default_block_labels()
        self.analysis_type_changed.emit(analysis_type)
        self.block_structure_changed.emit()

    # ═══════════════════════════════════════════════
    # BLOCK MANAGEMENT
    # ═══════════════════════════════════════════════

    def update_block_label(self, block_index: int, label: str):
        self._data.blocks[block_index].label = label
        self.block_structure_changed.emit()

    def toggle_block_inclusion(self, block_index: int):
        b = self._data.blocks[block_index]
        b.included = not b.included
        self.block_structure_changed.emit()

    def select_block(self, index: int):
        if index == self._data.current_block_index:
            return
        self._data.current_block_index = index
        self._recompute_current_block()
        self.selected_block_changed.emit(index)

    # ═══════════════════════════════════════════════
    # CALIBRATION
    # ═══════════════════════════════════════════════

    def load_calibration_file(self, path: str):
        # ... load .mat, extract scaleCh1/scaleCh2, best channel ...
        self._data.calibration.source = "file"
        self._data.calibration.file_path = path
        self.calibration_changed.emit()
        self._recompute_current_block()

    def set_manual_calibration(self, scale_ch1: float, scale_ch2: float, active: str):
        self._data.calibration.source = "manual"
        self._data.calibration.scale_ch1 = scale_ch1
        self._data.calibration.scale_ch2 = scale_ch2
        self._data.calibration.active_channel = active
        self.calibration_changed.emit()
        self._recompute_current_block()

    # ═══════════════════════════════════════════════
    # PARAMETER UPDATES
    # ═══════════════════════════════════════════════

    def set_filter_method(self, method: str):
        self._data.params.filter_method = method
        self.filter_method_changed.emit(method)
        self._recompute_current_block()

    def set_lp_cutoff(self, value: float):
        self._data.params.lp_cutoff_hz = value
        self.params_changed.emit()
        self._recompute_current_block()

    def set_sg_window(self, value: float):
        self._data.params.sg_window_ms = value
        self.params_changed.emit()
        self._recompute_current_block()

    def set_saccade_method(self, method: str):
        self._data.params.saccade_method = method
        self.params_changed.emit()
        self._recompute_current_block()

    def set_saccade_threshold(self, value: float):
        self._data.params.saccade_threshold = value
        self.params_changed.emit()
        self._recompute_current_block()

    def set_saccade_min_dur(self, value: float):
        self._data.params.saccade_min_dur_ms = value
        self.params_changed.emit()
        self._recompute_current_block()

    def set_saccade_padding(self, value: float):
        self._data.params.saccade_padding_ms = value
        self.params_changed.emit()
        self._recompute_current_block()

    def reset_params_to_defaults(self):
        self._data.params = AnalysisParams()
        self.params_changed.emit()
        self.filter_method_changed.emit(self._data.params.filter_method)
        self._recompute_current_block()

    # ═══════════════════════════════════════════════
    # A2-SPECIFIC
    # ═══════════════════════════════════════════════

    def select_cycle(self, index: int):
        self.selected_cycle_changed.emit(index)

    def set_display_mode(self, mode: str):
        self.display_mode_changed.emit(mode)

    # ═══════════════════════════════════════════════
    # METADATA
    # ═══════════════════════════════════════════════

    def update_metadata_field(self, field_name: str, value: str):
        if hasattr(self._data.metadata, field_name):
            setattr(self._data.metadata, field_name, value)
            self.metadata_changed.emit()
            self.remaining_fields_changed.emit(self._data.metadata.count_remaining())

    # ═══════════════════════════════════════════════
    # APPEARANCE
    # ═══════════════════════════════════════════════

    def toggle_theme(self):
        self._data.dark_mode = not self._data.dark_mode
        self.theme_changed.emit(self._data.dark_mode)

    # ═══════════════════════════════════════════════
    # EXPORT
    # ═══════════════════════════════════════════════

    def export_excel(self, path: str):
        # ... export logic ...
        self.export_completed.emit(f"Excel saved to {path}")

    def export_figures(self, path: str):
        # ... figure set determined by analysis_type ...
        self.export_completed.emit(f"Figures saved to {path}")

    def export_workspace(self, path: str):
        # ... export logic ...
        self.export_completed.emit(f"Workspace saved to {path}")

    def export_all(self, folder: str):
        self.export_excel(folder)
        self.export_figures(folder)
        self.export_workspace(folder)

    # ═══════════════════════════════════════════════
    # PRIVATE: Computation Engine
    # ═══════════════════════════════════════════════

    def _recompute_current_block(self):
        """Core recomputation cascade. Called on parameter or block change."""
        idx = self._data.current_block_index
        block = self._data.blocks[idx]

        # 1. Extract raw segment for this block
        raw_pos = self._extract_block_segment("hepos", block)

        # 2. Apply position filter
        filtered_pos = self._apply_position_filter(raw_pos)

        # 3. Derive velocity via SG differentiation
        raw_vel = self._differentiate(raw_pos)
        filtered_vel = self._differentiate(filtered_pos)

        # 4. Detect saccades
        saccade_mask = self._detect_saccades(filtered_vel)

        # 5. Cache on model
        self._data.current_raw_position = raw_pos
        self._data.current_filtered_position = filtered_pos
        self._data.current_raw_velocity = raw_vel
        self._data.current_filtered_velocity = filtered_vel
        self._data.current_saccade_mask = saccade_mask

        # 6. Compute block metrics
        result = self._compute_block_metrics(idx, filtered_vel, saccade_mask)
        self._update_block_result(idx, result)

        # 7. Emit signals
        self.block_signals_recomputed.emit()
        self.block_results_updated.emit(idx)
        self.all_results_stale.emit()

    def _apply_position_filter(self, raw: np.ndarray) -> np.ndarray:
        p = self._data.params
        if p.filter_method == "Butterworth":
            return butterworth_lowpass(raw, p.lp_cutoff_hz, self._data.sample_rate)
        elif p.filter_method == "Wavelet":
            return wavelet_denoise(raw, p.wavelet_level, p.wavelet_name, p.wavelet_method)
        return raw

    def _detect_saccades(self, velocity: np.ndarray) -> np.ndarray:
        p = self._data.params
        if p.saccade_method == "SVT":
            return svt_detect(velocity, p.saccade_threshold, p.saccade_min_dur_ms,
                              p.saccade_padding_ms, self._data.sample_rate)
        elif p.saccade_method == "STD":
            return std_detect(velocity, p.saccade_threshold, p.saccade_min_dur_ms,
                              p.saccade_padding_ms, self._data.sample_rate)
        elif p.saccade_method == "MAD":
            return mad_detect(velocity, p.saccade_threshold, p.saccade_min_dur_ms,
                              p.saccade_padding_ms, self._data.sample_rate)
        return np.zeros_like(velocity, dtype=bool)

    # ... additional private methods:
    # _extract_block_segment, _differentiate, _compute_block_metrics,
    # _update_block_result, _prepare_workspace, _ensure_all_results_computed,
    # _apply_default_block_labels, _auto_populate_metadata, _save_metadata_json
```

---

## 6. View Layer

The View layer consists of the `QMainWindow` subclass and individual screen widgets. Each screen receives a reference to the shared `AnalysisViewModel`.

### Pattern 1: View → ViewModel (user actions)

```python
# User drags LP cutoff slider in A1:
self.lp_slider.valueChanged.connect(lambda v: self.vm.set_lp_cutoff(v))
```

### Pattern 2: ViewModel → View (state updates)

```python
# A1 connects to ViewModel signals:
self.vm.block_signals_recomputed.connect(self.refresh_plots)
self.vm.params_changed.connect(self.refresh_param_display)
self.vm.selected_block_changed.connect(self.update_block_navigator)
```

### Pattern 3: Guard against signal loops

When a View widget must be updated programmatically (e.g., the S1 slider when A1's slider changes), use a guard flag identical to the `GroupInspector._updating_view` pattern from the reference implementation:

```python
class SettingsPanel(QWidget):
    def __init__(self, vm: AnalysisViewModel):
        self.vm = vm
        self._updating_view = False

        self.lp_slider.valueChanged.connect(self._on_lp_changed)
        self.vm.params_changed.connect(self._refresh_from_vm)

    def _on_lp_changed(self, value):
        if not self._updating_view:
            self.vm.set_lp_cutoff(value)

    def _refresh_from_vm(self):
        self._updating_view = True
        self.lp_slider.setValue(int(self.vm.params.lp_cutoff_hz))
        self._updating_view = False
```

### Main window structure

```python
class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.vm = AnalysisViewModel()   # single ViewModel instance

        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # All screens receive the shared vm
        self.w1_screen = W1LoadReview(self.vm)
        self.w2_screen = W2MetadataOutput(self.vm)
        self.workspace = WorkspaceContainer(self.vm)

        self.stack.addWidget(self.w1_screen)
        self.stack.addWidget(self.w2_screen)
        self.stack.addWidget(self.workspace)

        self.status = AnalysisStatusBar(self.vm)
        self.setStatusBar(self.status)

    def connect_signals(self):
        self.vm.phase_changed.connect(self._on_phase_changed)
        self.vm.wizard_step_changed.connect(self._on_wizard_step)
        self.vm.theme_changed.connect(self._apply_theme)
        self.vm.message_requested.connect(
            lambda t, m: QMessageBox.information(self, t, m)
        )

    def _on_phase_changed(self, phase):
        if phase == "wizard":
            self.stack.setCurrentWidget(self.w1_screen)
            self.status.hide()
        else:
            self.stack.setCurrentWidget(self.workspace)
            self.status.show()
```

---

## 7. Design System

### 7.1 Color Palette — Light Theme (Default)

**UI Chrome (accent: steel blue `#3E6E8C`):**

| Token | Hex | Usage |
|-------|-----|-------|
| `bgApp` | `#E8ECF0` | Application background |
| `bgPanel` | `#FFFFFF` | Card/panel backgrounds |
| `bgPanelAlt` | `#EFF2F6` | Alternate backgrounds (table headers, summary bars) |
| `bgInput` | `#FFFFFF` | Input field backgrounds |
| `bgTopbar` | `#263040` | Title bar |
| `bgTabActive` | `#3E6E8C` | Active tab / primary button |
| `bgCalibration` | `#EFF4F8` | Calibration section |
| `bgParamBar` | `#F3F6F9` | Parameter control bar |
| `bgPlot` | `#F8FAFB` | pyqtgraph PlotWidget background |
| `border` | `#CDD4DC` | Standard borders |
| `borderLight` | `#DFE4EA` | Light borders |
| `accent` | `#3E6E8C` | Primary interactive color |
| `accentDark` | `#2E5A74` | Hover/pressed states |
| `accentLight` | `#E0EDF5` | Accent backgrounds (badges) |

**Text:**

| Token | Hex | Usage |
|-------|-----|-------|
| `textPrimary` | `#1A2230` | Headings, values |
| `textSecondary` | `#4E5A6A` | Labels, section titles |
| `textTertiary` | `#8490A0` | Hints, placeholders |
| `textInverse` | `#FFFFFF` | Text on accent backgrounds |

**Signal Trace Colors (pyqtgraph pens):**

| Token | Hex | Usage |
|-------|-----|-------|
| `dataPosition` | `#E8690B` | Filtered eye position (orange) |
| `dataVelocity` | `#2563EB` | Filtered eye velocity (blue) |
| `dataSaccade` | `#D42A2A` | Saccade segments (red) |
| `dataStimulus` | `#8490A0` | Stimulus, dashed (gray) |
| `dataFit` | `#1A2230` | Sinusoidal fit (dark) |
| `dataRaw` | `#BCC4CE` | Raw traces (light gray) |
| `dataSem` | `#D6E4F7` | ±SEM fill (light blue) |

**Block & Quality:**

| Token | Hex | Usage |
|-------|-----|-------|
| `blockPrepost` | `#0F8A5F` | Pre/post-test blocks (green) |
| `blockPrepostBg` | `#D6F0E4` | Pre/post background fills |
| `blockTrain` | `#CF2C4A` | Training blocks (red) |
| `blockTrainBg` | `#FAE0E5` | Training background fills |
| `qualGood` | `#1A9E50` | ≥40% good cycles |
| `qualWarn` | `#D4930D` | 20–40% good cycles |
| `qualBad` | `#CF2C2C` | <20% good cycles |
| `qualSelected` | `#2D5FD4` | Selected cycle (indigo) |

### 7.2 Dark Theme

Same token names, shifted for dark backgrounds. Key changes: `accent` → `#508CB0`, `bgApp` → `#141A22`, `bgPanel` → `#1C2430`, signal colors brightened for contrast.

### 7.3 Typography

| Role | Font | Size | Weight |
|------|------|------|--------|
| UI text | Segoe UI / SF Pro Text | 11–12px | 400–600 |
| Section headers | Segoe UI | 10–11px | 700, UPPERCASE |
| Data values, paths | Consolas / SF Mono | 10–12px | 400–700 |

### 7.4 Spacing

Border radius: 3px. Button padding: 5px 14px (standard), 3px 10px (small). Input padding: 4px 7px. Slider track: 4px height, 14px thumb. No box shadows (QSS constraint).

---

## 8. Screen Specifications

### 8.1 W1: Load & Review

**Layout:** Control bar → Session summary → [Timeline plots | Block table]

- **Control bar:** [Browse] [File path QLineEdit] [Analysis Type QComboBox] [Next → QPushButton]
- **Timeline plots:** 3 stacked, each with channel QComboBox + pyqtgraph PlotWidget + block region overlays. Third plot shows hepos1 (orange) + hepos2 (blue).
- **Block table:** QTableView — #, Label (editable QComboBox delegate), Hz, ✓ (QCheckBox)
- **Empty state:** Centered placeholder when no file loaded

**View→VM:** `Browse.clicked → vm.load_file(path)` · `analysis_type.changed → vm.set_analysis_type(type)` · `Next.clicked → vm.go_to_wizard_step(2)`
**VM→View:** `vm.file_loaded → refresh_plots()` · `vm.block_structure_changed → refresh_block_table()`

### 8.2 W2: Metadata & Output

**Layout:** Control bar (top) → Scrollable metadata form (4 QGroupBox sections)

- **Control bar:** [← Back] [SAVE TO: Browse + path] [remaining count] [Start Analysis]
- **Form sections:** Subject, Session, Experiment, Device — labeled fields with red asterisks for required, green "auto" badges

**View→VM:** `field.textChanged → vm.update_metadata_field(name, value)` · `Start.clicked → vm.start_analysis()`
**VM→View:** `vm.remaining_fields_changed → update_counter()` · `vm.loading_started → show_progress()`

### 8.3 A1: Signal Explorer

**Layout:** Calibration (collapsible) → Block navigator → [Position plot | Velocity plot] → Parameter bar

- **Calibration:** Collapsible QGroupBox. Load File / Manual toggle. Scaling values + sanity badge.
- **Eye Position plot:** raw, filtered (orange), saccade segments + region fills
- **Eye Velocity plot:** stimulus (dashed), raw, filtered (blue), saccade segments + region fills
- **Parameter bar:** Position Filter (method QComboBox + method-specific params), Differentiation (SG Window), Saccade Detection (method QComboBox + threshold)

**View→VM:** `slider.changed → vm.set_lp_cutoff()` · `cali_browse → vm.load_calibration_file()` · `block_click → vm.select_block()`
**VM→View:** `vm.block_signals_recomputed → refresh_both_plots()` · `vm.calibration_changed → refresh_cali_display()` · `vm.params_changed → refresh_sliders()` (with `_updating_view` guard)

### 8.4 A2: Block Analysis

**Layout:** Block navigator → Cycle navigator + display mode → [Cycle plot | Metrics card]

- **Cycle navigator:** Green=good, red=saccade, blue=selected
- **Display mode:** SEM / All Cycles / Good Cycles segmented control
- **Cycle plot:** Average + SEM fill (SEM mode) or individual traces with selected highlighted (cycle modes)
- **Block Metrics:** Key-value pairs (Gain, Amp±SEM, Phase±SEM, etc.)

**View→VM:** `cycle_click → vm.select_cycle()` · `mode_click → vm.set_display_mode()` · `block_click → vm.select_block()`
**VM→View:** `vm.selected_block_changed → reload_cycle_data()` · `vm.block_results_updated → refresh_metrics()`

### 8.5 A3: Results Summary

**Layout:** Y-axis QComboBox → Gain time course plot → Results table → Export buttons

- **Scatter plot:** Block # vs. metric, green (pre/post) and red (training) markers
- **Table:** QTableView — #, Label, Hz, Start, End, Dur, Amp±SEM, Ph±SEM, StimA, Gain, GoodCyc, VarRes
- **Export bar:** Excel, Figures, Workspace, Export All

**VM→View:** `vm.all_results_stale → mark_stale()` → recompute on tab switch

### 8.6 S1: Settings Panel

**Width:** 265px, right-side drawer. Header + scrollable sections + Reset button.

**Sections:** Position Filter, Differentiation, Saccade Detection, Eye Channel, Appearance (dark mode toggle). All bidirectionally synced with A1 via `_updating_view` guard pattern.

---

## 9. Shared View Components

### 9.1 Block Navigator

Custom `QWidget` with `paintEvent`. Used in A1 and A2.

- **Top row (13px):** Block label colors (green pre/post, red training). Selected = 2px outline.
- **Bottom row (9px):** Good-cycle quality (green/amber/red).
- **◂/▸ buttons:** Call `vm.select_block(current ± 1)`.
- **Click segment:** Call `vm.select_block(index)`.
- **Observes:** `vm.selected_block_changed`, `vm.block_results_updated`.

### 9.2 Cycle Navigator (A2 only)

Custom `QWidget` with `paintEvent`. Green=good, red=saccade, blue=selected.

- **Click:** Call `vm.select_cycle(index)`.
- **Observes:** `vm.selected_cycle_changed`, `vm.selected_block_changed` (rebuild on block change).

### 9.3 Parameter Slider

Composite: `QLabel` (right-aligned) + `QSlider` + `QLabel` (monospace value). Slider groove: 4px `border` color, sub-page: `accent`, handle: 14px circle.

---

## 10. Data Flow & Recomputation

### Full pipeline

```
[.smr file] → W1: vm.load_file() → parse channels, detect blocks
            → W2: vm.start_analysis() → save _metadata.json, prepare workspace
            → A1: vm.load_calibration_file() or vm.set_manual_calibration()
                → vm._recompute_current_block():
                    1. Extract raw position segment
                    2. Apply position filter (Butterworth / Wavelet)
                    3. Derive velocity via SG differentiation
                    4. Detect saccades (SVT / STD / MAD)
                    5. Cache processed signals on Model
                    6. Compute block metrics (gain, amplitude, phase, etc.)
                    7. Emit: block_signals_recomputed, block_results_updated, all_results_stale
            → A2: Reads cached signals + results via ViewModel properties
            → A3: vm._ensure_all_results_computed() (lazy, on tab switch)
            → Export: vm.export_*() → .xlsx + .pdf + .mat
```

### Recomputation trigger map

| User Action | VM Method | Recomputes | Signals |
|-------------|-----------|------------|---------|
| Drag LP slider | `set_lp_cutoff()` | Current block | `params_changed`, `block_signals_recomputed`, `block_results_updated`, `all_results_stale` |
| Change saccade threshold | `set_saccade_threshold()` | Current block | Same |
| Select different block | `select_block()` | New block | `selected_block_changed`, `block_signals_recomputed`, `block_results_updated` |
| Apply calibration | `load_calibration_file()` | Current block | `calibration_changed`, `block_signals_recomputed`, `all_results_stale` |
| Switch to A3 | `switch_tab("A3")` | All blocks (lazy) | Per-block `block_results_updated` |
| Reset defaults | `reset_params_to_defaults()` | Current block | `params_changed`, `filter_method_changed`, `block_signals_recomputed` |

### Performance

- **Debounce sliders:** `QTimer.singleShot(80, ...)` in ViewModel setter methods.
- **Lazy A3:** Mark stale on param change; recompute all blocks only on A3 tab switch.
- **Downsampled W1 display:** Show every 10th sample in session timeline.
- **Block navigator:** Custom `QPainter` — fast for 60+ blocks.

---

## 11. PySide6 Implementation Notes

### 11.1 Widget Mapping

| Component | PySide6 Widget |
|-----------|----------------|
| Wizard/workspace switch | `QStackedWidget` |
| Workspace tabs | `QStackedWidget` + custom tab buttons |
| Settings drawer | `QWidget` in `QHBoxLayout` (toggled visibility) |
| Signal plots | `pyqtgraph.PlotWidget` |
| Block/cycle navigator | Custom `QWidget` with `paintEvent` |
| Block table (W1) | `QTableView` + `QStandardItemModel` + delegates |
| Results table (A3) | `QTableView` + custom `QAbstractTableModel` |
| Metadata form (W2) | `QScrollArea` → `QGroupBox` → `QGridLayout` |
| Loading dialog | `QProgressDialog` |
| Confirm dialogs | `QMessageBox` |

### 11.2 QSS Theming

Store themes as Python dicts. Apply global stylesheet at `QApplication` level. On theme switch, regenerate and reapply:

```python
def apply_theme(self, is_dark: bool):
    colors = THEMES["dark"] if is_dark else THEMES["light"]
    self.setStyleSheet(build_stylesheet(colors))
    for pw in self.all_plot_widgets:
        pw.setBackground(colors["bgPlot"])
```

### 11.3 pyqtgraph Setup

```python
pw.setBackground(theme['bgPlot'])
pw.getAxis('bottom').setPen(pg.mkPen(theme['border']))
pw.getAxis('left').setPen(pg.mkPen(theme['border']))
pw.showGrid(x=True, y=True, alpha=0.1)

# Pens:
raw_pen      = pg.mkPen(theme['dataRaw'], width=1)
pos_pen      = pg.mkPen(theme['dataPosition'], width=2)
vel_pen      = pg.mkPen(theme['dataVelocity'], width=2)
saccade_pen  = pg.mkPen(theme['dataSaccade'], width=1.5)
stimulus_pen = pg.mkPen(theme['dataStimulus'], width=1, style=Qt.DashLine)
fit_pen      = pg.mkPen(theme['dataFit'], width=1.5)

# Saccade regions: pg.LinearRegionItem, 6-8% opacity, immovable
# Block regions in W1: pg.LinearRegionItem, 15-20% opacity, immovable
```

### 11.4 File Structure

```
experiment_analysis/
├── main.py                          # QApplication, theme detection, launch
├── models/
│   ├── __init__.py
│   ├── session_model.py             # All dataclasses
│   └── metadata_fields.py           # MetadataFields with validation
├── viewmodels/
│   ├── __init__.py
│   └── analysis_viewmodel.py        # AnalysisViewModel(QObject)
├── views/
│   ├── __init__.py
│   ├── main_window.py               # AnalysisWindow(QMainWindow)
│   ├── screens/
│   │   ├── w1_load_review.py
│   │   ├── w2_metadata_output.py
│   │   ├── a1_signal_explorer.py
│   │   ├── a2_block_analysis.py
│   │   ├── a3_results_summary.py
│   │   └── s1_settings_panel.py
│   └── widgets/
│       ├── block_navigator.py       # Custom QWidget
│       ├── cycle_navigator.py       # Custom QWidget
│       ├── parameter_slider.py      # Composite widget
│       └── badge.py                 # Styled QLabel
├── analysis/                        # Pure functions, no Qt, independently testable
│   ├── file_loader.py               # Spike2 parsing
│   ├── block_detection.py
│   ├── filters.py                   # Butterworth, wavelet
│   ├── saccade_detection.py         # SVT, STD, MAD
│   ├── differentiation.py           # Savitzky-Golay
│   ├── sinusoidal_fit.py
│   └── cycle_analysis.py
├── export/
│   ├── xlsx_export.py
│   ├── pdf_export.py
│   ├── mat_export.py
│   └── metadata_json.py
├── themes/
│   ├── __init__.py
│   ├── colors.py                    # Light/dark dicts
│   └── stylesheet.py               # build_stylesheet(colors) → QSS string
└── resources/
    └── icons/
```

The `analysis/` directory contains pure functions with no Qt or UI dependencies. The ViewModel calls into these functions. This means the entire signal processing pipeline is independently testable via pytest without needing a running `QApplication`.

---

## 12. Prototype-to-Qt Component Adaptation

The JSX prototype uses web-native patterns (CSS flexbox, inline styles, arbitrary border-radius, CSS transitions, etc.) that have no direct PySide6 equivalents. This section maps every such component to its Qt adaptation, preserving the visual intent without compromising the aesthetics.

### 12.1 Collapsible Calibration Panel (A1)

**Prototype:** A `<div>` with a clickable header that toggles between `▸` / `▾` states, showing/hiding the content row via conditional rendering.

**Qt adaptation:** Use a `QGroupBox` with `setCheckable(False)` and a custom header widget. Place a `QPushButton` styled as flat text (no border, just the ▸/▾ character + "CALIBRATION" label) at the top. Connect its `clicked` signal to toggle the visibility of a child `QWidget` containing the expanded content via `content_widget.setVisible(not content_widget.isVisible())`. When collapsed, show a summary `QLabel` row (scaling values + sanity badge) beside the toggle button. When expanded, hide the summary and show the full controls. No animation needed — instant show/hide is fine and avoids Qt animation complexity.

```python
class CollapsibleCalibration(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.toggle_btn = QPushButton("▾ CALIBRATION")
        self.toggle_btn.setFlat(True)
        self.toggle_btn.clicked.connect(self._toggle)

        self.summary_row = QWidget()    # visible when collapsed
        self.detail_row = QWidget()     # visible when expanded
        self._expanded = True

    def _toggle(self):
        self._expanded = not self._expanded
        self.toggle_btn.setText(("▾" if self._expanded else "▸") + " CALIBRATION")
        self.detail_row.setVisible(self._expanded)
        self.summary_row.setVisible(not self._expanded)
```

### 12.2 Dark Theme Toggle Switch (S1)

**Prototype:** A custom pill-shaped toggle with a sliding circle, built from nested `<div>`s with `border-radius: 9px` and CSS `transition`.

**Qt adaptation:** Use a standard `QCheckBox` with custom QSS to make it appear as a toggle switch. This is a well-documented QSS pattern that works reliably in PySide6:

```css
QCheckBox#themeToggle::indicator {
    width: 36px;
    height: 18px;
    border-radius: 9px;
    background-color: {border};
}
QCheckBox#themeToggle::indicator:checked {
    background-color: {accent};
}
```

The sliding circle effect requires either a `QSS` image-based approach (using `:indicator:checked` with a shifted image) or a simple custom-painted `QWidget` with `paintEvent`. The latter is more reliable across platforms:

```python
class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 18)
        self._checked = False

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Track
        p.setBrush(QColor(accent if self._checked else border))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, 36, 18, 9, 9)
        # Thumb
        p.setBrush(QColor(bg_panel))
        x = 20 if self._checked else 2
        p.drawEllipse(x, 2, 14, 14)

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.toggled.emit(self._checked)
        self.update()
```

### 12.3 Segmented Tab Bar (Workspace Toolbar)

**Prototype:** A row of `<div>`s inside a flex container with `border-radius` and `overflow: hidden`, where the active item gets a colored background.

**Qt adaptation:** Use a `QButtonGroup` of `QPushButton`s in a `QHBoxLayout` with no spacing. Style with QSS to remove inter-button gaps and round only the outer corners:

```css
QPushButton.segmented { border: 1px solid {border}; border-radius: 0px; padding: 6px 14px; }
QPushButton.segmented:first-child { border-top-left-radius: 3px; border-bottom-left-radius: 3px; }
QPushButton.segmented:last-child { border-top-right-radius: 3px; border-bottom-right-radius: 3px; }
QPushButton.segmented:checked { background-color: {accent}; color: {textInverse}; }
```

Note: QSS `:first-child`/`:last-child` pseudo-selectors don't work in Qt. Instead, assign object names (`seg_first`, `seg_mid`, `seg_last`) and style individually, or set border-radius per-button in code after construction.

### 12.4 Display Mode Toggle (A2: SEM / All Cycles / Good Cycles)

Same pattern as 12.3 — a `QButtonGroup` of three `QPushButton`s with `setCheckable(True)` and `setExclusive(True)`. Style the checked button with accent background.

### 12.5 Inline Badges ("auto", "✓ OK", analysis type)

**Prototype:** `<span>` elements with colored background, small font, padding, and `border-radius: 2px`.

**Qt adaptation:** Use a `QLabel` with fixed QSS. Since badges are read-only, they don't need any interactivity:

```python
def make_badge(text, bg_color, text_color):
    label = QLabel(text)
    label.setStyleSheet(
        f"background-color: {bg_color}; color: {text_color}; "
        f"border-radius: 2px; padding: 1px 5px; font-size: 9px; font-weight: bold;"
    )
    label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return label
```

### 12.6 Block Navigator (Dual-Row Colored Strip)

**Prototype:** Two rows of `<div>`s using CSS flexbox with `flex: 1` and `gap: 1px`.

**Qt adaptation:** A single custom `QWidget` with `paintEvent` using `QPainter`. This is more performant and precise than trying to arrange 60+ tiny `QWidget`s in a layout. Draw colored rectangles in a loop, applying the selected-block outline via `QPainter.setPen()`. Handle `mousePressEvent` to detect which block was clicked by calculating the segment index from the click x-coordinate.

```python
def paintEvent(self, event):
    p = QPainter(self)
    n = len(self.blocks)
    seg_w = (self.width() - 2 * self.arrow_btn_width) / n
    for i, block in enumerate(self.blocks):
        x = self.arrow_btn_width + i * seg_w
        # Top row: block label color
        color = prepost_color if block.is_prepost else train_color
        p.fillRect(QRectF(x, 0, seg_w - 1, 13), QColor(color))
        # Bottom row: quality color
        q_color = good if block.good_frac >= 0.4 else warn if block.good_frac >= 0.2 else bad
        p.fillRect(QRectF(x, 14, seg_w - 1, 9), QColor(q_color))
        # Selection outline
        if i == self.selected:
            p.setPen(QPen(QColor(text_primary), 2))
            p.drawRect(QRectF(x, 0, seg_w - 1, 22))
```

### 12.7 Cycle Navigator (A2)

Same approach as 12.6 — a custom-painted `QWidget`. Simpler because it's a single row. Colors: green (good), red (saccade), blue (selected).

### 12.8 Slider with Accent Fill Track

**Prototype:** A custom slider with accent-colored fill from left to thumb position.

**Qt adaptation:** Use `QSlider` with QSS `::sub-page` and `::add-page` selectors. These are natively supported in PySide6 on all platforms:

```css
QSlider::groove:horizontal { height: 4px; background: {border}; border-radius: 2px; }
QSlider::sub-page:horizontal { background: {accent}; border-radius: 2px; }
QSlider::add-page:horizontal { background: {border}; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; height: 14px; margin: -5px 0; background: {accent}; border: 2px solid {bgPanel}; border-radius: 7px; }
```

### 12.9 Status Bar with Custom Background Color

**Prototype:** A `<div>` with accent-colored background spanning the full width.

**Qt adaptation:** `QStatusBar` with QSS background. Add custom `QLabel` widgets for each section:

```python
self.statusBar().setStyleSheet(
    f"QStatusBar {{ background-color: {accent}; color: {textInverse}; }} "
    f"QStatusBar::item {{ border: none; }}"
)
self.statusBar().addWidget(QLabel("M001 · 2026-01-15"))
self.statusBar().addPermanentWidget(QLabel("LP:40Hz · SG:30ms"))
```

### 12.10 Flex-Wrap Form Layout (W2 Metadata)

**Prototype:** `<div style="display: flex; flex-wrap: wrap; gap: 7px;">` for flowing form fields across rows.

**Qt adaptation:** Qt does not have a native flex-wrap layout. Two options:

- **Option A (simpler):** Use `QGridLayout` with manually assigned row/column positions. This is deterministic, easy to maintain, and is the approach used in the reference `test_abfconverter.py`. Each field gets a fixed grid position. This is the **recommended approach** for a solo developer.
- **Option B:** Use a `QFlowLayout` custom class (available in Qt examples). This auto-wraps but adds complexity and can behave unpredictably on resize.

### 12.11 Vertical Dividers in Parameter Bar (A1)

**Prototype:** `<div style="width: 1px; height: 32px; background: {border};">` between parameter sections.

**Qt adaptation:** Use a `QFrame` with `setFrameShape(QFrame.VLine)` and `setStyleSheet(f"color: {border};")`, or a plain `QWidget` with `setFixedWidth(1)` and a background color. The latter is more predictable:

```python
divider = QWidget()
divider.setFixedWidth(1)
divider.setFixedHeight(32)
divider.setStyleSheet(f"background-color: {border};")
```

### 12.12 Plot Legends (Top-Left Overlay)

**Prototype:** Absolutely positioned `<div>`s with small colored text inside the plot area.

**Qt adaptation:** pyqtgraph has a built-in `LegendItem` that can be added to the `PlotWidget`. Alternatively, use `pg.TextItem` elements positioned in the plot's ViewBox for more control over placement and styling:

```python
legend = pg.LegendItem(offset=(10, 10))
legend.setParentItem(plot_widget.getPlotItem())
legend.addItem(raw_curve, "raw")
legend.addItem(filtered_curve, "filtered")
```

### 12.13 Summary Table

| Prototype Component | Qt Adaptation | Complexity |
|---------------------|---------------|------------|
| Collapsible panel (▸/▾) | `QFrame` + `QPushButton.setFlat()` + `QWidget.setVisible()` | Low |
| Dark theme toggle | Custom `QWidget` with `paintEvent` (toggle switch) | Low |
| Segmented tab bar | `QButtonGroup` + `QPushButton`s with per-button QSS | Low |
| Display mode toggle (A2) | Same as segmented tab bar | Low |
| Inline badges | `QLabel` with fixed QSS | Trivial |
| Block navigator | Custom `QWidget` with `paintEvent` + `mousePressEvent` | Medium |
| Cycle navigator | Same as block navigator (simpler) | Low–Medium |
| Accent-fill slider | `QSlider` with `::sub-page` / `::handle` QSS | Low |
| Colored status bar | `QStatusBar` with QSS background | Trivial |
| Flex-wrap form layout | `QGridLayout` with manual positions | Low |
| Vertical dividers | `QWidget(fixedWidth=1)` with background QSS | Trivial |
| Plot legends | `pg.LegendItem` or `pg.TextItem` | Low |

---

## 13. Performance & Responsiveness

### 13.1 Signal Processing Debouncing

When the user drags a slider (LP cutoff, SG window, saccade threshold), `valueChanged` fires on every pixel of mouse movement. Without debouncing, this triggers the full recomputation cascade (filter → differentiate → saccade detect → metrics) dozens of times per second, freezing the UI.

**Solution:** Use a debounce timer in the ViewModel. Each setter resets the timer; computation only fires once the user pauses dragging for ~80ms.

```python
class AnalysisViewModel(QObject):
    def __init__(self):
        super().__init__()
        self._recompute_timer = QTimer()
        self._recompute_timer.setSingleShot(True)
        self._recompute_timer.setInterval(80)  # ms
        self._recompute_timer.timeout.connect(self._recompute_current_block)

    def set_lp_cutoff(self, value: float):
        self._data.params.lp_cutoff_hz = value
        self.params_changed.emit()        # Updates slider displays immediately
        self._recompute_timer.start()     # Defers heavy computation
```

This ensures slider UI updates are instant (the `params_changed` signal fires immediately to update linked sliders and the status bar), while the expensive plot recomputation is debounced.

### 13.2 Lazy A3 Computation

Recomputing metrics for all 60+ blocks on every parameter change would be extremely slow. Instead:

- On any parameter change, the ViewModel emits `all_results_stale`.
- A3's view sets an internal `_stale = True` flag.
- When the user switches to the A3 tab, the view checks `_stale`. If true, it requests a full recomputation from the ViewModel: `vm._ensure_all_results_computed()`.
- This method iterates all blocks, computes metrics, and emits per-block `block_results_updated` signals. Use a `QProgressDialog` if this takes more than ~500ms.
- After completion, `_stale` is set to `False`.

### 13.3 W1 Session Timeline Downsampling

Full-session recordings at 1000 Hz over 3800+ seconds produce ~3.8 million samples per channel. Rendering all of these in three pyqtgraph plots would be slow.

**Solution:** Downsample for display. pyqtgraph has built-in downsampling:

```python
curve = plot_widget.plot(data, pen=pen, downsample=10, downsampleMethod='peak')
```

The `'peak'` method preserves min/max envelopes, which keeps the visual appearance faithful to the full data. Keep full-resolution data in memory for computation — only the display is downsampled.

Alternatively, use `pg.PlotDataItem` with `clipToView=True` and `autoDownsample=True` for automatic LOD (level of detail) management as the user zooms.

### 13.4 Plot Update Strategy

When switching blocks in A1, avoid clearing and recreating all plot items. Instead, reuse existing `PlotDataItem` objects and call `setData()`:

```python
# Initial setup (once):
self.raw_curve = self.position_plot.plot([], pen=raw_pen)
self.filtered_curve = self.position_plot.plot([], pen=pos_pen)

# On block change (fast):
self.raw_curve.setData(new_raw_data)
self.filtered_curve.setData(new_filtered_data)
```

`setData()` is significantly faster than `clear()` + `plot()` because it reuses the existing GPU buffers.

### 13.5 Saccade Region Overlay Management

Each block may have 5–20 saccade regions. Creating and destroying `LinearRegionItem` objects on every block switch is expensive.

**Solution:** Pre-create a pool of region items (e.g., 20) at initialization, all hidden. On each block update, show and reposition the needed ones, hide the rest:

```python
# Init (once):
self.saccade_regions = []
for _ in range(20):
    region = pg.LinearRegionItem(brush=saccade_brush, movable=False)
    region.setVisible(False)
    self.plot.addItem(region)
    self.saccade_regions.append(region)

# On block update:
for i, region in enumerate(self.saccade_regions):
    if i < len(saccade_intervals):
        region.setRegion(saccade_intervals[i])
        region.setVisible(True)
    else:
        region.setVisible(False)
```

### 13.6 Thread Safety

All signal processing computation (filtering, differentiation, saccade detection) runs synchronously in the ViewModel on the main thread. For single-block recomputation with ~60,000 samples (60 seconds at 1000 Hz), this typically completes in <50ms on modern hardware, which is imperceptible.

If profiling shows that certain operations (e.g., wavelet denoising, or the full A3 all-block recomputation) exceed ~200ms, move them to a `QThread` or use `QThreadPool` with a `QRunnable`. Emit the result signals back on the main thread via `QMetaObject.invokeMethod` or a signal from the worker.

For the initial implementation, keep everything synchronous and only add threading if profiling shows it's needed. Premature threading adds significant complexity for a solo developer.

---

## 14. Maintainability for a Solo Developer

### 14.1 Guiding Principles

This application is developed, maintained, and troubleshot by a single engineer. Every architectural decision should optimize for:

- **Readability over cleverness.** Prefer explicit, verbose code over compact abstractions. A future developer (or the same developer in 6 months) should understand any file without needing to trace through multiple layers of inheritance.
- **Flat over nested.** Avoid deep class hierarchies. Prefer composition (a screen widget *has* a block navigator) over inheritance (a screen widget *is* a specialized navigator container).
- **Locality.** Keep related code together. Each screen file (`a1_signal_explorer.py`) should be self-contained — all layout, signal connections, and refresh methods for that screen live in one file.
- **Minimal abstraction.** Only abstract when the same code would otherwise appear in 3+ places. Shared components (block navigator, parameter slider) are justified. A generic "AnalysisScreenBase" class is probably not.

### 14.2 File Size Guideline

Keep individual files under ~400 lines. If a screen file grows beyond this, extract clearly-bounded sub-components (e.g., the calibration section of A1 can become its own `CalibrationPanel` class in the same file or a separate one). The reference `test_abfconverter.py` is ~860 lines for the entire application — individual screen files in this application should be smaller since the logic lives in the ViewModel.

### 14.3 Naming Conventions

- **Files:** `snake_case.py` (e.g., `a1_signal_explorer.py`, `block_navigator.py`)
- **Classes:** `PascalCase` (e.g., `SignalExplorerScreen`, `BlockNavigator`, `AnalysisViewModel`)
- **Signals:** `snake_case` verbs in past tense (e.g., `block_selected`, `params_changed`, `file_loaded`)
- **Private methods:** Prefix with `_` (e.g., `_recompute_current_block`, `_apply_position_filter`)
- **Guard flags:** `_updating_view` (consistent with reference)

### 14.4 Debugging Strategy

The MVVM pattern makes debugging straightforward because state changes flow in one direction:

1. **UI not updating?** Check that the ViewModel is emitting the correct signal. Add a `print()` or `logging.debug()` in the ViewModel method.
2. **Signal emitted but View not responding?** Check that the View's `connect_signals()` method connects to the signal, and that the refresh method is correct.
3. **Wrong values displayed?** Check the ViewModel's `@property` accessors and the Model's data fields.
4. **Signal loop?** Check that the `_updating_view` guard is in place in the relevant View class.

Add a `--debug` command-line flag that enables verbose logging of all ViewModel signal emissions:

```python
class AnalysisViewModel(QObject):
    def _emit(self, signal, *args):
        """Wrapper for debugging signal emissions."""
        if self._debug:
            print(f"[VM] {signal.signal} emitted with args={args}")
        signal.emit(*args)
```

### 14.5 Testing Strategy

- **Model tests:** Pure dataclass validation. Test `MetadataFields.count_remaining()`, `is_complete()`, default values.
- **Analysis function tests:** Test `butterworth_lowpass()`, `svt_detect()`, `savitzky_golay_differentiate()` etc. with known synthetic inputs and expected outputs. These are pure functions with no Qt dependency — standard pytest.
- **ViewModel tests:** Instantiate `AnalysisViewModel()` (requires a `QApplication` instance but no visible window). Call methods, assert signal emissions using `QSignalSpy` or a simple mock callback, verify property values.
- **View tests:** Not recommended for a solo developer. Visual correctness is verified by using the application. Focus testing effort on the Model and ViewModel layers where bugs are hardest to find visually.

### 14.6 Dependencies

Keep the dependency list minimal. This improves installation reliability across lab computers and reduces maintenance burden.

**Required:**
- `Python >= 3.10`
- `PySide6` (Qt 6 bindings)
- `pyqtgraph` (plotting)
- `numpy` (signal processing)
- `scipy` (filters, signal processing)
- `openpyxl` (Excel export)
- `matplotlib` (PDF figure export — use `matplotlib.backends.backend_pdf`)

**Optional:**
- `PyWavelets` (pywt) — only if Wavelet denoising is used
- `hdf5storage` or `scipy.io` — for `.mat` export

Avoid adding dependencies for features that can be implemented in a few lines of code (e.g., don't add a JSON schema library just for metadata validation — `MetadataFields.count_remaining()` is sufficient).

### 14.7 Configuration & Defaults

Store all default parameter values in one place — the `AnalysisParams` dataclass. This means:

- Defaults are defined once, not scattered across UI code
- `reset_params_to_defaults()` simply creates a new `AnalysisParams()` instance
- Adding a new parameter in the future requires editing one dataclass, one ViewModel setter, and the relevant View widgets — nothing else

Similarly, store all analysis-type-to-default-labels mappings in a single dictionary:

```python
ANALYSIS_TYPE_LABELS = {
    "Standard VOR": {"pretest": "VORD", "training": "VOR", "posttest": "VORD"},
    "Standard OKR": {"pretest": "VORD", "training": "OKR", "posttest": "VORD"},
    "NDD":          {"pretest": "VORD", "training": "OKR", "posttest": "VORD"},
    "VOR Single-Trial Opto": {"pretest": "VORD", "training": "VOR", "posttest": "VORD"},
}
```

### 14.8 Version Control

Since this replaces MATLAB `.mlapp` files (which are binary and impossible to diff), the PySide6 codebase is entirely text-based. Every file is diffable, searchable, and greppable in any IDE.

Recommended commit granularity for a solo developer:
- One commit per screen implemented (e.g., "Add W1 Load & Review screen")
- One commit per feature (e.g., "Add wavelet denoising filter method")
- One commit per bug fix with a descriptive message

### 14.9 When to Refactor

As a solo developer, resist the urge to preemptively refactor. Only refactor when:

- The same block of code (10+ lines) appears in 3 or more places → extract to a shared function or widget
- A single file exceeds ~400 lines → split into sub-components
- A ViewModel method exceeds ~30 lines → extract helper methods
- A new analysis type requires copy-pasting an entire screen → create a shared base (but only at this point, not before)
