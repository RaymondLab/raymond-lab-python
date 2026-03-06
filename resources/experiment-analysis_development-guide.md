# Behavioral Experiment Analysis GUI — Development Guide

**Prototype reference:** `experiment-analysis_prototype.jsx`
**Target implementation:** Python 3.10+, PySide6, pyqtgraph
**Target platforms:** Windows 11 (primary), macOS (secondary)

---

## Table of Contents

1. [Application Overview](#1-application-overview)
2. [Navigation Architecture](#2-navigation-architecture)
3. [Application State](#3-application-state)
4. [Design System](#4-design-system)
5. [Screen Specifications](#5-screen-specifications)
6. [Shared Components](#6-shared-components)
7. [Data Flow](#7-data-flow)
8. [PySide6 Implementation Notes](#8-pyside6-implementation-notes)

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

The application has two phases:

### Phase A — Setup Wizard (2 steps, linear)

```
W1: Load & Review  ──Next──►  W2: Metadata & Output  ──Start Analysis──►  [Workspace]
                    ◄──Back──
```

- W1 and W2 are sequential. "Next" and "Back" buttons navigate between them.
- "Next" on W1 is disabled until a file is loaded AND an analysis type is selected.
- "Start Analysis" on W2 is disabled until all required metadata fields have valid inputs.
- Clicking "Start Analysis" triggers a processing phase (show a progress dialog/spinner) and then transitions to the workspace.

### Phase B — Analysis Workspace (3 tabs, non-linear)

```
A1: Signal Explorer  ◄──►  A2: Block Analysis  ◄──►  A3: Results Summary
         ▲                          ▲                          ▲
         └──────────────────────────┼──────────────────────────┘
                                    │
                               S1: Settings Panel (slide-out drawer, accessible from any tab)
```

- The three workspace tabs (A1, A2, A3) are freely navigable via a tab bar in the workspace toolbar.
- S1 is a slide-out panel toggled by a gear icon button. It overlays the right side of the content area without replacing the active tab.
- A "↺ New Analysis" button in the workspace toolbar returns to W1 after a confirmation dialog. This resets all workspace state.

### Title Bar

- Always visible at the top of the window.
- Displays the application name: **"Behavioral Experiment Analysis"**
- Shows contextual info: current wizard step (e.g., "— Step 1 of 2: Load & Review") or current workspace tab (e.g., "— Signal Explorer").
- In PySide6: use `QMainWindow.setWindowTitle()` to update dynamically.

### Workspace Toolbar

- Only visible when in the workspace phase (not during wizard).
- **Left side:** Mouse ID (bold, 14px), session date (monospace, 11px), analysis type badge.
- **Right side:** "↺ New Analysis" button, tab bar (Signal Explorer / Block Analysis / Results Summary), gear icon button for settings.

### Status Bar

- Only visible when in the workspace phase.
- **Background:** Accent color (`#3E6E8C` light / `#508CB0` dark).
- **Left:** "M001 · 2026-01-15" (bold white), "Standard VOR" (white, 70% opacity, monospace).
- **Right:** Current parameter values live-updated (e.g., "LP:40Hz · SG:30ms · Sac:50°/s"), session info ("1000Hz · 62 blocks").
- In PySide6: use `QStatusBar` with `QLabel` widgets, styled with QSS.

---

## 3. Application State

All state should be managed centrally (e.g., in the `QMainWindow` subclass or a dedicated state object) so that changes propagate across tabs.

### Navigation State

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `phase` | enum | `"wizard"` | `"wizard"` or `"workspace"` |
| `wizard_step` | int | `1` | `1` (W1) or `2` (W2) |
| `workspace_tab` | str | `"A1"` | `"A1"`, `"A2"`, or `"A3"` |
| `settings_open` | bool | `False` | Whether the S1 panel is visible |

### Data State

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `file_loaded` | bool | `False` | Whether an experiment file has been loaded |
| `file_path` | str | `""` | Path to the loaded experiment file |
| `analysis_type` | str | `"Standard VOR"` | Selected analysis type |
| `calibration_loaded` | bool | `False` | Whether calibration has been applied |
| `calibration_source` | str | `"file"` | `"file"` or `"manual"` |
| `scale_ch1` | float | `None` | Calibration scaling factor for channel 1 |
| `scale_ch2` | float | `None` | Calibration scaling factor for channel 2 |
| `active_channel` | str | `"Auto"` | `"Auto"`, `"Ch1"`, or `"Ch2"` |
| `selected_block` | int | `0` | Currently selected block index (0-based), synced across A1 and A2 |
| `selected_cycle` | int | `0` | Currently selected cycle index in A2 (0-based) |
| `display_mode` | str | `"SEM"` | A2 display mode: `"SEM"`, `"All Cycles"`, or `"Good Cycles"` |

### Analysis Parameters (synced between A1 sliders and S1 panel)

| Variable | Type | Default | Range | Description |
|----------|------|---------|-------|-------------|
| `filter_method` | str | `"Butterworth"` | Dropdown | Position filter method |
| `lp_cutoff_hz` | float | `40` | ~1–100 | Low-pass filter cutoff frequency (Hz) |
| `sg_window_ms` | float | `30` | ~3–100 | Savitzky-Golay differentiation window size (ms) |
| `saccade_method` | str | `"SVT"` | Dropdown | Saccade detection algorithm |
| `saccade_threshold` | float | `50` | ~5–200 | Saccade detection threshold (deg/s) |
| `saccade_min_dur_ms` | float | `10` | 1–50 | Minimum saccade duration (ms) |
| `saccade_padding_ms` | float | `5` | 0–20 | Padding around detected saccades (ms) |

### Appearance State

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `dark_mode` | bool | `False` | Whether dark theme is active |

### Metadata State (W2 form fields)

All metadata is stored in a dictionary that maps to `_metadata.json` fields. Required fields are marked with `*`. Fields that can be auto-populated from the loaded file are marked with `(auto)`.

| Field | Required | Auto | Group |
|-------|----------|------|-------|
| `subject_id` | * | (auto) | Subject |
| `species` | | (auto) | Subject |
| `strain` | * | | Subject |
| `sex` | * | | Subject |
| `age` | | | Subject |
| `weight_g` | | | Subject |
| `genotype` | * | | Subject |
| `session_date` | * | (auto) | Session |
| `session_start_time` | * | (auto) | Session |
| `experimenter` | * | | Session |
| `lab` | | (auto) | Session |
| `institution` | | (auto) | Session |
| `experiment_description` | | | Session |
| `cohort` | * | | Experiment |
| `subject_condition` | * | | Experiment |
| `task_condition` | * | (auto) | Experiment |
| `stimulus_frequency_hz` | * | (auto) | Experiment |
| `magnet_eye` | | | Experiment |
| `rig_id` | | | Device |
| `recording_system` | | (auto) | Device |
| `eye_tracking_system` | | (auto) | Device |
| `sampling_rate_hz` | * | (auto) | Device |

---

## 4. Design System

### 4.1 Color Palette — Light Theme (Default)

**UI Chrome (accent: steel blue — avoids data red/blue/green):**

| Token | Hex | Usage |
|-------|-----|-------|
| `bgApp` | `#E8ECF0` | Main application background (behind all panels) |
| `bgPanel` | `#FFFFFF` | Card/panel/input backgrounds |
| `bgPanelAlt` | `#EFF2F6` | Alternate backgrounds (table headers, summary bars) |
| `bgInput` | `#FFFFFF` | Input field backgrounds |
| `bgTopbar` | `#263040` | Title bar background |
| `bgTabActive` | `#3E6E8C` | Active tab and primary button background |
| `bgTabInactive` | `#324050` | Inactive tab background (in title bar context) |
| `bgCalibration` | `#EFF4F8` | Calibration section background |
| `bgParamBar` | `#F3F6F9` | Parameter control bar background |
| `bgPlot` | `#F8FAFB` | pyqtgraph PlotWidget background |
| `border` | `#CDD4DC` | Standard borders |
| `borderLight` | `#DFE4EA` | Light borders (between table rows, inner dividers) |
| `borderFocus` | `#3E6E8C` | Focused input border |
| `accent` | `#3E6E8C` | Primary interactive color (buttons, tabs, sliders, status bar) |
| `accentDark` | `#2E5A74` | Primary button border, hover states |
| `accentLight` | `#E0EDF5` | Accent background (badges, settings button active state) |
| `accentText` | `#2E5A74` | Accent-colored text |

**Text:**

| Token | Hex | Usage |
|-------|-----|-------|
| `textPrimary` | `#1A2230` | Headings, values, primary content |
| `textSecondary` | `#4E5A6A` | Labels, section titles, table headers |
| `textTertiary` | `#8490A0` | Hints, placeholders, disabled text |
| `textInverse` | `#FFFFFF` | Text on accent-colored backgrounds |
| `textOnTopbar` | `#A8B4C2` | Secondary text on the dark title bar |

**Signal Trace Colors (for pyqtgraph pen colors):**

| Token | Hex | Usage |
|-------|-----|-------|
| `dataPosition` | `#E8690B` | Filtered eye position trace (orange) |
| `dataVelocity` | `#2563EB` | Filtered eye velocity trace (blue) |
| `dataSaccade` | `#D42A2A` | Saccade segments and region shading (red) |
| `dataStimulus` | `#8490A0` | Stimulus overlay, dashed line (gray) |
| `dataFit` | `#1A2230` | Sinusoidal fit line (dark/black) |
| `dataRaw` | `#BCC4CE` | Raw unfiltered traces (light gray) |
| `dataSem` | `#D6E4F7` | ±SEM shaded fill region (light blue) |

**Block & Quality Colors:**

| Token | Hex | Usage |
|-------|-----|-------|
| `blockPrepost` | `#0F8A5F` | Pre-test and post-test block labels and markers |
| `blockPrepostBg` | `#D6F0E4` | Pre/post block background fills, "auto" badges |
| `blockTrain` | `#CF2C4A` | Training block labels and markers |
| `blockTrainBg` | `#FAE0E5` | Training block background fills |
| `qualGood` | `#1A9E50` | ≥40% good cycles (green) |
| `qualWarn` | `#D4930D` | 20–40% good cycles (amber) |
| `qualBad` | `#CF2C2C` | <20% good cycles (red) |
| `qualSelected` | `#2D5FD4` | Currently selected cycle in A2 (indigo) |

### 4.2 Color Palette — Dark Theme

The dark theme follows the same token structure with values shifted for dark backgrounds:

| Token | Light | Dark |
|-------|-------|------|
| `bgApp` | `#E8ECF0` | `#141A22` |
| `bgPanel` | `#FFFFFF` | `#1C2430` |
| `bgPanelAlt` | `#EFF2F6` | `#18202A` |
| `bgInput` | `#FFFFFF` | `#243040` |
| `bgTopbar` | `#263040` | `#0E1418` |
| `accent` | `#3E6E8C` | `#508CB0` |
| `bgPlot` | `#F8FAFB` | `#18202A` |
| `border` | `#CDD4DC` | `#304050` |
| `textPrimary` | `#1A2230` | `#DEE4EA` |
| `textSecondary` | `#4E5A6A` | `#90A0B0` |
| `textTertiary` | `#8490A0` | `#607080` |
| `dataPosition` | `#E8690B` | `#F0923C` |
| `dataVelocity` | `#2563EB` | `#6BA3F5` |
| `dataSaccade` | `#D42A2A` | `#F06B6B` |
| `blockPrepost` | `#0F8A5F` | `#3BD48A` |
| `blockTrain` | `#CF2C4A` | `#F27088` |
| `qualGood` | `#1A9E50` | `#2ED06A` |

### 4.3 Typography

| Role | Font Family | Size | Weight |
|------|------------|------|--------|
| UI labels, buttons, menus | Segoe UI (Win) / SF Pro Text (Mac) | 11–12px | 400–600 |
| Section headers | Segoe UI | 10–11px | 700, UPPERCASE, letter-spacing 0.06em |
| Numeric data, file paths, axis labels | Consolas (Win) / SF Mono (Mac) | 10–12px | 400–700 |
| Title bar | Segoe UI | 12px | 700 |
| Plot titles | Segoe UI | 10px | 600 |

### 4.4 Spacing & Layout

| Element | Value |
|---------|-------|
| Border radius (all widgets) | 3px |
| Padding (buttons, standard) | 5px 14px |
| Padding (buttons, small) | 3px 10px |
| Padding (inputs) | 4px 7px |
| Padding (panels/cards) | 8–12px |
| Gap (tight, label-to-input) | 2–3px |
| Gap (components in a row) | 6–8px |
| Gap (sections) | 8–12px |
| Slider track height | 4px |
| Slider thumb diameter | 14px |

### 4.5 Shadows

No box shadows. All depth is achieved through borders and background color differences. This is a PySide6 constraint (QSS does not support `box-shadow`).

---

## 5. Screen Specifications

### 5.1 W1: Load & Review

**Purpose:** Load experiment file, review session/block structure, select analysis type.

**Layout (top to bottom):**

1. **Control bar** (`QGroupBox` or `QFrame` with `bgPanel` background, border)
   - Row: [Browse `QPushButton`] [File path `QLineEdit` (read-only, stretches)] [Analysis Type `QComboBox` (w=155)] [Next → `QPushButton` (primary, disabled until file loaded)]
   - Second row (visible after file loaded): file metadata in monospace — Channels, Size, Date, Format

2. **Session summary bar** (`QFrame` with `bgPanelAlt` background)
   - Horizontal row of labeled stats: Duration, Blocks, Schema, Pre/Post (green), Training (red), Freq, Sample Rate

3. **Main area** (`QSplitter` horizontal)
   - **Left: Timeline plots** (`QVBoxLayout` with 3 plot sections)
     - Each plot section contains:
       - A header row: "CHANNEL:" label + `QComboBox` (for channel selection, defaults: `htvel`, `hhvel`) + description text
       - A `pyqtgraph.PlotWidget` that fills the remaining vertical space
       - Block regions drawn as colored `LinearRegionItem` or `FillBetweenItem` overlays (green for pre/post, red/pink for training)
       - Signal trace as a `PlotDataItem`
     - Third plot is fixed to "Raw Eye Position — UNCALIBRATED" showing two traces (hepos1 in orange, hepos2 in blue) overlaid
   - **Right: Block table** (w=195, `QTableWidget` or `QTableView`)
     - Header: #, Label, Hz, ✓
     - Label column is an editable `QComboBox` delegate, color-coded (green for VORD, red for OKR)
     - ✓ column is a `QCheckBox` delegate for excluding blocks

4. **Empty state** (when no file loaded): centered placeholder with folder icon and "Click Browse to load an experiment file" text

**Interactions:**
- "Browse" opens a `QFileDialog` for `.smr`, `.smrx`, `.mat` files
- Loading a file: parse channels, detect block boundaries, populate session summary, populate block table with default labels from selected analysis type, render timeline plots
- Changing analysis type repopulates block table labels
- Clicking a block table row highlights that block in the timeline (scroll to + highlight)
- "Next →" navigates to W2

---

### 5.2 W2: Metadata & Output

**Purpose:** Fill NWB/BIDS metadata, configure save location, launch analysis.

**Layout (top to bottom):**

1. **Control bar** (`QFrame`, `bgPanel` background) — **at the top**
   - Row: [← Back `QPushButton`] [SAVE TO: label] [Browse `QPushButton`] [Path `QLineEdit`] ... [remaining count `QLabel` in red] [Start Analysis `QPushButton` (primary, disabled until all required fields filled)]

2. **Metadata form** (scrollable `QScrollArea` containing `QVBoxLayout`)
   - Four `QGroupBox` sections, each with a title and a flow layout of form fields:
     - **Subject Information:** Mouse ID*, Species, Strain*, Sex*, Age, Weight, Genotype*
     - **Session Information:** Date*, Start Time*, Experimenter*, Lab, Institution, Description
     - **Experiment Details:** Cohort*, Condition*, Task*, Stim Freq*, Magnet Eye, Notes
     - **Device Information:** Rig ID, Recording System, Eye Tracking, Sample Rate*
   - Required fields (*) show a red asterisk in the label
   - Auto-populated fields show a green "auto" badge (`QLabel` styled as a badge)
   - As fields are filled, the remaining-fields counter updates in real time
   - When count reaches 0, "Start Analysis" button enables and the counter text changes to green "✓ All fields complete"

**Interactions:**
- "← Back" returns to W1 (preserves all metadata entries)
- "Start Analysis" triggers:
  1. Generate and save `_metadata.json`
  2. Show a modal progress dialog ("Processing... Segmenting blocks, preparing workspace...")
  3. Transition to workspace phase, A1 tab

---

### 5.3 A1: Signal Explorer

**Purpose:** Manage calibration, explore signals per-block, tune parameters in real-time.

**Layout (top to bottom):**

1. **Calibration section** (collapsible `QGroupBox`, `bgCalibration` background, accent-tinted border)
   - **Collapsed state:** Single row showing ▸ Calibration label, summary values (Ch1: .0412, Active: Ch1), green "✓ OK" badge, Load File / Manual buttons
   - **Expanded state (▾):** Additional row with Browse button, file path input, all three scaling values displayed, sanity badge, Apply button
   - Toggle between states by clicking the header
   - Sanity check: if scaling values are negative, zero, or outside a configurable "typical range", show amber warning badge instead of green

2. **Block navigator** (shared component, see Section 6.1)

3. **Signal plots** (`QSplitter` horizontal, two `pyqtgraph.PlotWidget` instances)
   - **Left: Eye Position plot**
     - Traces: raw (light gray), filtered (orange `#E8690B`), saccade segments (red)
     - Overlays: saccade region shading (light red fill)
     - Legend: top-left corner
   - **Right: Eye Velocity plot**
     - Traces: stimulus (gray, dashed), raw (light gray), filtered (blue `#2563EB`), saccade segments (red)
     - Overlays: saccade region shading (light red fill)
     - Legend: top-left corner
   - Both plots share linked x-axes (`ViewBox.setXLink()`)
   - Selecting a different block in the navigator re-renders both plots with that block's data

4. **Parameter control bar** (`QFrame`, `bgParamBar` background)
   - Three sections separated by vertical dividers (`QFrame` with fixed width 1px, `border` color):
     - **Position Filter:** Section label + Method `QComboBox` (default "Butterworth") + LP Cutoff `QSlider` with `QSpinBox`
       - When method is "Butterworth": show LP Cutoff slider
       - When method is "Wavelet": replace slider with Level `QComboBox` (4–7), Wavelet `QComboBox` (sym4/sym6), Method `QComboBox` (BlockJS/Bayes/SURE)
     - **Differentiation:** Section label + SG Window `QSlider` with `QSpinBox`
     - **Saccade Detection:** Section label + Method `QComboBox` (SVT/STD/MAD) + Threshold `QSlider` with `QSpinBox`

**Real-time parameter update behavior:**
- Changing any slider or parameter value triggers a re-computation on the currently displayed block:
  1. Re-apply position filter → update filtered eye position trace
  2. Re-derive velocity via SG differentiation → update filtered eye velocity trace
  3. Re-run saccade detection → update saccade segments and region overlays
  4. Update the good-cycle quality indicator in the block navigator for the current block
- Debounce slider changes (e.g., 50–100ms) to avoid excessive recomputation during rapid dragging

---

### 5.4 A2: Block Analysis

**Purpose:** View cycle-averaged analysis results for a single selected block.

**Layout (top to bottom):**

1. **Block navigator** (same shared component as A1, synced `selected_block`)

2. **Cycle navigator + display mode** (horizontal row)
   - **Cycle label:** "CYCLES:" section label
   - **Cycle strip:** Horizontal row of clickable segments, one per cycle in the selected block
     - Green = good cycle, Red = saccade-detected cycle, Blue = currently selected cycle
     - Selected cycle has a 2px solid outline in `textPrimary` color
   - **Legend:** good / saccade / selected
   - **Display mode toggle:** Three-way segmented control (`QButtonGroup` of `QPushButton`s)
     - **SEM** (default): Show cycle-average ± SEM shaded band
     - **All Cycles**: Show all individual cycle traces as semi-transparent lines; selected cycle highlighted
     - **Good Cycles**: Show only non-saccade individual cycles; selected cycle highlighted

3. **Main area** (`QSplitter` horizontal)
   - **Left: Cycle-average plot** (`pyqtgraph.PlotWidget`, flex=1)
     - Traces (SEM mode): stimulus (gray dashed), average eye velocity (blue, bold), sinusoidal fit (dark/black), ±SEM fill region (light blue)
     - Traces (All/Good Cycles mode): individual cycle traces (thin, semi-transparent blue, ~20% opacity), selected cycle trace (bold blue, 100% opacity), stimulus (gray dashed), average (blue, bold), fit (dark)
     - Title: "Block N (N of Total): LABEL"
   - **Right: Block Metrics card** (w=168, `QGroupBox`)
     - Key-value pairs in two columns:
       - Gain, Eye Amp ± SEM, Eye Phase ± SEM, Stim Amp, Freq, Good Cycles (N/Total), Var Residual
     - Values in monospace font, right-aligned

---

### 5.5 A3: Results Summary

**Purpose:** Cross-block summary for publication. Gain time course, results table, export.

**Layout (top to bottom):**

1. **Y-axis metric selector** (right-aligned `QComboBox`, options: Gain / Eye Amplitude / Eye Phase / Good Cycle Fraction / Variance Residual)

2. **Gain time course plot** (`pyqtgraph.PlotWidget`, fixed height ~175px)
   - Scatter plot: block number (x-axis) vs. selected metric (y-axis)
   - Pre/post-test blocks: larger green markers (`#0F8A5F`)
   - Training blocks: smaller red markers (`#CF2C4A`, ~55% opacity)
   - Grid lines in `borderLight` color
   - Legend: top-right, "Pre/Post" and "Training"

3. **Results data table** (`QTableView` with `QAbstractTableModel`, flex=1, scrollable)
   - Columns: #, Label, Hz, Start (s), End (s), Dur (s), Eye Amp ± SEM, Eye Phase ± SEM, Stim Amp, Gain, Good Cyc, VarRes
   - Label column color-coded (green for pre/post, red for training)
   - Numeric columns in monospace font
   - Clicking a row selects that block in the shared `selected_block` state (and therefore in A1/A2)

4. **Export bar** (right-aligned row of buttons)
   - "Excel" (`QPushButton`) — exports `.xlsx` with results table + metadata
   - "Figures" (`QPushButton`) — exports `.pdf` figures (set determined by analysis type)
   - "Workspace" (`QPushButton`) — exports `.mat` with full analysis workspace
   - "Export All" (`QPushButton`, primary) — runs all three exports

---

### 5.6 S1: Settings Panel

**Purpose:** Centralized parameter controls accessible from any workspace tab.

**Layout:** Slide-out panel on the right side of the content area.

**Structure:**
- **Width:** 265px
- **Left border:** 2px solid `border` color
- **Background:** `bgPanel`
- **Header:** "⚙ Settings" title + ✕ close button, separated by bottom border
- **Content:** Scrollable area with collapsible sections:

| Section | Controls |
|---------|----------|
| **Position Filter** | Method `QComboBox` (Butterworth / Wavelet / ...) + method-specific params (LP Cutoff slider for Butterworth; Level/Wavelet/Method dropdowns for Wavelet) |
| **Differentiation** | SG Window slider with value display |
| **Saccade Detection** | Method `QComboBox` (SVT / STD / MAD / ...) + Threshold slider + Min Duration input + Padding input |
| **Eye Channel** | Active Channel `QComboBox` (Auto / Ch1 / Ch2) |
| **Appearance** | Dark Theme toggle (`QCheckBox` or custom toggle switch) |

- **Footer:** "Reset to Defaults" button, separated by top border

**Synchronization:** All parameter controls in S1 are bidirectionally synced with the corresponding controls in A1's parameter bar. Changing a slider in A1 updates S1, and vice versa. Use Qt signals/slots to connect them to the same underlying state.

---

## 6. Shared Components

### 6.1 Block Navigator

Used in A1 and A2 (synced via shared `selected_block` state).

**Structure:** A horizontal widget with the following children:

```
[◂ QPushButton] [dual-row block strip] [▸ QPushButton] [label area]
```

**Dual-row block strip (custom QWidget with paintEvent):**
- **Top row (height 13px):** One segment per block, color-coded by label type:
  - Pre/post-test blocks: `blockPrepost` color
  - Training blocks: `blockTrain` color
  - Selected block: full opacity + 2px outline in `textPrimary`
  - Unselected blocks: reduced opacity (40–50%)
- **Bottom row (height 9px):** Same segments, color-coded by good-cycle fraction:
  - ≥40% good cycles: `qualGood` (green)
  - 20–40% good cycles: `qualWarn` (amber)
  - <20% good cycles: `qualBad` (red)
  - Selected block: higher opacity + 2px outline

**Label area:** Block number ("Block N / Total") in bold, block label and type in tertiary color. Below: legend for quality colors.

**Interactions:**
- Click a segment to select that block
- ◂ / ▸ buttons decrement/increment `selected_block`
- Selection change emits a signal that triggers plot updates in A1 and A2

### 6.2 Cycle Navigator (A2 only)

**Structure:** Horizontal row of clickable segments, one per cycle.

- Good cycles: `qualGood` color
- Saccade-detected cycles: `qualBad` color
- Selected cycle: `qualSelected` color + 2px outline
- Unselected cycles: 55% opacity

**Interactions:**
- Click a segment to select that cycle
- In "All Cycles" or "Good Cycles" display mode, the selected cycle's trace is highlighted

### 6.3 Parameter Slider

A composite widget used in A1's parameter bar and S1's settings panel.

**Structure:**
```
[Label (right-aligned, 72px min)] [QSlider (horizontal, stretches)] [Value display (monospace, 52px min)]
```

**Styling (QSS):**
- Groove: 4px height, `border` color background, 2px border-radius
- Filled portion: `accent` color
- Handle: 14px diameter circle, `accent` color, 2px `bgPanel` border

---

## 7. Data Flow

```
[Experiment .smr file]
        │
        ▼
    W1: Parse channels → detect block boundaries → extract stimulus params
        │
        ▼
    W2: Merge file metadata with user entries → save _metadata.json
        │
        ▼
    A1: Apply calibration (file or manual) → filter eye position
        → differentiate via SG → detect saccades
        │                              │
        │   [Parameters adjustable      │
        │    in real-time via sliders]   │
        │                              ▼
        ├──────────────────────► A2: Segment block into cycles
        │                           → compute cycle averages
        │                           → sinusoidal fit → block metrics
        │                              │
        │                              ▼
        └──────────────────────► A3: Aggregate all block metrics
                                    → populate results table
                                    → render gain time course
                                       │
                                       ▼
                                  [Export: .xlsx + .pdf + .mat]
```

**When a parameter changes (in A1 or S1):**
1. Re-filter the position signal for the current block
2. Re-derive velocity via SG differentiation
3. Re-run saccade detection
4. Update signal plots in A1
5. Re-compute cycle averages and metrics for the current block in A2
6. Update the good-cycle quality indicators in the block navigator
7. Note: Full re-computation across all blocks for A3 can be deferred until the user switches to A3 (lazy computation)

---

## 8. PySide6 Implementation Notes

### 8.1 Recommended Widget Mapping

| Prototype Component | PySide6 Widget |
|---------------------|----------------|
| Application window | `QMainWindow` |
| Wizard / workspace switching | `QStackedWidget` as central widget |
| Wizard steps | Two `QWidget` pages in a `QStackedWidget` |
| Workspace tabs | `QTabWidget` or manual `QStackedWidget` + custom tab bar |
| Settings panel | `QDockWidget` (right-docked, no title bar float) or manual `QWidget` in a `QHBoxLayout` |
| Signal plots | `pyqtgraph.PlotWidget` |
| Block navigator | Custom `QWidget` with `paintEvent` |
| Cycle navigator | Custom `QWidget` with `paintEvent` |
| Block table (W1) | `QTableView` + `QStandardItemModel` with `QComboBox` delegates |
| Results table (A3) | `QTableView` + custom `QAbstractTableModel` |
| Metadata form (W2) | `QScrollArea` containing `QGroupBox` sections with `QFormLayout` or `QFlowLayout` |
| Parameter sliders | `QSlider` + `QSpinBox`/`QDoubleSpinBox` linked via signals |
| Status bar | `QStatusBar` with custom `QLabel` widgets |
| Loading dialog | `QProgressDialog` or custom `QDialog` |
| Confirmation dialogs | `QMessageBox` |
| File browsers | `QFileDialog` |

### 8.2 QSS Theming Approach

Define all theme colors as Python dictionaries (mirroring the token tables above). Apply a global stylesheet at the `QApplication` level that references these values. When switching themes, regenerate and reapply the stylesheet.

Example QSS structure:
```css
QMainWindow { background-color: {bgApp}; }
QGroupBox { background-color: {bgPanel}; border: 1px solid {border}; border-radius: 3px; }
QPushButton { background-color: {bgPanel}; border: 1px solid {border}; border-radius: 3px; padding: 5px 14px; color: {textSecondary}; font-weight: 600; }
QPushButton:primary { background-color: {accent}; border: 1px solid {accentDark}; color: {textInverse}; }
QPushButton:disabled { opacity: 0.4; }
QLineEdit { background-color: {bgInput}; border: 1px solid {border}; border-radius: 3px; padding: 4px 7px; }
QLineEdit:focus { border-color: {borderFocus}; }
QComboBox { background-color: {bgInput}; border: 1px solid {border}; border-radius: 3px; padding: 4px 7px; }
QSlider::groove:horizontal { height: 4px; background: {border}; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; height: 14px; margin: -5px 0; background: {accent}; border: 2px solid {bgPanel}; border-radius: 7px; }
QSlider::sub-page:horizontal { background: {accent}; border-radius: 2px; }
```

### 8.3 pyqtgraph Configuration

Configure all `PlotWidget` instances with:
```python
pw.setBackground(theme['bgPlot'])
pw.getAxis('bottom').setPen(pg.mkPen(theme['border']))
pw.getAxis('left').setPen(pg.mkPen(theme['border']))
pw.getAxis('bottom').setTextPen(pg.mkPen(theme['textTertiary']))
pw.getAxis('left').setTextPen(pg.mkPen(theme['textTertiary']))
pw.showGrid(x=True, y=True, alpha=0.1)
```

Signal traces use `pg.mkPen(color, width)`:
- Raw: `mkPen(theme['dataRaw'], width=1)`
- Filtered position: `mkPen(theme['dataPosition'], width=2)`
- Filtered velocity: `mkPen(theme['dataVelocity'], width=2)`
- Saccade segments: `mkPen(theme['dataSaccade'], width=1.5)`
- Stimulus: `mkPen(theme['dataStimulus'], width=1, style=Qt.DashLine)`
- Fit: `mkPen(theme['dataFit'], width=1.5)`

Saccade region overlays: use `pg.LinearRegionItem` or `pg.FillBetweenItem` with the saccade color at ~6–8% opacity.

Block region overlays in W1: use `pg.LinearRegionItem` with `blockPrepost` or `blockTrain` colors at ~15–20% opacity, set to immovable.

### 8.4 Signal/Slot Architecture

Key connections:

```
# Parameter changes propagate everywhere
lp_cutoff_slider.valueChanged → recompute_current_block()
sg_window_slider.valueChanged → recompute_current_block()
saccade_threshold_slider.valueChanged → recompute_current_block()

# Block selection syncs across tabs
block_navigator.blockSelected → update_a1_plots()
block_navigator.blockSelected → update_a2_plots()
block_navigator.blockSelected → update_a2_cycle_navigator()

# Cycle selection in A2
cycle_navigator.cycleSelected → update_a2_plot_highlight()

# Settings panel ↔ A1 parameter bar (bidirectional)
settings_lp_slider.valueChanged → a1_lp_slider.setValue()  [blocked to prevent loops]
a1_lp_slider.valueChanged → settings_lp_slider.setValue()  [blocked to prevent loops]

# Theme change
dark_mode_toggle.toggled → apply_theme()
```

Use `QSignalBlocker` when syncing bidirectional slider connections to prevent infinite signal loops.

### 8.5 Performance Considerations

- **Debounce slider changes:** Use a `QTimer` (50–100ms) to debounce rapid slider movements before triggering recomputation.
- **Lazy computation for A3:** Do not recompute all-block metrics on every parameter change. Instead, mark A3 as "stale" and recompute when the user switches to the A3 tab.
- **Downsampled display for W1:** The full-session timeline in W1 can display downsampled data (e.g., every 10th sample) for performance while keeping full resolution data in memory for computation.
- **Block navigator painting:** The block navigator is a lightweight custom-painted widget. Use `QPainter` in `paintEvent` — this is very fast even for 60+ blocks.

### 8.6 File Structure Suggestion

```
experiment_analysis/
├── main.py                      # Entry point, QApplication setup
├── app.py                       # QMainWindow, navigation state, theme management
├── themes.py                    # Light/dark color dictionaries
├── state.py                     # Shared application state (dataclass or QObject)
├── widgets/
│   ├── block_navigator.py       # Custom QWidget for dual-row block navigator
│   ├── cycle_navigator.py       # Custom QWidget for cycle navigator
│   ├── parameter_slider.py      # Composite slider + label + value widget
│   └── badge.py                 # Styled QLabel for badges
├── screens/
│   ├── w1_load_review.py        # W1 screen
│   ├── w2_metadata_output.py    # W2 screen
│   ├── a1_signal_explorer.py    # A1 screen
│   ├── a2_block_analysis.py     # A2 screen
│   ├── a3_results_summary.py    # A3 screen
│   └── s1_settings_panel.py     # S1 slide-out panel
├── analysis/
│   ├── file_loader.py           # Spike2 file parsing
│   ├── block_detection.py       # Block boundary detection
│   ├── filters.py               # Butterworth, wavelet, SG differentiation
│   ├── saccade_detection.py     # SVT, STD, MAD algorithms
│   ├── sinusoidal_fit.py        # Sinusoidal fitting via linear regression
│   ├── cycle_analysis.py        # Cycle segmentation, averaging, metrics
│   └── calibration.py           # Calibration file loading, sanity checks
├── export/
│   ├── xlsx_export.py           # Excel results export
│   ├── pdf_export.py            # Figure export
│   ├── mat_export.py            # MATLAB workspace export
│   └── metadata_json.py         # _metadata.json generation
└── resources/
    └── icons/                   # Any icon assets
```
