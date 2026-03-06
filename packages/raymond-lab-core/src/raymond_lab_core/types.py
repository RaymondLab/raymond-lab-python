from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from numpy.typing import NDArray
from typing import Optional

@dataclass
class Spike2FileHeader:
    """Information extracted from Spike2 file header."""
    recording_date: Optional[datetime] = None
    spike2_version: str
    file_comments: list[str]
    sample_rate: float
    channel_count: int

@dataclass
class Spike2ChannelInfo:
    """Information about each channel in the Spike2 file."""
    channel: int
    title: str
    type: str
    max_time: float
    scale: float
    offset: float
    units: str
    divide: float
    size: int

@dataclass
class Spike2Data:
    """Raw data extracted from Spike2 files."""
    # File metadata
    header: Spike2FileHeader

    # Channel metadata — keyed by channel number or name
    channels: dict[int, Spike2ChannelInfo] = field(default_factory=dict)

    # Analog channels (continuous data)
    HTVEL: NDArray[np.float64]   # Drum (target) velocity command
    HHVEL: NDArray[np.float64]   # Chair (head) velocity command
    HTPOS: NDArray[np.float64]   # Drum (target) position command
    HHPOS: NDArray[np.float64]   # Chair (head) position command
    hepos1: NDArray[np.float64]  # Eye position channel 1 (horizontal)
    hepos2: NDArray[np.float64]  # Eye position channel 2 (horizontal)
    htpos: NDArray[np.float64]   # Drum (target) position feedback
    hhpos: NDArray[np.float64]   # Chair (head) position feedback
    htvel: NDArray[np.float64]   # Drum (target) velocity feedback
    hhvel: NDArray[np.float64]   # Chair (head) velocity feedback

    # Event channels (discrete events)
    TTL: dict[str, NDArray[np.float64]]  # TTL channels (rise/fall times)
    TextMark: list[tuple[float, str]]    # Text markers (tick, label)
    Keyboard: list[tuple[float, str]]    # Keyboard markers (tick, key)