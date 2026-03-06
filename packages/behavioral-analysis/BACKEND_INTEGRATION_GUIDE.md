# Backend Integration Guide

This guide explains how to replace the mock data layer with real signal processing and analysis logic. The GUI is fully functional with stub functions — integrating the backend means replacing those stubs one at a time without modifying any GUI code.

---

## Architecture Overview

```
screens/           GUI screens — DO NOT MODIFY during backend integration
  a1_signal_explorer.py   calls: process_block
  a2_block_analysis.py    calls: compute_cycle_analysis, compute_block_metrics
  a3_results_summary.py   calls: compute_all_results, export_*
  w1_load_review.py       calls: load_experiment_file
  s1_settings_panel.py    calls: (none — reads/writes state only)

analysis/          Backend logic lives here
  stubs.py         API boundary — screens import ONLY from here
  mock_data.py     Mock generators (remove when fully replaced)

  # Add your real backend modules here:
  file_loader.py       .smr/.smrx/.mat file parsing
  filters.py           Butterworth, wavelet position filtering
  differentiation.py   Savitzky-Golay velocity computation
  saccade_detection.py SVT/STD/MAD saccade detection
  cycle_analysis.py    Cycle averaging, SEM, sinusoidal fitting
  calibration.py       Calibration file loading and scaling
  export.py            Excel, PDF figures, MATLAB workspace export
```

The key rule: **screens only import from `stubs.py`**. Each stub function has a fixed signature and return structure. Replace the mock call inside each stub with real logic — the GUI will work unchanged as long as the return structure matches.

---

## The `params` Dict

Several stub functions receive a `params` dict containing user-adjustable analysis parameters. It is produced by `AppState.current_params()` and always has these keys:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `lp_cutoff_hz` | `float` | 40.0 | Low-pass filter cutoff frequency (Hz) |
| `sg_window_ms` | `float` | 30.0 | Savitzky-Golay window for differentiation (ms) |
| `saccade_threshold` | `float` | 50.0 | Saccade velocity threshold (deg/s) |
| `saccade_method` | `str` | "SVT" | Saccade detection method: "SVT", "STD", or "MAD" |
| `filter_method` | `str` | "Butterworth" | Position filter method: "Butterworth" or "Wavelet" |
| `saccade_min_dur_ms` | `float` | 10.0 | Minimum saccade duration (ms) |
| `saccade_padding_ms` | `float` | 5.0 | Padding around detected saccades (ms) |

---

## Stub Functions — Signatures and Return Contracts

### 1. `load_experiment_file(path: str) -> dict`

**Called by:** W1 (Load & Review) when the user browses for a file.

**Input:** Absolute path to a `.smr`, `.smrx`, or `.mat` file.

**Must return:**

```python
{
    "sample_rate": int,          # e.g. 1000 (Hz)
    "duration": float,           # total recording duration in seconds
    "num_blocks": int,           # number of detected blocks
    "channels": list[str],       # channel names, e.g. ["HTVEL", "HHVEL", ...]
    "blocks": list[dict],        # one dict per block (see below)
    "metadata_defaults": dict,   # auto-detected metadata (see below)
    "analysis_type": str,        # e.g. "Standard VOR"
    "timelines": dict,           # downsampled overview traces (see below)
    "file_info": dict,           # file-level info (see below)
}
```

**`blocks` list — each element:**

```python
{
    "index": int,                # 0-based block index
    "type": str,                 # "pre", "train", or "post"
    "label": str,                # default label, e.g. "Pre-test", "Train 1"
    "freq_hz": float,            # stimulus frequency for this block
    "start_sample": int,         # first sample index in the full recording
    "end_sample": int,           # last sample index (exclusive)
    "start_time": float,         # start time in seconds
    "end_time": float,           # end time in seconds
    "quality_fraction": float,   # 0.0-1.0, estimated quality
    "enabled": bool,             # whether this block is included in analysis
    "num_cycles": int,           # number of stimulus cycles in this block
}
```

**`timelines` dict:**

```python
{
    "time": ndarray[float32],    # time axis (downsampled, e.g. 100 Hz)
    "HTVEL": ndarray[float32],   # drum velocity trace
    "HHVEL": ndarray[float32],   # chair velocity trace
    "hepos1": ndarray[float32],  # eye position channel 1
    "hepos2": ndarray[float32],  # eye position channel 2
}
```

All timeline arrays must have the same length. Downsample from the raw sample rate (e.g. 1000 Hz -> 100 Hz) to keep the overview plots responsive.

**`metadata_defaults` dict:**

```python
{
    "subject_id": str,
    "species": str,
    "session_date": str,           # ISO format: "YYYY-MM-DD"
    "session_start_time": str,     # "HH:MM:SS"
    "lab": str,
    "institution": str,
    "task_condition": str,
    "stimulus_frequency_hz": str,
    "recording_system": str,
    "eye_tracking_system": str,
    "sampling_rate_hz": str,
}
```

These populate the W2 metadata form. Any key can be an empty string if unknown.

**`file_info` dict:**

```python
{
    "num_channels": int,
    "file_size_mb": float,
    "file_format": str,            # e.g. "Spike2 .smr"
    "file_date": str,
}
```

---

### 2. `apply_calibration(session: dict, calib_path: str) -> dict`

**Called by:** A1 (Signal Explorer) when the user loads a calibration file.

**Inputs:**
- `session`: The session dict returned by `load_experiment_file`.
- `calib_path`: Path to a calibration `.mat` or `.smr` file.

**Must return:**

```python
{
    "scale_ch1": float,          # scaling factor for eye channel 1
    "scale_ch2": float,          # scaling factor for eye channel 2
    "active_channel": str,       # "Ch1", "Ch2", or "Auto"
}
```

---

### 3. `process_block(session: dict, block_index: int, params: dict) -> dict`

**Called by:** A1 (Signal Explorer) — called on every parameter change and block selection. This is the most performance-sensitive function because sliders trigger it in real time (debounced at 80ms).

**Inputs:**
- `session`: Session dict.
- `block_index`: 0-based block index.
- `params`: Analysis parameters dict (see above).

**Must return:**

```python
{
    "time": ndarray[float32],              # shape (N,), seconds within block
    "raw_position": ndarray[float32],      # shape (N,), raw eye position
    "filtered_position": ndarray[float32], # shape (N,), after LP filter
    "raw_velocity": ndarray[float32],      # shape (N,), numerical derivative of raw
    "filtered_velocity": ndarray[float32], # shape (N,), after SG differentiation
    "stimulus": ndarray[float32],          # shape (N,), stimulus velocity
    "saccade_mask": ndarray[bool],         # shape (N,), True where saccade detected
}
```

All arrays must have the same length `N` (typically `sample_rate * block_duration`, e.g. 60000).

**Processing pipeline:**

1. Extract raw eye position for the selected block from the session data
2. Apply position filter (Butterworth or Wavelet, using `params["filter_method"]` and `params["lp_cutoff_hz"]`)
3. Compute velocity via Savitzky-Golay differentiation (using `params["sg_window_ms"]`)
4. Detect saccades (using `params["saccade_method"]`, `params["saccade_threshold"]`, `params["saccade_min_dur_ms"]`, `params["saccade_padding_ms"]`)
5. Extract stimulus trace for the block

**Performance note:** This function is called frequently during slider drags. Target < 50ms per call for smooth interaction. Consider caching intermediate results (e.g., cache the filtered position and only recompute velocity/saccades when only saccade params change).

---

### 4. `compute_cycle_analysis(session: dict, block_index: int, params: dict) -> dict`

**Called by:** A2 (Block Analysis) on block selection and parameter changes.

**Must return:**

```python
{
    "cycle_time": ndarray[float32],        # shape (M,), time within one cycle
    "cycle_traces": ndarray[float32],      # shape (num_cycles, M), individual cycles
    "cycle_average": ndarray[float32],     # shape (M,), mean of good cycles
    "cycle_sem": ndarray[float32],         # shape (M,), SEM of good cycles
    "cycle_fit": ndarray[float32],         # shape (M,), sinusoidal fit to average
    "stimulus_trace": ndarray[float32],    # shape (M,), one cycle of stimulus
    "cycle_quality": list[bool],           # length num_cycles, True = good cycle
}
```

`M` = samples per cycle (e.g. `sample_rate / stimulus_freq`). `num_cycles` = number of stimulus cycles in the block.

**Processing steps:**

1. Process the block (filter, differentiate, detect saccades — reuse `process_block` logic)
2. Segment the velocity signal into individual stimulus cycles
3. Mark each cycle as good or bad (a cycle containing any saccade samples is bad)
4. Compute cycle average and SEM from good cycles only
5. Fit a sinusoid to the cycle average to extract amplitude and phase
6. Return all components for visualization

---

### 5. `compute_block_metrics(session: dict, block_index: int, params: dict) -> dict`

**Called by:** A2 (Block Analysis) alongside `compute_cycle_analysis`.

**Must return:**

```python
{
    "block_index": int,          # 0-based
    "block_type": str,           # "pre", "train", or "post"
    "block_label": str,          # display label
    "gain": float,               # eye_amp / stim_amp
    "eye_amp": float,            # amplitude of eye velocity (deg/s)
    "eye_amp_sem": float,        # SEM of eye amplitude across cycles
    "eye_phase": float,          # phase relative to stimulus (degrees)
    "eye_phase_sem": float,      # SEM of phase across cycles
    "stim_amp": float,           # stimulus amplitude (deg/s)
    "freq_hz": float,            # stimulus frequency (Hz)
    "good_cycles": int,          # number of cycles without saccades
    "total_cycles": int,         # total number of cycles
    "var_residual": float,       # variance of residual (average - fit)
}
```

This is typically computed from the same data as `compute_cycle_analysis`. Consider having both functions share an internal computation to avoid duplicate work.

---

### 6. `compute_all_results(session: dict, params: dict) -> list[dict]`

**Called by:** A3 (Results Summary) when switching to the results tab (lazy computation).

**Must return:** A list of dicts, one per enabled block, each with the same structure as `compute_block_metrics` above.

**Implementation:** Loop over all enabled blocks, call `compute_block_metrics` (or equivalent) for each, collect into a list.

---

### 7. `export_excel(results: list[dict], path: str) -> None`

**Called by:** A3 export bar.

**Input:** The results list from `compute_all_results` and the output file path (`.xlsx`).

Write block metrics to an Excel spreadsheet. Consider using `openpyxl` or `pandas`.

---

### 8. `export_figures(results: list[dict], path: str) -> None`

**Called by:** A3 export bar.

**Input:** Results list and output path (`.pdf`).

Generate publication-quality figures (gain vs block, phase vs block, etc.) and save as multi-page PDF. Consider using `matplotlib`.

---

### 9. `export_workspace(results: list[dict], path: str) -> None`

**Called by:** A3 export bar.

**Input:** Results list and output path (`.mat`).

Save results as a MATLAB `.mat` file using `scipy.io.savemat`.

---

## Step-by-Step Integration Procedure

### Step 1: Set up backend modules

Create your backend modules in the `analysis/` directory:

```
analysis/
  __init__.py
  stubs.py           # existing — you'll modify this
  mock_data.py       # existing — keep until fully replaced
  file_loader.py     # NEW: .smr/.smrx/.mat parsing
  filters.py         # NEW: Butterworth, wavelet filters
  differentiation.py # NEW: Savitzky-Golay
  saccade_detection.py # NEW: SVT/STD/MAD
  cycle_analysis.py  # NEW: cycle segmentation, averaging, fitting
  calibration.py     # NEW: calibration file handling
  export.py          # NEW: Excel, PDF, MATLAB export
```

### Step 2: Replace stubs one at a time

Open `stubs.py` and replace one function at a time. For example, to integrate `process_block`:

**Before:**
```python
def process_block(session, block_index, params):
    return mock_data.generate_mock_block_signals(block_index, params)
```

**After:**
```python
def process_block(session, block_index, params):
    from .filters import apply_position_filter
    from .differentiation import compute_velocity
    from .saccade_detection import detect_saccades

    block = session["blocks"][block_index]
    raw_pos = _extract_block_signal(session, block)

    filtered_pos = apply_position_filter(
        raw_pos, session["sample_rate"],
        method=params["filter_method"],
        cutoff_hz=params["lp_cutoff_hz"],
    )

    raw_vel = compute_velocity(
        raw_pos, session["sample_rate"],
        window_ms=params["sg_window_ms"],
    )
    filtered_vel = compute_velocity(
        filtered_pos, session["sample_rate"],
        window_ms=params["sg_window_ms"],
    )

    saccade_mask = detect_saccades(
        filtered_vel, session["sample_rate"],
        method=params["saccade_method"],
        threshold=params["saccade_threshold"],
        min_dur_ms=params["saccade_min_dur_ms"],
        padding_ms=params["saccade_padding_ms"],
    )

    t = np.arange(len(raw_pos)) / session["sample_rate"]
    stimulus = _extract_stimulus(session, block)

    return {
        "time": t.astype(np.float32),
        "raw_position": raw_pos.astype(np.float32),
        "filtered_position": filtered_pos.astype(np.float32),
        "raw_velocity": raw_vel.astype(np.float32),
        "filtered_velocity": filtered_vel.astype(np.float32),
        "stimulus": stimulus.astype(np.float32),
        "saccade_mask": saccade_mask.astype(bool),
    }
```

### Step 3: Recommended integration order

1. **`load_experiment_file`** — Start here. Once real data loads, you can visually verify everything in W1.
2. **`process_block`** — The core signal processing pipeline. This lets you verify filtering, differentiation, and saccade detection in A1 with real-time parameter tuning.
3. **`apply_calibration`** — Needed for proper scaling but can be deferred.
4. **`compute_cycle_analysis`** + **`compute_block_metrics`** — Integrate together since they share computations. Verify in A2.
5. **`compute_all_results`** — Usually just loops `compute_block_metrics`. Verify in A3.
6. **`export_*`** — Last, since they don't affect visualization.

### Step 4: Test each replacement

After replacing each stub:

1. Launch the app: `python -m behavioral_analysis.main`
2. Load a real data file
3. Navigate to the relevant screen
4. Verify the plots render correctly
5. For `process_block`: drag all sliders and confirm real-time updates work without lag
6. Switch themes to confirm plots still render
7. Test edge cases: first/last block, blocks with no good cycles, very short blocks

### Step 5: Remove mock_data.py

Once all stubs are replaced with real implementations, delete `mock_data.py` and remove the `from . import mock_data` line from `stubs.py`.

---

## GUI Consumption Reference

This table shows exactly which screen calls which stub and what it does with the return data:

| Stub Function | Screen | What the GUI Does |
|---|---|---|
| `load_experiment_file` | W1 | Plots `timelines` in 3 overview plots, fills block table from `blocks`, shows `file_info` and `metadata_defaults` |
| `apply_calibration` | A1 | Stores `scale_ch1`, `scale_ch2`, `active_channel` in AppState |
| `process_block` | A1 | Plots all 7 arrays as traces on 2 linked pyqtgraph plots; uses `saccade_mask` for region shading |
| `compute_cycle_analysis` | A2 | Plots `cycle_traces` individually or as average+SEM+fit depending on display mode; `cycle_quality` drives CycleNavigator colors |
| `compute_block_metrics` | A2 | Displays all values in the metrics card (9 labels) |
| `compute_all_results` | A3 | Feeds scatter plot (x=block#, y=selected metric) and results table (11 columns) |
| `export_*` | A3 | Called on button click with results list and auto-generated path |

---

## Common Pitfalls

1. **Array dtype matters.** The GUI expects `float32` for plot data and `bool` for masks. Using `float64` works but wastes memory. Using integer types for plot data may cause rendering issues.

2. **All arrays in a return dict must have consistent lengths.** If `time` has 60000 elements, every other array in that dict must also have 60000 elements.

3. **`process_block` is performance-critical.** It's called on every slider change (debounced at 80ms). If it takes > 100ms, the UI will feel sluggish. Profile and optimize this function first.

4. **`cycle_quality` must be a Python `list[bool]`, not a numpy array.** The CycleNavigator iterates over it with Python indexing.

5. **`compute_all_results` can be slow.** It processes all blocks. The GUI handles this by only calling it lazily (when the user switches to the A3 tab). No special handling needed — just be aware it may take a few seconds.

6. **Don't modify the session dict.** Functions receive the session dict by reference. If your backend needs to cache processed data, store it in a separate cache structure rather than mutating the session.

7. **Block indices are 0-based.** The GUI adds 1 for display purposes. Your backend should use 0-based indices consistently.

8. **The `blocks` list in the session dict may have `enabled: False` entries.** `compute_all_results` should skip disabled blocks (or include them — the GUI handles both, but skipping is cleaner).
