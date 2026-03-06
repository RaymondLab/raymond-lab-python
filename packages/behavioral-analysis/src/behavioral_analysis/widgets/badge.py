"""Badge: small styled label with color variants."""

from PySide6.QtWidgets import QLabel


# Variant → (background, text color)
_VARIANTS = {
    "green": ("#D6F0E4", "#0F8A5F"),
    "accent": ("#E0EDF5", "#2E5A74"),
    "neutral": ("#EFF2F6", "#4E5A6A"),
    "warning": ("#FFF3CD", "#856404"),
    "error": ("#FAE0E5", "#CF2C2C"),
}

_DARK_VARIANTS = {
    "green": ("#0F3028", "#3BD48A"),
    "accent": ("#1A2C3C", "#70A8CA"),
    "neutral": ("#243040", "#90A0B0"),
    "warning": ("#3A2E10", "#F0B030"),
    "error": ("#3A1422", "#F06B6B"),
}


class Badge(QLabel):
    """Small badge label with preset color variants.

    Variants: 'green', 'accent', 'neutral', 'warning', 'error'.
    """

    def __init__(self, text="", variant="neutral", parent=None):
        super().__init__(text, parent)
        self._variant = variant
        self._dark = False
        self._apply_style()

    def set_variant(self, variant):
        self._variant = variant
        self._apply_style()

    def set_dark(self, dark):
        self._dark = dark
        self._apply_style()

    def _apply_style(self):
        variants = _DARK_VARIANTS if self._dark else _VARIANTS
        bg, fg = variants.get(self._variant, variants["neutral"])
        self.setStyleSheet(
            f"background-color: {bg}; color: {fg}; "
            "font-size: 10px; font-weight: 600; "
            "padding: 2px 6px; border-radius: 3px;"
        )
