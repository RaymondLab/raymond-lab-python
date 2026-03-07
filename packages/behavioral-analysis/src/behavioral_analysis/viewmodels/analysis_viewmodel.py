"""Single AnalysisViewModel — the sole source of truth for application state."""

from PySide6.QtCore import QObject, QTimer, Signal

from ..analysis import stubs
from ..models.session_model import (
    SessionModel, AnalysisParams, BlockInfo, CalibrationData,
)


class AnalysisViewModel(QObject):
    """Central ViewModel owning a SessionModel and exposing signals for views."""

    # Navigation
    phase_changed = Signal(str)           # "wizard" | "workspace"
    wizard_step_changed = Signal(int)     # 1 | 2 | 3
    workspace_tab_changed = Signal(str)   # "A1" | "A2"

    # File & session
    file_loaded = Signal()
    session_info_changed = Signal()
    block_structure_changed = Signal()
    analysis_type_changed = Signal(str)

    # Calibration
    calibration_changed = Signal()

    # Parameters (active during W3)
    params_changed = Signal()
    filter_method_changed = Signal(str)

    # Selection
    selected_block_changed = Signal(int)
    selected_cycle_changed = Signal(int)
    display_mode_changed = Signal(str)

    # Computation
    block_signals_recomputed = Signal()
    all_results_recomputed = Signal()

    # Metadata
    remaining_fields_changed = Signal(int)

    # Dialog requests
    message_requested = Signal(str, str)
    export_completed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = SessionModel()
        self._phase = "wizard"
        self._wizard_step = 1
        self._workspace_tab = "A1"

        # 80ms debounce timer for param-triggered recomputation
        self._recompute_timer = QTimer(self)
        self._recompute_timer.setSingleShot(True)
        self._recompute_timer.setInterval(80)
        self._recompute_timer.timeout.connect(self._recompute_current_block)

    # ── Property accessors ──

    @property
    def data(self) -> SessionModel:
        return self._data

    @property
    def is_file_loaded(self) -> bool:
        return self._data.is_loaded

    @property
    def params(self) -> AnalysisParams:
        return self._data.params

    @property
    def selected_block(self) -> int:
        return self._data.selected_block

    @property
    def selected_cycle(self) -> int:
        return self._data.selected_cycle

    @property
    def blocks(self) -> list[BlockInfo]:
        return self._data.blocks

    @property
    def calibration(self) -> CalibrationData:
        return self._data.calibration

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def wizard_step(self) -> int:
        return self._wizard_step

    @property
    def workspace_tab(self) -> str:
        return self._workspace_tab

    # ── Navigation ──

    def go_to_wizard_step(self, step: int):
        if self._wizard_step != step:
            self._wizard_step = step
            self.wizard_step_changed.emit(step)
        if step == 3 and self._data.is_loaded:
            self._recompute_current_block()

    def start_analysis(self):
        """Transition from wizard W3 to workspace. Params are now locked."""
        self._data.all_results = None  # force recompute on A2 visit
        self._phase = "workspace"
        self._workspace_tab = "A1"
        self.phase_changed.emit("workspace")
        self.workspace_tab_changed.emit("A1")
        # Recompute current block for A1
        self._recompute_current_block()

    def switch_tab(self, tab: str):
        if self._workspace_tab != tab:
            self._workspace_tab = tab
            self.workspace_tab_changed.emit(tab)
        if tab == "A2":
            self._ensure_all_results_computed()

    def return_to_signal_explorer(self):
        """Return from workspace to W3 for parameter re-tuning."""
        self._phase = "wizard"
        self._wizard_step = 3
        self.phase_changed.emit("wizard")
        self.wizard_step_changed.emit(3)
        self._recompute_current_block()

    def new_analysis(self):
        """Reset everything and return to W1."""
        self._data.reset()
        self._phase = "wizard"
        self._wizard_step = 1
        self.phase_changed.emit("wizard")
        self.wizard_step_changed.emit(1)

    # ── File loading ──

    def load_file(self, path: str):
        session = stubs.load_experiment_file(path)
        self._data.raw = session
        self._data.file_path = path

        # Parse blocks
        self._data.blocks = [
            BlockInfo(
                index=b["index"],
                label=b["label"],
                block_type=b["type"],
                start_time=b["start_time"],
                end_time=b["end_time"],
                freq_hz=b["freq_hz"],
            )
            for b in session.get("blocks", [])
        ]

        # Auto-populate metadata from session defaults
        defaults = session.get("metadata_defaults", {})
        for key, value in defaults.items():
            self._data.metadata.set(key, str(value))

        self._data.selected_block = 0
        self._data.selected_cycle = 0

        self.file_loaded.emit()
        self.session_info_changed.emit()
        self.block_structure_changed.emit()
        self.remaining_fields_changed.emit(self._data.metadata.count_remaining())

    def set_analysis_type(self, analysis_type: str):
        if self._data.analysis_type != analysis_type:
            self._data.analysis_type = analysis_type
            self.analysis_type_changed.emit(analysis_type)

    # ── Block management ──

    def select_block(self, index: int):
        if self._data.selected_block != index:
            self._data.selected_block = index
            self._data.selected_cycle = 0
            self.selected_block_changed.emit(index)
            self._recompute_current_block()

    def update_block_label(self, index: int, label: str):
        if 0 <= index < len(self._data.blocks):
            self._data.blocks[index].label = label
            self.block_structure_changed.emit()

    def select_cycle(self, index: int):
        if self._data.selected_cycle != index:
            self._data.selected_cycle = index
            self.selected_cycle_changed.emit(index)

    def set_display_mode(self, mode: str):
        if self._data.display_mode != mode:
            self._data.display_mode = mode
            self.display_mode_changed.emit(mode)

    # ── Calibration ──

    def load_calibration_file(self, path: str):
        result = stubs.apply_calibration(self._data.raw, path)
        self._data.calibration = CalibrationData(
            source="file",
            file_path=path,
            scale_ch1=result["scale_ch1"],
            scale_ch2=result["scale_ch2"],
            active_channel=result["active_channel"],
        )
        self.calibration_changed.emit()

    def set_manual_calibration(self, s1: float, s2: float, active: str):
        self._data.calibration = CalibrationData(
            source="manual",
            scale_ch1=s1,
            scale_ch2=s2,
            active_channel=active,
        )
        self.calibration_changed.emit()

    # ── Parameters (active only during W3) ──

    def set_filter_method(self, method: str):
        if self._data.params.filter_method != method:
            self._data.params.filter_method = method
            self.filter_method_changed.emit(method)
            self.params_changed.emit()
            self._recompute_timer.start()

    def set_lp_cutoff(self, value: float):
        if self._data.params.lp_cutoff_hz != value:
            self._data.params.lp_cutoff_hz = value
            self.params_changed.emit()
            self._recompute_timer.start()

    def set_sg_window(self, value: float):
        if self._data.params.sg_window_ms != value:
            self._data.params.sg_window_ms = value
            self.params_changed.emit()
            self._recompute_timer.start()

    def set_saccade_method(self, method: str):
        if self._data.params.saccade_method != method:
            self._data.params.saccade_method = method
            self.params_changed.emit()
            self._recompute_timer.start()

    def set_saccade_threshold(self, value: float):
        if self._data.params.saccade_threshold != value:
            self._data.params.saccade_threshold = value
            self.params_changed.emit()
            self._recompute_timer.start()

    def set_saccade_min_dur(self, value: float):
        if self._data.params.saccade_min_dur_ms != value:
            self._data.params.saccade_min_dur_ms = value
            self.params_changed.emit()
            self._recompute_timer.start()

    def set_saccade_padding(self, value: float):
        if self._data.params.saccade_padding_ms != value:
            self._data.params.saccade_padding_ms = value
            self.params_changed.emit()
            self._recompute_timer.start()

    def set_eye_channel(self, channel: str):
        if self._data.params.eye_channel != channel:
            self._data.params.eye_channel = channel
            self.params_changed.emit()
            self._recompute_timer.start()

    def reset_params_to_defaults(self):
        self._data.params = AnalysisParams()
        self.params_changed.emit()
        self.filter_method_changed.emit(self._data.params.filter_method)
        self._recompute_timer.start()

    # ── Metadata ──

    def update_metadata_field(self, name: str, value: str):
        self._data.metadata.set(name, value)
        self.remaining_fields_changed.emit(self._data.metadata.count_remaining())

    # ── Computation ──

    def _recompute_current_block(self):
        if not self._data.is_loaded:
            return

        params_dict = self._data.params.to_dict()
        block_index = self._data.selected_block

        self._data.current_block_signals = stubs.process_block(
            self._data.raw, block_index, params_dict
        )
        self._data.current_cycle_data = stubs.compute_cycle_analysis(
            self._data.raw, block_index, params_dict
        )
        self._data.current_block_metrics = stubs.compute_block_metrics(
            self._data.raw, block_index, params_dict
        )

        # Invalidate all-results cache when params change
        self._data.all_results = None

        self.block_signals_recomputed.emit()

    def _ensure_all_results_computed(self):
        if self._data.all_results is None and self._data.is_loaded:
            params_dict = self._data.params.to_dict()
            self._data.all_results = stubs.compute_all_results(
                self._data.raw, params_dict
            )
            self.all_results_recomputed.emit()

    # ── Export ──

    def export_excel(self, path: str):
        if self._data.all_results:
            stubs.export_excel(self._data.all_results, path)
            self.export_completed.emit(path)

    def export_figures(self, path: str):
        if self._data.all_results:
            stubs.export_figures(self._data.all_results, path)
            self.export_completed.emit(path)

    def export_workspace(self, path: str):
        if self._data.all_results:
            stubs.export_workspace(self._data.all_results, path)
            self.export_completed.emit(path)

    def export_all(self, folder: str):
        self._ensure_all_results_computed()
        self.export_excel(folder + "_results.xlsx")
        self.export_figures(folder + "_figures.pdf")
        self.export_workspace(folder + "_workspace.mat")
