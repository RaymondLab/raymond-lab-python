"""Centralized application state with Qt signals for cross-component synchronization."""

from PySide6.QtCore import QObject, Signal


class AppState(QObject):
    """Central state object that all screens read/write.

    Properties emit signals on change so that UI components can react.
    Use QSignalBlocker when setting values programmatically to prevent loops.
    """

    # Navigation signals
    phase_changed = Signal(str)          # "wizard" or "workspace"
    wizard_step_changed = Signal(int)    # 1 or 2
    workspace_tab_changed = Signal(str)  # "A1", "A2", "A3"
    settings_open_changed = Signal(bool)

    # Data signals
    file_loaded_changed = Signal(bool)
    file_path_changed = Signal(str)
    analysis_type_changed = Signal(str)
    session_data_changed = Signal(object)

    # Calibration signals
    calibration_loaded_changed = Signal(bool)
    calibration_source_changed = Signal(str)
    scale_ch1_changed = Signal(object)  # float or None
    scale_ch2_changed = Signal(object)  # float or None
    active_channel_changed = Signal(str)

    # Block/cycle selection signals
    selected_block_changed = Signal(int)
    selected_cycle_changed = Signal(int)
    display_mode_changed = Signal(str)

    # Analysis parameter signals
    filter_method_changed = Signal(str)
    lp_cutoff_hz_changed = Signal(float)
    sg_window_ms_changed = Signal(float)
    saccade_method_changed = Signal(str)
    saccade_threshold_changed = Signal(float)
    saccade_min_dur_ms_changed = Signal(float)
    saccade_padding_ms_changed = Signal(float)
    parameters_changed = Signal()  # Emitted when any analysis parameter changes

    # Appearance signals
    dark_mode_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Navigation state
        self._phase = "wizard"
        self._wizard_step = 1
        self._workspace_tab = "A1"
        self._settings_open = False

        # Data state
        self._file_loaded = False
        self._file_path = ""
        self._analysis_type = "Standard VOR"
        self._session_data = None

        # Calibration state
        self._calibration_loaded = False
        self._calibration_source = "file"
        self._scale_ch1 = None
        self._scale_ch2 = None
        self._active_channel = "Auto"

        # Block/cycle selection
        self._selected_block = 0
        self._selected_cycle = 0
        self._display_mode = "SEM"

        # Analysis parameters
        self._filter_method = "Butterworth"
        self._lp_cutoff_hz = 40.0
        self._sg_window_ms = 30.0
        self._saccade_method = "SVT"
        self._saccade_threshold = 50.0
        self._saccade_min_dur_ms = 10.0
        self._saccade_padding_ms = 5.0

        # Appearance
        self._dark_mode = False

        # Metadata (stored as dict, not individually signaled)
        self.metadata = {}

    # --- Navigation properties ---

    @property
    def phase(self):
        return self._phase

    @phase.setter
    def phase(self, value):
        if self._phase != value:
            self._phase = value
            self.phase_changed.emit(value)

    @property
    def wizard_step(self):
        return self._wizard_step

    @wizard_step.setter
    def wizard_step(self, value):
        if self._wizard_step != value:
            self._wizard_step = value
            self.wizard_step_changed.emit(value)

    @property
    def workspace_tab(self):
        return self._workspace_tab

    @workspace_tab.setter
    def workspace_tab(self, value):
        if self._workspace_tab != value:
            self._workspace_tab = value
            self.workspace_tab_changed.emit(value)

    @property
    def settings_open(self):
        return self._settings_open

    @settings_open.setter
    def settings_open(self, value):
        if self._settings_open != value:
            self._settings_open = value
            self.settings_open_changed.emit(value)

    # --- Data properties ---

    @property
    def file_loaded(self):
        return self._file_loaded

    @file_loaded.setter
    def file_loaded(self, value):
        if self._file_loaded != value:
            self._file_loaded = value
            self.file_loaded_changed.emit(value)

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        if self._file_path != value:
            self._file_path = value
            self.file_path_changed.emit(value)

    @property
    def analysis_type(self):
        return self._analysis_type

    @analysis_type.setter
    def analysis_type(self, value):
        if self._analysis_type != value:
            self._analysis_type = value
            self.analysis_type_changed.emit(value)

    @property
    def session_data(self):
        return self._session_data

    @session_data.setter
    def session_data(self, value):
        self._session_data = value
        self.session_data_changed.emit(value)

    # --- Calibration properties ---

    @property
    def calibration_loaded(self):
        return self._calibration_loaded

    @calibration_loaded.setter
    def calibration_loaded(self, value):
        if self._calibration_loaded != value:
            self._calibration_loaded = value
            self.calibration_loaded_changed.emit(value)

    @property
    def calibration_source(self):
        return self._calibration_source

    @calibration_source.setter
    def calibration_source(self, value):
        if self._calibration_source != value:
            self._calibration_source = value
            self.calibration_source_changed.emit(value)

    @property
    def scale_ch1(self):
        return self._scale_ch1

    @scale_ch1.setter
    def scale_ch1(self, value):
        if self._scale_ch1 != value:
            self._scale_ch1 = value
            self.scale_ch1_changed.emit(value)

    @property
    def scale_ch2(self):
        return self._scale_ch2

    @scale_ch2.setter
    def scale_ch2(self, value):
        if self._scale_ch2 != value:
            self._scale_ch2 = value
            self.scale_ch2_changed.emit(value)

    @property
    def active_channel(self):
        return self._active_channel

    @active_channel.setter
    def active_channel(self, value):
        if self._active_channel != value:
            self._active_channel = value
            self.active_channel_changed.emit(value)

    # --- Block/cycle selection properties ---

    @property
    def selected_block(self):
        return self._selected_block

    @selected_block.setter
    def selected_block(self, value):
        if self._selected_block != value:
            self._selected_block = value
            self.selected_block_changed.emit(value)

    @property
    def selected_cycle(self):
        return self._selected_cycle

    @selected_cycle.setter
    def selected_cycle(self, value):
        if self._selected_cycle != value:
            self._selected_cycle = value
            self.selected_cycle_changed.emit(value)

    @property
    def display_mode(self):
        return self._display_mode

    @display_mode.setter
    def display_mode(self, value):
        if self._display_mode != value:
            self._display_mode = value
            self.display_mode_changed.emit(value)

    # --- Analysis parameter properties ---

    @property
    def filter_method(self):
        return self._filter_method

    @filter_method.setter
    def filter_method(self, value):
        if self._filter_method != value:
            self._filter_method = value
            self.filter_method_changed.emit(value)
            self.parameters_changed.emit()

    @property
    def lp_cutoff_hz(self):
        return self._lp_cutoff_hz

    @lp_cutoff_hz.setter
    def lp_cutoff_hz(self, value):
        if self._lp_cutoff_hz != value:
            self._lp_cutoff_hz = value
            self.lp_cutoff_hz_changed.emit(value)
            self.parameters_changed.emit()

    @property
    def sg_window_ms(self):
        return self._sg_window_ms

    @sg_window_ms.setter
    def sg_window_ms(self, value):
        if self._sg_window_ms != value:
            self._sg_window_ms = value
            self.sg_window_ms_changed.emit(value)
            self.parameters_changed.emit()

    @property
    def saccade_method(self):
        return self._saccade_method

    @saccade_method.setter
    def saccade_method(self, value):
        if self._saccade_method != value:
            self._saccade_method = value
            self.saccade_method_changed.emit(value)
            self.parameters_changed.emit()

    @property
    def saccade_threshold(self):
        return self._saccade_threshold

    @saccade_threshold.setter
    def saccade_threshold(self, value):
        if self._saccade_threshold != value:
            self._saccade_threshold = value
            self.saccade_threshold_changed.emit(value)
            self.parameters_changed.emit()

    @property
    def saccade_min_dur_ms(self):
        return self._saccade_min_dur_ms

    @saccade_min_dur_ms.setter
    def saccade_min_dur_ms(self, value):
        if self._saccade_min_dur_ms != value:
            self._saccade_min_dur_ms = value
            self.saccade_min_dur_ms_changed.emit(value)
            self.parameters_changed.emit()

    @property
    def saccade_padding_ms(self):
        return self._saccade_padding_ms

    @saccade_padding_ms.setter
    def saccade_padding_ms(self, value):
        if self._saccade_padding_ms != value:
            self._saccade_padding_ms = value
            self.saccade_padding_ms_changed.emit(value)
            self.parameters_changed.emit()

    # --- Appearance properties ---

    @property
    def dark_mode(self):
        return self._dark_mode

    @dark_mode.setter
    def dark_mode(self, value):
        if self._dark_mode != value:
            self._dark_mode = value
            self.dark_mode_changed.emit(value)

    # --- Utility methods ---

    def current_params(self):
        """Return current analysis parameters as a dict for passing to stubs."""
        return {
            "filter_method": self._filter_method,
            "lp_cutoff_hz": self._lp_cutoff_hz,
            "sg_window_ms": self._sg_window_ms,
            "saccade_method": self._saccade_method,
            "saccade_threshold": self._saccade_threshold,
            "saccade_min_dur_ms": self._saccade_min_dur_ms,
            "saccade_padding_ms": self._saccade_padding_ms,
        }

    def reset_parameters(self):
        """Reset all analysis parameters to default values."""
        self.filter_method = "Butterworth"
        self.lp_cutoff_hz = 40.0
        self.sg_window_ms = 30.0
        self.saccade_method = "SVT"
        self.saccade_threshold = 50.0
        self.saccade_min_dur_ms = 10.0
        self.saccade_padding_ms = 5.0

    def reset_workspace(self):
        """Reset all workspace state for a new analysis."""
        self._file_loaded = False
        self._file_path = ""
        self._session_data = None
        self._calibration_loaded = False
        self._scale_ch1 = None
        self._scale_ch2 = None
        self._selected_block = 0
        self._selected_cycle = 0
        self._display_mode = "SEM"
        self.reset_parameters()
        self.metadata = {}
        self.phase = "wizard"
        self.wizard_step = 1
