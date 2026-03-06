"""Stub functions defining the backend API contract.

Each function delegates to mock_data.py for now. To integrate real backend
logic, replace the mock calls — the function signatures and return dict
structures stay the same.
"""

from . import mock_data


def load_experiment_file(path):
    """Load an experiment file and return session data.

    Args:
        path: Path to .smr/.smrx/.mat file (ignored in stub).

    Returns dict with keys:
        sample_rate (int), duration (float), num_blocks (int),
        channels (list[str]), blocks (list[dict]), metadata_defaults (dict),
        analysis_type (str), timelines (dict), file_info (dict).
    """
    return mock_data.generate_mock_session()


def apply_calibration(session, calib_path):
    """Apply calibration from file or manual entry.

    Args:
        session: Session dict from load_experiment_file.
        calib_path: Path to calibration file (ignored in stub).

    Returns dict with keys:
        scale_ch1 (float), scale_ch2 (float), active_channel (str).
    """
    return {
        "scale_ch1": 1.0,
        "scale_ch2": 0.95,
        "active_channel": "Ch1",
    }


def process_block(session, block_index, params):
    """Process a single block: filter, differentiate, detect saccades.

    Args:
        session: Session dict from load_experiment_file.
        block_index: 0-based block index.
        params: dict with lp_cutoff_hz, sg_window_ms, saccade_threshold,
                saccade_method, filter_method, saccade_min_dur_ms,
                saccade_padding_ms.

    Returns dict with keys:
        time (ndarray[60000]), raw_position (ndarray[60000]),
        filtered_position (ndarray[60000]), raw_velocity (ndarray[60000]),
        filtered_velocity (ndarray[60000]), stimulus (ndarray[60000]),
        saccade_mask (ndarray[60000] bool).
    """
    return mock_data.generate_mock_block_signals(block_index, params)


def compute_cycle_analysis(session, block_index, params):
    """Compute cycle-averaged analysis for a block.

    Args:
        session: Session dict from load_experiment_file.
        block_index: 0-based block index.
        params: Analysis parameter dict.

    Returns dict with keys:
        cycle_time (ndarray[1000]), cycle_traces (ndarray[N, 1000]),
        cycle_average (ndarray[1000]), cycle_sem (ndarray[1000]),
        cycle_fit (ndarray[1000]), stimulus_trace (ndarray[1000]),
        cycle_quality (list[bool]).
    """
    return mock_data.generate_mock_cycle_data(block_index)


def compute_block_metrics(session, block_index, params):
    """Compute summary metrics for a single block.

    Args:
        session: Session dict from load_experiment_file.
        block_index: 0-based block index.
        params: Analysis parameter dict.

    Returns dict with keys:
        block_index (int), block_type (str), block_label (str),
        gain (float), eye_amp (float), eye_amp_sem (float),
        eye_phase (float), eye_phase_sem (float), stim_amp (float),
        freq_hz (float), good_cycles (int), total_cycles (int),
        var_residual (float).
    """
    return mock_data.generate_mock_block_metrics(block_index)


def compute_all_results(session, params):
    """Compute metrics for all blocks.

    Args:
        session: Session dict from load_experiment_file.
        params: Analysis parameter dict.

    Returns list of block metric dicts (one per block).
    """
    return mock_data.generate_mock_results_table()


def export_excel(results, path):
    """Export results to Excel file (stub — prints only)."""
    print(f"[STUB] export_excel: {len(results)} blocks -> {path}")


def export_figures(results, path):
    """Export figures as PDF (stub — prints only)."""
    print(f"[STUB] export_figures: {len(results)} blocks -> {path}")


def export_workspace(results, path):
    """Export MATLAB workspace (stub — prints only)."""
    print(f"[STUB] export_workspace: {len(results)} blocks -> {path}")
