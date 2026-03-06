# Behavioral Experiment Analysis — Frontend Development Plan

## Context

The Raymond Lab currently uses MATLAB GUIs (`.mlapp` files) for analyzing behavioral experiment data (VOR/OKR paradigms). These tools are not version-control friendly, require manual parameter tuning without real-time feedback, and generate scattered output files. This plan replaces them with a unified Python GUI built with PySide6 and pyqtgraph.

The frontend will be developed first using mock data and stub functions for all backend elements (file loading, signal processing, analysis). The backend will be developed after a working prototype is complete.

**Key constraints:**
- Single maintainer — structure must be simple yet robust
- Python >=3.9,<3.10
- PySide6 + pyqtgraph
- Windows 11 primary, macOS secondary
- Non-technical users — all interactions must be GUI-based

**Authoritative references:**
- [resources/experiment-analysis_development-guide.md](resources/experiment-analysis_development-guide.md) — full specification
- [resources/experiment-analysis_prototype.jsx](resources/experiment-analysis_prototype.jsx) — visual prototype

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Project Scaffolding | Complete |
| 1 | Navigation Shell & Theme Switching | Complete |
| 2 | Custom Shared Widgets | Complete |
| 3 | Mock Data Layer & Analysis Stubs | Complete |
| 4 | W1 (Load & Review) & W2 (Metadata & Output) | Complete |
| 5 | A1 (Signal Explorer) & S1 (Settings Panel) | Complete |
| 6 | A2 (Block Analysis) & A3 (Results Summary) | Complete |
| 7 | Polish & Edge Cases | Complete |

---

## Backend Integration Strategy

All backend logic is isolated behind a clean API in `analysis/stubs.py`. Each stub function has a defined signature and return type that will remain stable when the real backend is implemented. To integrate the backend later:

1. **Replace stubs one at a time.** Each function in `stubs.py` delegates to `mock_data.py`. To integrate real backend logic, replace the mock call with the real implementation — the function signature and return dict structure stay the same.
2. **No GUI code changes needed.** Screens call only stub functions and expect specific dict/array shapes. As long as the backend returns the same shapes, the GUI works unchanged.
3. **Stub function signatures are the contract:**
   - `load_experiment_file(path: str) -> dict` — keys: `sample_rate`, `duration`, `num_blocks`, `channels`, `blocks`, `metadata_defaults`, etc.
   - `apply_calibration(session: dict, calib_path: str) -> dict` — keys: `scale_ch1`, `scale_ch2`, `active_channel`
   - `process_block(session: dict, block_index: int, params: dict) -> dict` — keys: `time`, `raw_position`, `filtered_position`, `raw_velocity`, `filtered_velocity`, `stimulus`, `saccade_mask`
   - `compute_cycle_analysis(session: dict, block_index: int, params: dict) -> dict` — keys: `cycle_time`, `cycle_traces`, `cycle_average`, `cycle_sem`, `cycle_fit`, `stimulus_trace`, `cycle_quality`
   - `compute_block_metrics(session: dict, block_index: int, params: dict) -> dict` — keys: `gain`, `eye_amp`, `eye_amp_sem`, `eye_phase`, `eye_phase_sem`, `stim_amp`, `freq_hz`, `good_cycles`, `total_cycles`, `var_residual`
   - `compute_all_results(session: dict, params: dict) -> list[dict]` — list of block metric dicts
   - `export_excel/figures/workspace(results, path: str) -> None`
4. **The `params` dict** passed to processing functions contains: `lp_cutoff_hz`, `sg_window_ms`, `saccade_threshold`, `saccade_method`, `filter_method`, `saccade_min_dur_ms`, `saccade_padding_ms`
5. **Future backend files** go in `analysis/` alongside the stubs (e.g., `filters.py`, `saccade_detection.py`, `sinusoidal_fit.py`, `cycle_analysis.py`, `calibration.py`, `file_loader.py`). The stubs then import and call these instead of mock_data.

---

## Phase 0: Project Scaffolding

**Goal:** Fix package structure, establish file layout, open a blank themed window.

**Tasks:**
1. Rename outer directory `packages/experiment-analysis/` -> `packages/behavioral-analysis/` and inner source directory `src/experiment-analysis/` -> `src/behavioral_analysis/`
2. Update `packages/behavioral-analysis/pyproject.toml`: update package name and change entry point to `behavioral_analysis.app:main`
3. Create core files:
   - `behavioral_analysis/main.py` — `QApplication` setup, calls `main()` from app
   - `behavioral_analysis/app.py` — `MainWindow(QMainWindow)` with `QStackedWidget` central widget (wizard page + workspace page), initial size 1280x800, min 1024x600
   - `behavioral_analysis/state.py` — `AppState(QObject)` with all state variables from dev guide Section 3, Qt signals for each property change
   - `behavioral_analysis/themes.py` — `LIGHT_THEME` / `DARK_THEME` dicts mirroring Section 4 tokens, `generate_stylesheet(theme) -> str`, `apply_theme(app, theme)`
4. Create empty `__init__.py` files for `widgets/`, `screens/`, `analysis/` subpackages

**Tests:**
- [ ] App launches without errors: `python -m behavioral_analysis.main`
- [ ] Window appears at 1280x800 with title "Behavioral Experiment Analysis"
- [ ] Window respects minimum size 1024x600
- [ ] Light theme QSS applied (verify background color matches `#E8ECF0`)
- [ ] App closes cleanly with no console errors

**Files:**
```
packages/behavioral-analysis/src/behavioral_analysis/
|-- __init__.py
|-- main.py
|-- app.py
|-- state.py
|-- themes.py
|-- widgets/__init__.py
|-- screens/__init__.py
+-- analysis/__init__.py
```

---

## Phase 1: Navigation Shell & Theme Switching

**Goal:** Full navigation architecture with placeholder screen content and working theme toggle.

**Tasks:**
1. Create placeholder screens (each a `QWidget` with centered label):
   - `screens/w1_load_review.py` — `W1Screen`
   - `screens/w2_metadata_output.py` — `W2Screen`
   - `screens/a1_signal_explorer.py` — `A1Screen`
   - `screens/a2_block_analysis.py` — `A2Screen`
   - `screens/a3_results_summary.py` — `A3Screen`
   - `screens/s1_settings_panel.py` — `S1Panel` (265px wide, header + dark mode `QCheckBox` + close button)
2. Build navigation in `app.py`:
   - **Wizard phase:** `QStackedWidget` with W1/W2, Next/Back buttons
   - **Workspace phase:** toolbar (left: session info labels, right: New Analysis button + tab `QButtonGroup` + gear button) + content `QStackedWidget` (A1/A2/A3) + S1 panel (show/hide)
   - **Status bar:** `QStatusBar` with styled `QLabel`s, accent background, placeholder text
   - Dynamic `setWindowTitle()` on navigation changes
3. Wire `AppState` signals: `phase`, `wizard_step`, `workspace_tab`, `settings_open`
4. Wire dark mode toggle -> `apply_theme()` (regenerate QSS, reapply)
5. Add temp "skip to workspace" button on W1 for testing

**Tests:**
- [ ] W1 placeholder visible on launch
- [ ] Next button navigates to W2; Back button returns to W1
- [ ] Start Analysis (or skip button) transitions to workspace phase
- [ ] Workspace toolbar visible with tab buttons, gear icon, New Analysis button
- [ ] Tab buttons switch between A1/A2/A3 placeholder content
- [ ] Gear icon toggles S1 panel visibility (slides in/out)
- [ ] Dark mode toggle in S1 switches entire app theme (light <-> dark)
- [ ] New Analysis shows confirmation dialog, then returns to W1
- [ ] Window title updates on each navigation change
- [ ] Status bar visible in workspace phase with placeholder text

---

## Phase 2: Custom Shared Widgets

**Goal:** Build the four reusable widgets, testable in isolation.

**Tasks:**
1. `widgets/block_navigator.py` — `BlockNavigator(QWidget)`:
   - Custom `paintEvent`: dual-row strip (top: block type colors, bottom: quality colors)
   - Prev/Next `QPushButton`s, label area ("Block N / Total")
   - Properties: `selected_block`, block data list
   - Signals: `block_selected(int)`
   - `mousePressEvent` maps x -> block index
2. `widgets/cycle_navigator.py` — `CycleNavigator(QWidget)`:
   - Custom `paintEvent`: horizontal cycle segments (green=good, red=saccade, blue=selected)
   - Properties: `cycle_data` (list of bools), `selected_cycle`
   - Signals: `cycle_selected(int)`
3. `widgets/parameter_slider.py` — `ParameterSlider(QWidget)`:
   - Composite: `QLabel` (72px, right-aligned) + `QSlider` + `QLabel` (52px, monospace value + unit)
   - Properties: `label`, `value`, `minimum`, `maximum`, `suffix`
   - Debounced `value_changed(float)` signal via `QTimer` (80ms)
   - QSS: 4px groove, 14px circular handle, accent fill
4. `widgets/badge.py` — `Badge(QLabel)`:
   - Variants: "green", "accent", "neutral", "warning", "error"
   - Small font, rounded background

**Tests (standalone `widgets/test_widgets.py`):**
- [ ] BlockNavigator: renders 31+ colored segments in dual rows
- [ ] BlockNavigator: clicking a segment selects it (outline + label update)
- [ ] BlockNavigator: Prev/Next buttons change selection
- [ ] BlockNavigator: `block_selected` signal emits correct index
- [ ] CycleNavigator: renders cycle segments with correct colors
- [ ] CycleNavigator: click selects cycle, emits `cycle_selected`
- [ ] ParameterSlider: dragging updates value display in real time
- [ ] ParameterSlider: debounced `value_changed` signal fires (not on every pixel)
- [ ] Badge: all 5 variants render with distinct colors
- [ ] All widgets render correctly in both light and dark themes

---

## Phase 3: Mock Data Layer & Analysis Stubs

**Goal:** Create mock data generators and stub functions defining the data contracts all screens will use. These stubs define the exact API that the real backend will implement later.

**Tasks:**
1. `analysis/mock_data.py`:
   - `generate_mock_session() -> dict` — 62 blocks (1 pre + 60 training + 1 post), 13 channels, 1kHz, metadata defaults
   - `generate_mock_timeline(num_samples, channel) -> np.ndarray` — downsampled sinusoidal + noise
   - `generate_mock_block_signals(block_index, params) -> dict` — 60k-sample arrays: raw/filtered position, raw/filtered velocity, stimulus, saccade_mask. `lp_cutoff_hz` varies noise; `saccade_threshold` varies saccade count
   - `generate_mock_cycle_data(block_index, num_cycles) -> dict` — cycle traces, average, SEM, fit, quality bools
   - `generate_mock_block_metrics(block_index) -> dict` — gain, amplitude, phase, etc.
   - `generate_mock_results_table() -> list[dict]` — 62 rows of block metrics
2. `analysis/stubs.py` — stub functions matching future backend API (see Backend Integration Strategy above for full signatures):
   - `load_experiment_file(path) -> dict`
   - `apply_calibration(session, calib_path) -> dict`
   - `process_block(session, block_index, params) -> dict`
   - `compute_cycle_analysis(session, block_index, params) -> dict`
   - `compute_block_metrics(session, block_index, params) -> dict`
   - `compute_all_results(session, params) -> list[dict]`
   - `export_excel/figures/workspace(results, path) -> None` (print stubs)

**Mock data design:** Use `numpy` with deterministic seeds. Sinusoids at 1 Hz with block-index-dependent phase shifts. Saccades: 3-5 random intervals per block. Quality fractions: 0.15-0.95 range.

**Tests:**
- [ ] `load_experiment_file()` returns dict with all expected keys
- [ ] `process_block()` returns arrays of correct shape (60000 samples)
- [ ] `compute_cycle_analysis()` returns cycle traces, average, SEM, fit of correct shapes
- [ ] `compute_block_metrics()` returns dict with all metric keys
- [ ] `compute_all_results()` returns list of 62 dicts
- [ ] Mock signals vary plausibly with parameter changes (lp_cutoff, saccade_threshold)
- [ ] All functions are deterministic (same seed -> same output)
- [ ] Return types match the documented contract in Backend Integration Strategy

---

## Phase 4: W1 (Load & Review) & W2 (Metadata & Output)

**Goal:** Full wizard screens connected to mock data.

**W1 layout (top -> bottom):**
1. **Control bar** (`QFrame`): Browse `QPushButton` -> `QFileDialog`, file path `QLineEdit` (read-only), Analysis Type `QComboBox` (Standard VOR / OKR / VOR Cancellation / Custom), Next button (disabled until file loaded). Second row: file metadata (monospace, hidden until loaded)
2. **Session summary bar** (`QFrame`, `bgPanelAlt`): Duration, Blocks, Pre/Post, Training, Freq, Sample Rate labels
3. **Main area** (`QSplitter`):
   - Left: 3 vertically stacked `pyqtgraph.PlotWidget`s (drum vel, chair vel, raw eye position). Channel `QComboBox` headers. Block region overlays (`LinearRegionItem`, immovable, 15-20% opacity). Third plot: two overlaid traces (hepos1 orange, hepos2 blue)
   - Right (w=195): `QTableView` + `QStandardItemModel`. Columns: #, Label (`QComboBox` delegate, color-coded), Hz, checkmark (checkbox). Row click highlights block in plots
4. **Empty state:** centered placeholder shown when no file loaded

**W2 layout:**
1. **Control bar:** Back button, Save To path, remaining-fields counter (red), Start Analysis (disabled until all required fields filled)
2. **Metadata form** (`QScrollArea`): 4 `QGroupBox` sections (Subject, Session, Experiment, Device). Required fields: red asterisk. Auto-populated: green `Badge`. Real-time validation updates counter

**Wiring:**
- Browse -> calls `stubs.load_experiment_file()` -> populates plots, table, summary
- Next -> `state.wizard_step = 2`; Back -> `state.wizard_step = 1`
- Start Analysis -> `QProgressDialog` (1.2s simulated) -> `state.phase = "workspace"`

**Tests:**
- [ ] Empty state shown on launch (no file loaded)
- [ ] Browse opens file dialog; selecting any file triggers mock data loading
- [ ] After loading: 3 timeline plots render with sinusoidal traces
- [ ] Block region overlays visible (green for pre/post, red for training)
- [ ] Third plot shows two overlaid traces in orange and blue
- [ ] Session summary bar populates with correct stats
- [ ] Block table fills with 62 rows; labels are color-coded
- [ ] Clicking a block table row highlights that block in the timeline plots
- [ ] Next button disabled until file loaded; enabled after loading
- [ ] W2: metadata form shows 4 sections with all fields
- [ ] Required fields marked with red asterisk
- [ ] Auto-populated fields show green "auto" badge
- [ ] Remaining-fields counter updates as fields are filled
- [ ] Start Analysis disabled until all required fields filled; enabled when count = 0
- [ ] Start Analysis shows progress dialog, then transitions to workspace
- [ ] Back preserves metadata entries

---

## Phase 5: A1 (Signal Explorer) & S1 (Settings Panel) with Bidirectional Sync

**Goal:** Primary analysis screen with real-time parameter tuning and settings panel synchronization.

**A1 layout (top -> bottom):**
1. **Calibration section** (collapsible):
   - Collapsed: summary values, green "OK" badge, Load File / Manual buttons
   - Expanded: Browse, file path, scaling values, sanity badge, Apply
2. **Block navigator** (`BlockNavigator` from Phase 2, connected to `state.selected_block`)
3. **Signal plots** (`QSplitter`):
   - Eye Position: raw (gray), filtered (orange), saccade segments (red), saccade region shading
   - Eye Velocity: stimulus (gray dashed), raw (gray), filtered (blue), saccade segments (red)
   - X-axes linked via `setXLink()`
4. **Parameter bar** (`QFrame`, `bgParam`): 3 sections with vertical dividers:
   - Position Filter: Method `QComboBox` + LP Cutoff `ParameterSlider` (1-100 Hz, default 40)
   - Differentiation: SG Window `ParameterSlider` (3-100 ms, default 30)
   - Saccade Detection: Method `QComboBox` + Threshold `ParameterSlider` (5-200 deg/s, default 50)

**S1 full layout:** Collapsible sections mirroring A1 params + Eye Channel `QComboBox` + Dark Mode toggle + Reset to Defaults

**Bidirectional sync pattern:**
```
a1_slider.value_changed -> state.property (setter)
s1_slider.value_changed -> state.property (setter)
state.property_changed -> a1_slider.set_value (QSignalBlocker)
state.property_changed -> s1_slider.set_value (QSignalBlocker)
```

**Real-time update:** `state.parameters_changed` -> `stubs.process_block()` -> update all `PlotDataItem` data. Debounce from `ParameterSlider` ensures max 1 recompute per 80ms.

**Tests:**
- [ ] Calibration section toggles between collapsed/expanded states
- [ ] Block navigator displays blocks with correct type/quality colors
- [ ] Selecting a block updates both signal plots with new data
- [ ] Eye Position plot shows raw, filtered, and saccade traces
- [ ] Eye Velocity plot shows stimulus, raw, filtered, and saccade traces
- [ ] X-axes are linked between the two plots
- [ ] Dragging LP Cutoff slider updates filtered position trace in real time
- [ ] Dragging SG Window slider updates velocity traces in real time
- [ ] Dragging Saccade Threshold slider updates saccade highlights in real time
- [ ] Opening S1 shows matching parameter values
- [ ] Changing a slider in S1 updates the corresponding A1 slider and plots
- [ ] Changing a slider in A1 updates the corresponding S1 slider
- [ ] No infinite signal loops during bidirectional sync
- [ ] Reset to Defaults restores all parameters to initial values
- [ ] Rapid slider dragging doesn't cause UI freezes (debounce working)

---

## Phase 6: A2 (Block Analysis) & A3 (Results Summary)

**Goal:** Complete all workspace tabs.

**A2 layout:**
1. `BlockNavigator` (shared `state.selected_block`)
2. Cycle row: `CycleNavigator` + legend + display mode toggle (`QButtonGroup`: SEM / All Cycles / Good Cycles)
3. Main area (`QSplitter`):
   - Cycle-average plot: SEM mode (average + SEM fill + fit + stimulus), All/Good Cycles mode (individual traces at 20% opacity + selected trace at 100%)
   - Metrics card (w=168): Gain, Eye Amp+/-SEM, Phase+/-SEM, Stim Amp, Freq, Good Cycles, Var Residual

**A3 layout:**
1. Y-axis selector `QComboBox` (Gain / Eye Amp / Phase / Good Cycle Fraction / Var Residual)
2. Scatter plot (`PlotWidget`, h=175): pre/post green markers, training red markers. Click -> select block
3. Results table (`QTableView` + `QAbstractTableModel`): all block metrics, color-coded labels, monospace numerics. Row click -> select block
4. Export bar: Excel / Figures / Workspace / Export All buttons -> call stubs

**Lazy computation:** A3 marks stale on param changes, recomputes on tab switch.

**Tests:**
- [ ] A2: Block navigator synced with A1 (selecting block in A1 updates A2)
- [ ] A2: Cycle navigator renders cycles with correct good/bad colors
- [ ] A2: SEM mode shows average trace + SEM shaded band + fit line
- [ ] A2: All Cycles mode shows individual traces at low opacity + selected at full
- [ ] A2: Good Cycles mode filters out saccade-detected cycles
- [ ] A2: Clicking a cycle in navigator highlights it in the plot
- [ ] A2: Metrics card displays all values in correct format
- [ ] A3: Scatter plot renders pre/post (green) and training (red) markers
- [ ] A3: Y-axis selector changes the plotted metric
- [ ] A3: Clicking a scatter point selects that block (syncs across tabs)
- [ ] A3: Results table populates with 62 rows, correct columns
- [ ] A3: Clicking a table row selects that block
- [ ] A3: Export buttons call stubs and show confirmation
- [ ] A3: Lazy recomputation works (stale flag set on param change, recompute on tab switch)
- [ ] Cross-tab sync: selecting a block in A3 table updates A1 and A2

---

## Phase 7: Polish & Edge Cases

**Goal:** Visual fidelity, UX refinements, edge case handling.

**Tasks:**
1. **QSS refinement:** Match prototype pixel-for-pixel — padding, fonts, borders, `QComboBox` dropdowns, `QScrollBar`, `QSplitter` handles
2. **pyqtgraph styling:** Axis tick formatting (seconds, degrees), label fonts (monospace 10px), grid opacity, legend colors
3. **Status bar:** Live parameter values ("LP:40Hz . SG:30ms . Sac:50deg/s"), session info ("1000Hz . 62 blocks")
4. **Keyboard shortcuts:** Ctrl+O (Browse), Left/Right (block nav), Escape (close settings)
5. **Edge cases:** Block disable/enable (checkbox), cancelled file dialog, resize at 1024x600 minimum, theme switch mid-session (repaint pyqtgraph)
6. **Loading dialog:** Styled `QProgressDialog` matching prototype
7. **W1 block highlight:** Row click scrolls timeline + briefly highlights block overlay
8. **Cross-platform fonts:** Segoe UI / SF Pro Text (UI), Consolas / SF Mono (monospace)

**Tests:**
- [ ] Visual comparison against JSX prototype in both themes
- [ ] Status bar updates live with parameter values and session info
- [ ] Keyboard shortcuts work (Ctrl+O, arrows, Escape)
- [ ] Disabling a block in W1 excludes it from navigation and analysis
- [ ] Cancelling file dialog causes no state change
- [ ] App usable at minimum window size (1024x600)
- [ ] Theme switch mid-session restyles all widgets and pyqtgraph plots
- [ ] Loading dialog styled correctly with progress text
- [ ] W1 block table row click scrolls and highlights the block in timeline
- [ ] Correct fonts render on macOS (SF Pro Text / SF Mono)
- [ ] Full end-to-end walkthrough completes without errors
- [ ] Rapid slider dragging causes no freezes or visual glitches

---

## Verification Checklist (Per Phase)

After completing each phase:
1. Run the app and verify all tests listed for that phase
2. Test in both light and dark themes
3. Test window resize behavior (drag to minimum, maximize, restore)
4. Confirm no console errors, warnings, or uncaught exceptions
5. Verify all previously completed phases still work (regression)
6. Update the Phase Status table above

## Final Verification (After Phase 7)

- Complete end-to-end walkthrough: Browse -> Load -> Review blocks -> Fill metadata -> Start Analysis -> Explore signals with parameter tuning -> View cycle analysis in all 3 display modes -> Review results summary -> Export (stubs) -> New Analysis -> repeat
- Test at minimum window size (1024x600)
- Toggle theme multiple times during a session
- Rapid slider dragging on all parameters
- Verify backend integration readiness: confirm all screen-to-stub connections use the documented API contracts
