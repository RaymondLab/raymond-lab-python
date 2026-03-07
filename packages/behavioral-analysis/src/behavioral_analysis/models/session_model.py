"""Pure-Python dataclasses for the behavioral analysis data model.

No Qt imports — these are serializable, testable value objects.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AnalysisParams:
    """Parameters controlling signal processing and saccade detection."""

    filter_method: str = "Butterworth"
    lp_cutoff_hz: float = 11.0
    wavelet_level: int = 5
    wavelet_name: str = "sym4"
    wavelet_method: str = "BlockJS"
    sg_window_ms: float = 11.0
    saccade_method: str = "SVT"
    saccade_threshold: float = 1000.0
    saccade_min_dur_ms: float = 10.0
    saccade_padding_ms: float = 5.0
    eye_channel: str = "Auto"

    def to_dict(self) -> dict:
        """Convert to dict for passing to stubs API."""
        return {
            "filter_method": self.filter_method,
            "lp_cutoff_hz": self.lp_cutoff_hz,
            "sg_window_ms": self.sg_window_ms,
            "saccade_method": self.saccade_method,
            "saccade_threshold": self.saccade_threshold,
            "saccade_min_dur_ms": self.saccade_min_dur_ms,
            "saccade_padding_ms": self.saccade_padding_ms,
        }


@dataclass
class BlockInfo:
    """Metadata for a single experimental block."""

    index: int
    label: str
    block_type: str  # "pre", "post", or "train"
    start_time: float
    end_time: float
    freq_hz: float


@dataclass
class CalibrationData:
    """Calibration state."""

    source: str = "none"  # "none", "file", "manual"
    file_path: str = ""
    scale_ch1: Optional[float] = None
    scale_ch2: Optional[float] = None
    active_channel: str = "Auto"

    @property
    def is_loaded(self) -> bool:
        return self.source != "none"


METADATA_FIELD_DEFS = {
    "Subject Information": [
        ("subject_id", "Mouse ID", True, "subject_id", "line", 125, None),
        ("species", "Species", False, "species", "line", 105, None),
        ("strain", "Strain", True, None, "combo", 110,
         ["C57BL/6J", "C57BL/6N", "BALB/c", "Other"]),
        ("sex", "Sex", True, None, "combo", 75, ["Male", "Female"]),
        ("age", "Age", False, None, "line", 70, None),
        ("weight_g", "Wt (g)", False, None, "line", 65, None),
        ("genotype", "Genotype", True, None, "combo", 90,
         ["WT", "Het", "Hom", "Other"]),
    ],
    "Session Information": [
        ("session_date", "Date", True, "session_date", "line", 110, None),
        ("session_start_time", "Start", True, "session_start_time", "line", 90, None),
        ("experimenter", "Experimenter", True, None, "combo", 130,
         ["Select...", "Dr. Smith", "Dr. Jones", "Other"]),
        ("lab", "Lab", False, "lab", "line", 125, None),
        ("institution", "Institution", False, "institution", "line", 145, None),
        ("experiment_description", "Description", False, None, "line", 200, None),
    ],
    "Experiment Details": [
        ("cohort", "Cohort", True, None, "line", 105, None),
        ("subject_condition", "Condition", True, None, "combo", 90,
         ["WT", "KO", "Het", "Control"]),
        ("task_condition", "Task", True, "task_condition", "combo", 120,
         ["Std VOR", "OKR", "VORD", "Custom"]),
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

REQUIRED_METADATA_FIELDS = [
    key
    for fields in METADATA_FIELD_DEFS.values()
    for key, _, required, *_ in fields
    if required
]


@dataclass
class MetadataFields:
    """User-entered metadata for the session."""

    values: dict = field(default_factory=dict)

    def get(self, key: str) -> str:
        return self.values.get(key, "")

    def set(self, key: str, value: str):
        self.values[key] = value

    def count_remaining(self) -> int:
        count = 0
        for key in REQUIRED_METADATA_FIELDS:
            val = self.values.get(key, "")
            if not val or val == "Select...":
                count += 1
        return count

    def is_complete(self) -> bool:
        return self.count_remaining() == 0


@dataclass
class BlockResults:
    """Computed metrics for a single block."""

    block_index: int = 0
    block_type: str = ""
    block_label: str = ""
    gain: float = 0.0
    eye_amp: float = 0.0
    eye_amp_sem: float = 0.0
    eye_phase: float = 0.0
    eye_phase_sem: float = 0.0
    stim_amp: float = 0.0
    freq_hz: float = 0.0
    good_cycles: int = 0
    total_cycles: int = 0
    var_residual: float = 0.0


@dataclass
class SessionModel:
    """Top-level data container for the entire analysis session."""

    # Raw session dict from stubs.load_experiment_file()
    raw: Optional[dict] = None

    # Parsed block structure
    blocks: list[BlockInfo] = field(default_factory=list)

    # Analysis configuration
    params: AnalysisParams = field(default_factory=AnalysisParams)
    calibration: CalibrationData = field(default_factory=CalibrationData)
    metadata: MetadataFields = field(default_factory=MetadataFields)

    # Navigation / selection
    file_path: str = ""
    analysis_type: str = "Standard VOR"
    selected_block: int = 0
    selected_cycle: int = 0
    display_mode: str = "SEM"

    # Cached computation results for current block
    current_block_signals: Optional[dict] = None  # from stubs.process_block()
    current_cycle_data: Optional[dict] = None  # from stubs.compute_cycle_analysis()
    current_block_metrics: Optional[dict] = None  # from stubs.compute_block_metrics()

    # All-blocks results (for A2 Results Summary)
    all_results: Optional[list] = None

    @property
    def is_loaded(self) -> bool:
        return self.raw is not None

    @property
    def num_blocks(self) -> int:
        return len(self.blocks)

    @property
    def sample_rate(self) -> int:
        if self.raw:
            return self.raw.get("sample_rate", 0)
        return 0

    @property
    def duration(self) -> float:
        if self.raw:
            return self.raw.get("duration", 0.0)
        return 0.0

    def reset(self):
        """Reset all state for a new analysis."""
        self.raw = None
        self.blocks.clear()
        self.params = AnalysisParams()
        self.calibration = CalibrationData()
        self.metadata = MetadataFields()
        self.file_path = ""
        self.analysis_type = "Standard VOR"
        self.selected_block = 0
        self.selected_cycle = 0
        self.display_mode = "SEM"
        self.current_block_signals = None
        self.current_cycle_data = None
        self.current_block_metrics = None
        self.all_results = None
