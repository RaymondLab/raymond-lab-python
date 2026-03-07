"""Light-mode theme color dictionary and QSS stylesheet generation."""

THEME = {
    # UI Chrome
    "bgApp": "#E8ECF0",
    "bgPanel": "#FFFFFF",
    "bgPanelAlt": "#EFF2F6",
    "bgInput": "#FFFFFF",
    "bgTopbar": "#263040",
    "bgTabActive": "#3E6E8C",
    "bgTabInactive": "#324050",
    "bgCalibration": "#EFF4F8",
    "bgParamBar": "#F3F6F9",
    "bgPlot": "#F8FAFB",
    # Borders
    "border": "#CDD4DC",
    "borderLight": "#DFE4EA",
    "borderFocus": "#3E6E8C",
    # Text
    "textPrimary": "#1A2230",
    "textSecondary": "#4E5A6A",
    "textTertiary": "#8490A0",
    "textInverse": "#FFFFFF",
    "textOnTopbar": "#A8B4C2",
    # Accent
    "accent": "#3E6E8C",
    "accentDark": "#2E5A74",
    "accentLight": "#E0EDF5",
    "accentText": "#2E5A74",
    # Signal trace colors
    "dataPosition": "#E8690B",
    "dataVelocity": "#2563EB",
    "dataSaccade": "#D42A2A",
    "dataStimulus": "#8490A0",
    "dataFit": "#1A2230",
    "dataRaw": "#BCC4CE",
    "dataSem": "#D6E4F7",
    # Block & quality colors
    "blockPrepost": "#0F8A5F",
    "blockPrepostBg": "#D6F0E4",
    "blockTrain": "#CF2C4A",
    "blockTrainBg": "#FAE0E5",
    "qualGood": "#1A9E50",
    "qualWarn": "#D4930D",
    "qualBad": "#CF2C2C",
    "qualSelected": "#2D5FD4",
    # Typography tokens
    "fontMono": "'Consolas', 'SF Mono', 'Menlo', monospace",
    "fontXs": "9px",
    "fontSm": "11px",
    "fontMd": "12px",
    "fontLg": "14px",
}


def generate_stylesheet(theme):
    """Generate a QSS stylesheet from a theme dictionary."""
    t = theme
    return f"""
    QMainWindow {{
        background-color: {t['bgApp']};
    }}
    QWidget {{
        font-family: "Segoe UI", "SF Pro Text", system-ui, sans-serif;
        font-size: 12px;
        color: {t['textPrimary']};
        background-color: {t['bgApp']};
    }}
    QDialog, QMessageBox, QProgressDialog {{
        background-color: {t['bgPanel']};
        color: {t['textPrimary']};
    }}
    QGroupBox {{
        background-color: {t['bgPanel']};
        border: 1px solid {t['border']};
        border-radius: 3px;
        padding: 8px;
        margin-top: 6px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 4px;
        color: {t['textSecondary']};
        font-weight: 700;
        font-size: 10px;
    }}
    QPushButton {{
        background-color: {t['bgPanel']};
        border: 1px solid {t['border']};
        border-radius: 3px;
        padding: 5px 14px;
        color: {t['textSecondary']};
        font-weight: 600;
        font-size: 12px;
    }}
    QPushButton:hover {{
        border-color: {t['accent']};
    }}
    QPushButton:pressed {{
        background-color: {t['bgPanelAlt']};
    }}
    QPushButton:disabled {{
        opacity: 0.4;
        color: {t['textTertiary']};
    }}
    QPushButton[primary="true"] {{
        background-color: {t['accent']};
        border: 1px solid {t['accentDark']};
        color: {t['textInverse']};
    }}
    QPushButton[primary="true"]:hover {{
        background-color: {t['accentDark']};
    }}
    QPushButton[primary="true"]:disabled {{
        opacity: 0.4;
    }}
    QLineEdit {{
        background-color: {t['bgInput']};
        border: 1px solid {t['border']};
        border-radius: 3px;
        padding: 4px 7px;
        color: {t['textPrimary']};
        font-size: 12px;
    }}
    QLineEdit:focus {{
        border-color: {t['borderFocus']};
    }}
    QLineEdit:read-only {{
        background-color: {t['bgPanelAlt']};
    }}
    QComboBox {{
        background-color: {t['bgInput']};
        border: 1px solid {t['border']};
        border-radius: 3px;
        padding: 4px 7px;
        color: {t['textPrimary']};
        font-size: 12px;
    }}
    QComboBox:focus {{
        border-color: {t['borderFocus']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 16px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['bgPanel']};
        border: 1px solid {t['border']};
        selection-background-color: {t['accentLight']};
        selection-color: {t['textPrimary']};
    }}
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: {t['bgApp']};
        width: 8px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {t['border']};
        border-radius: 4px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: {t['bgApp']};
        height: 8px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {t['border']};
        border-radius: 4px;
        min-width: 20px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QSlider::groove:horizontal {{
        height: 4px;
        background: {t['border']};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 14px;
        height: 14px;
        margin: -5px 0;
        background: {t['accent']};
        border: 2px solid {t['bgPanel']};
        border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: {t['accent']};
        border-radius: 2px;
    }}
    QTableView {{
        background-color: {t['bgPanel']};
        border: 1px solid {t['border']};
        gridline-color: {t['borderLight']};
        selection-background-color: {t['accentLight']};
        selection-color: {t['textPrimary']};
    }}
    QHeaderView::section {{
        background-color: {t['bgPanelAlt']};
        border: none;
        border-bottom: 1px solid {t['border']};
        border-right: 1px solid {t['borderLight']};
        padding: 5px;
        font-weight: 700;
        font-size: 11px;
        color: {t['textSecondary']};
    }}
    QCheckBox {{
        spacing: 6px;
        color: {t['textPrimary']};
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {t['border']};
        border-radius: 3px;
        background-color: {t['bgInput']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {t['accent']};
        border-color: {t['accentDark']};
    }}
    QSplitter::handle {{
        background-color: {t['border']};
    }}
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    QSplitter::handle:vertical {{
        height: 1px;
    }}
    QLabel {{
        background: transparent;
    }}
    QMenu {{
        background-color: {t['bgPanel']};
        border: 1px solid {t['border']};
        color: {t['textPrimary']};
        padding: 4px 0;
    }}
    QMenu::item {{
        padding: 4px 20px;
    }}
    QMenu::item:selected {{
        background-color: {t['accentLight']};
        color: {t['textPrimary']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {t['border']};
        margin: 4px 8px;
    }}
    QFrame[frameShape="4"] {{
        color: {t['border']};
    }}
    QFrame[frameShape="5"] {{
        color: {t['border']};
    }}
    #workspaceToolbar {{
        background-color: {t['bgTopbar']};
    }}
    #workspaceToolbar QLabel {{
        color: {t['textOnTopbar']};
    }}
    #paramBar {{
        background-color: {t['bgParamBar']};
        border: 1px solid {t['borderLight']};
        border-radius: 3px;
    }}
    #sectionHeader {{
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: {t['textTertiary']};
    }}
    [monospace="true"] {{
        font-family: {t['fontMono']};
    }}
    #w1SummaryBar {{
        background-color: {t['bgPanelAlt']};
        border: 1px solid {t['borderLight']};
        border-radius: 3px;
    }}
    #w1ControlBar {{
        background-color: {t['bgTopbar']};
        border: 1px solid {t['bgTopbar']};
        border-radius: 3px;
    }}
    #w1ControlBar QLabel {{
        color: {t['textOnTopbar']};
    }}
    #w1ControlBar QLineEdit {{
        background-color: {t['bgTabInactive']};
        border: 1px solid rgba(255,255,255,0.15);
        color: {t['textInverse']};
    }}
    #w1ControlBar QLineEdit:focus {{
        border-color: {t['bgTabActive']};
    }}
    #w1ControlBar QComboBox {{
        background-color: {t['bgTabInactive']};
        border: 1px solid rgba(255,255,255,0.15);
        color: {t['textInverse']};
    }}
    #w1ControlBar QPushButton {{
        background-color: transparent;
        border: 1px solid rgba(255,255,255,0.2);
        color: {t['textOnTopbar']};
    }}
    #w1ControlBar QPushButton:hover {{
        border-color: rgba(255,255,255,0.4);
        color: {t['textInverse']};
    }}
    #w1ControlBar QPushButton[primary="true"] {{
        background-color: {t['bgTabActive']};
        border: 1px solid {t['accent']};
        color: {t['textInverse']};
    }}
    #w1ControlBar QPushButton[primary="true"]:hover {{
        background-color: {t['accent']};
    }}
    #w1ControlBar QPushButton[primary="true"]:disabled {{
        opacity: 0.4;
    }}
    """


def apply_theme(app):
    """Apply the light theme stylesheet to the QApplication."""
    app.setStyleSheet(generate_stylesheet(THEME))
