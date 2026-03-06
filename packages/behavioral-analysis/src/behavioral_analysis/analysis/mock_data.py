"""Mock data generators for frontend development.

All generators use deterministic numpy seeds so outputs are reproducible.
"""

import numpy as np

# Constants
SAMPLE_RATE = 1000  # Hz
BLOCK_DURATION = 60.0  # seconds per block
SAMPLES_PER_BLOCK = int(SAMPLE_RATE * BLOCK_DURATION)  # 60000
NUM_BLOCKS = 62  # 1 pre + 60 train + 1 post
NUM_CHANNELS = 13
STIMULUS_FREQ = 1.0  # Hz

# Channel names matching Spike2 convention
CHANNEL_NAMES = [
    "HTVEL", "HHVEL", "htpos", "hhpos", "hepos1", "hepos2",
    "htvel_raw", "hhvel_raw", "TTL1", "TTL2", "TTL3", "TextMark", "Keyboard",
]


def _block_type(block_index):
    """Return block type string for a given index."""
    if block_index == 0:
        return "pre"
    elif block_index == NUM_BLOCKS - 1:
        return "post"
    return "train"


def _block_label(block_index, analysis_type="Standard VOR"):
    """Return a default label for a block."""
    btype = _block_type(block_index)
    if btype == "pre":
        return "Pre-test"
    elif btype == "post":
        return "Post-test"
    return f"Train {block_index}"


def generate_mock_session(analysis_type="Standard VOR"):
    """Generate a complete mock session dict.

    Returns dict with keys: sample_rate, duration, num_blocks, channels,
    blocks, metadata_defaults, analysis_type, timelines.
    """
    rng = np.random.RandomState(42)
    total_duration = NUM_BLOCKS * BLOCK_DURATION
    total_samples = int(total_duration * SAMPLE_RATE)

    blocks = []
    for i in range(NUM_BLOCKS):
        start_sample = i * SAMPLES_PER_BLOCK
        end_sample = start_sample + SAMPLES_PER_BLOCK
        qf = 0.15 + rng.random() * 0.80  # quality fraction 0.15-0.95
        blocks.append({
            "index": i,
            "type": _block_type(i),
            "label": _block_label(i, analysis_type),
            "freq_hz": STIMULUS_FREQ,
            "start_sample": start_sample,
            "end_sample": end_sample,
            "start_time": i * BLOCK_DURATION,
            "end_time": (i + 1) * BLOCK_DURATION,
            "quality_fraction": round(qf, 3),
            "enabled": True,
            "num_cycles": int(BLOCK_DURATION * STIMULUS_FREQ),
        })

    # Generate downsampled timelines for W1 overview (every 10th sample)
    downsample = 10
    timeline_samples = total_samples // downsample
    t_ds = np.arange(timeline_samples) / (SAMPLE_RATE / downsample)

    timelines = {}
    for ch_name in ["HTVEL", "HHVEL", "hepos1", "hepos2"]:
        timelines[ch_name] = generate_mock_timeline(
            timeline_samples, ch_name, rng_seed=hash(ch_name) % (2**31)
        )
    timelines["time"] = t_ds

    metadata_defaults = {
        "subject_id": "M001",
        "species": "Mus musculus",
        "session_date": "2026-01-15",
        "session_start_time": "10:30:00",
        "lab": "Raymond Lab",
        "institution": "Stanford University",
        "task_condition": analysis_type,
        "stimulus_frequency_hz": str(STIMULUS_FREQ),
        "recording_system": "Spike2",
        "eye_tracking_system": "Search coil",
        "sampling_rate_hz": str(SAMPLE_RATE),
    }

    return {
        "sample_rate": SAMPLE_RATE,
        "duration": total_duration,
        "num_blocks": NUM_BLOCKS,
        "channels": CHANNEL_NAMES,
        "blocks": blocks,
        "metadata_defaults": metadata_defaults,
        "analysis_type": analysis_type,
        "timelines": timelines,
        "file_info": {
            "num_channels": NUM_CHANNELS,
            "file_size_mb": 59.2,
            "file_format": "Spike2 .smr",
            "file_date": "2026-01-15",
        },
    }


def generate_mock_timeline(num_samples, channel, rng_seed=0):
    """Generate a downsampled timeline array for W1 overview plots.

    Returns an ndarray of shape (num_samples,).
    """
    rng = np.random.RandomState(rng_seed)
    t = np.arange(num_samples) / 100.0  # assuming 100 Hz after downsample

    if channel in ("HTVEL", "htvel_raw"):
        # Drum velocity: sinusoidal blocks
        signal = 10.0 * np.sin(2 * np.pi * STIMULUS_FREQ * t)
    elif channel in ("HHVEL", "hhvel_raw"):
        # Chair velocity: sinusoidal, phase-shifted
        signal = 8.0 * np.sin(2 * np.pi * STIMULUS_FREQ * t + np.pi / 4)
    elif channel == "hepos1":
        # Eye position ch1
        signal = 5.0 * np.sin(2 * np.pi * STIMULUS_FREQ * t + np.pi / 6)
    elif channel == "hepos2":
        # Eye position ch2
        signal = 4.5 * np.sin(2 * np.pi * STIMULUS_FREQ * t + np.pi / 3)
    else:
        signal = np.zeros(num_samples)

    signal += rng.normal(0, 0.3, num_samples)
    return signal.astype(np.float32)


def generate_mock_block_signals(block_index, params):
    """Generate signal arrays for a single block.

    Args:
        block_index: 0-based block index.
        params: dict with lp_cutoff_hz, sg_window_ms, saccade_threshold, etc.

    Returns dict with keys: time, raw_position, filtered_position,
        raw_velocity, filtered_velocity, stimulus, saccade_mask.
        All arrays have shape (60000,).
    """
    rng = np.random.RandomState(1000 + block_index)
    n = SAMPLES_PER_BLOCK
    t = np.arange(n) / SAMPLE_RATE

    # Phase varies by block index
    phase = block_index * 0.05

    # Stimulus: clean sinusoid
    stim_amp = 10.0
    stimulus = stim_amp * np.sin(2 * np.pi * STIMULUS_FREQ * t)

    # Raw position: sinusoidal + noise + occasional saccades
    lp_cutoff = params.get("lp_cutoff_hz", 40.0)
    noise_scale = 80.0 / max(lp_cutoff, 1.0)  # more noise at lower cutoffs
    eye_amp = stim_amp * (0.4 + block_index * 0.008)  # gain ~0.4-0.9
    raw_position = (
        eye_amp * np.sin(2 * np.pi * STIMULUS_FREQ * t + phase)
        + rng.normal(0, noise_scale * 0.15, n)
    )

    # Insert saccade-like transients
    sac_threshold = params.get("saccade_threshold", 50.0)
    num_saccades = max(2, int(5 - sac_threshold / 50.0 * 2))
    num_saccades = min(num_saccades, 8)
    saccade_mask = np.zeros(n, dtype=bool)
    for _ in range(num_saccades):
        sac_start = rng.randint(1000, n - 1000)
        sac_dur = rng.randint(10, 40)
        sac_amp = rng.uniform(3.0, 8.0)
        sac_sign = rng.choice([-1, 1])
        sac_end = min(sac_start + sac_dur, n)
        raw_position[sac_start:sac_end] += sac_sign * sac_amp
        saccade_mask[sac_start:sac_end] = True

    # Filtered position: same but with reduced noise
    filtered_position = (
        eye_amp * np.sin(2 * np.pi * STIMULUS_FREQ * t + phase)
        + rng.normal(0, noise_scale * 0.02, n)
    )

    # Velocity: derivative-like sinusoidal
    sg_window = params.get("sg_window_ms", 30.0)
    vel_noise = 0.5 + 30.0 / max(sg_window, 1.0)
    vel_amp = eye_amp * 2 * np.pi * STIMULUS_FREQ
    raw_velocity = (
        vel_amp * np.cos(2 * np.pi * STIMULUS_FREQ * t + phase)
        + rng.normal(0, vel_noise * 0.5, n)
    )
    filtered_velocity = (
        vel_amp * np.cos(2 * np.pi * STIMULUS_FREQ * t + phase)
        + rng.normal(0, vel_noise * 0.05, n)
    )

    return {
        "time": t.astype(np.float32),
        "raw_position": raw_position.astype(np.float32),
        "filtered_position": filtered_position.astype(np.float32),
        "raw_velocity": raw_velocity.astype(np.float32),
        "filtered_velocity": filtered_velocity.astype(np.float32),
        "stimulus": stimulus.astype(np.float32),
        "saccade_mask": saccade_mask,
    }


def generate_mock_cycle_data(block_index, num_cycles=None):
    """Generate cycle-level analysis data for a block.

    Returns dict with keys: cycle_time, cycle_traces, cycle_average,
        cycle_sem, cycle_fit, stimulus_trace, cycle_quality.
    """
    if num_cycles is None:
        num_cycles = int(BLOCK_DURATION * STIMULUS_FREQ)  # 60

    rng = np.random.RandomState(2000 + block_index)
    cycle_samples = SAMPLE_RATE  # 1 second per cycle at 1 Hz
    cycle_time = np.arange(cycle_samples) / SAMPLE_RATE

    phase = block_index * 0.05
    eye_amp = 10.0 * (0.4 + block_index * 0.008)

    # Individual cycle traces
    cycle_traces = np.zeros((num_cycles, cycle_samples), dtype=np.float32)
    cycle_quality = []

    for c in range(num_cycles):
        base = eye_amp * np.sin(2 * np.pi * STIMULUS_FREQ * cycle_time + phase)
        noise = rng.normal(0, 0.3, cycle_samples)
        cycle_traces[c] = base + noise

        # Quality: random, biased towards good
        is_good = rng.random() > 0.25
        cycle_quality.append(is_good)

    # Average and SEM
    good_mask = np.array(cycle_quality)
    if good_mask.any():
        good_traces = cycle_traces[good_mask]
        cycle_average = good_traces.mean(axis=0)
        cycle_sem = good_traces.std(axis=0) / np.sqrt(good_mask.sum())
    else:
        cycle_average = cycle_traces.mean(axis=0)
        cycle_sem = cycle_traces.std(axis=0) / np.sqrt(num_cycles)

    # Fit: clean sinusoidal
    cycle_fit = eye_amp * np.sin(
        2 * np.pi * STIMULUS_FREQ * cycle_time + phase
    ).astype(np.float32)

    # Stimulus trace
    stimulus_trace = 10.0 * np.sin(
        2 * np.pi * STIMULUS_FREQ * cycle_time
    ).astype(np.float32)

    return {
        "cycle_time": cycle_time.astype(np.float32),
        "cycle_traces": cycle_traces,
        "cycle_average": cycle_average.astype(np.float32),
        "cycle_sem": cycle_sem.astype(np.float32),
        "cycle_fit": cycle_fit,
        "stimulus_trace": stimulus_trace,
        "cycle_quality": cycle_quality,
    }


def generate_mock_block_metrics(block_index):
    """Generate summary metrics for a single block.

    Returns dict with keys: gain, eye_amp, eye_amp_sem, eye_phase,
        eye_phase_sem, stim_amp, freq_hz, good_cycles, total_cycles,
        var_residual, block_index, block_type, block_label.
    """
    rng = np.random.RandomState(3000 + block_index)
    btype = _block_type(block_index)

    gain = 0.4 + block_index * 0.008 + rng.normal(0, 0.02)
    eye_amp = 10.0 * gain
    stim_amp = 10.0
    total_cycles = int(BLOCK_DURATION * STIMULUS_FREQ)
    good_frac = 0.15 + rng.random() * 0.80
    good_cycles = int(total_cycles * good_frac)

    return {
        "block_index": block_index,
        "block_type": btype,
        "block_label": _block_label(block_index),
        "gain": round(gain, 4),
        "eye_amp": round(eye_amp, 2),
        "eye_amp_sem": round(rng.uniform(0.1, 0.5), 3),
        "eye_phase": round(rng.uniform(-15, 15), 2),
        "eye_phase_sem": round(rng.uniform(1.0, 5.0), 2),
        "stim_amp": stim_amp,
        "freq_hz": STIMULUS_FREQ,
        "good_cycles": good_cycles,
        "total_cycles": total_cycles,
        "var_residual": round(rng.uniform(0.01, 0.15), 4),
    }


def generate_mock_results_table():
    """Generate results for all blocks.

    Returns list of 62 block metric dicts.
    """
    return [generate_mock_block_metrics(i) for i in range(NUM_BLOCKS)]
