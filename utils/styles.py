"""Shared PyQt6 Styles & Base Widgets"""
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QHBoxLayout, QVBoxLayout,
    QMessageBox, QDialog, QFormLayout, QComboBox, QTextEdit,
    QDateEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QPainter

# ─── Color Palette ──────────────────────────────────────────────────────────────
COLORS = {
    "bg_dark":     "#0d1117",
    "bg_card":     "#161b22",
    "bg_input":    "#21262d",
    "bg_hover":    "#30363d",
    "border":      "#30363d",
    "accent":      "#2ea043",
    "accent_blue": "#1f6feb",
    "accent_red":  "#da3633",
    "accent_orange":"#d29922",
    "text_primary":"#e6edf3",
    "text_muted":  "#8b949e",
    "text_link":   "#58a6ff",
    "sidebar_bg":  "#0d1117",
    "sidebar_sel": "#1f6feb",
    "white":       "#ffffff",
    "success":     "#2ea043",
    "warning":     "#d29922",
    "danger":      "#da3633",
    "info":        "#1f6feb",
    "teal":        "#0d9488",
}

APP_STYLE = f"""
QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    font-family: "Segoe UI", "SF Pro Display", sans-serif;
    font-size: 13px;
}}
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}
QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['bg_hover']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar:horizontal {{
    background: {COLORS['bg_dark']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['bg_hover']};
    border-radius: 4px;
}}
QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS['text_primary']};
    font-size: 13px;
    selection-background-color: {COLORS['accent_blue']};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border: 1px solid {COLORS['accent_blue']};
    outline: none;
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_input']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent_blue']};
    color: {COLORS['text_primary']};
}}
QPushButton {{
    background-color: {COLORS['accent_blue']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 9px 20px;
    font-weight: 600;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: #388bfd;
}}
QPushButton:pressed {{
    background-color: #1158c7;
}}
QPushButton:disabled {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_muted']};
}}
QPushButton[class="danger"] {{
    background-color: {COLORS['accent_red']};
}}
QPushButton[class="danger"]:hover {{ background-color: #f85149; }}
QPushButton[class="success"] {{
    background-color: {COLORS['accent']};
}}
QPushButton[class="success"]:hover {{ background-color: #3fb950; }}
QPushButton[class="warning"] {{
    background-color: {COLORS['accent_orange']};
}}
QPushButton[class="ghost"] {{
    background-color: transparent;
    border: 1px solid {COLORS['border']};
    color: {COLORS['text_primary']};
}}
QPushButton[class="ghost"]:hover {{
    background-color: {COLORS['bg_hover']};
}}
QTableWidget {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    selection-background-color: {COLORS['accent_blue']};
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 12px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: rgba(31, 111, 235, 0.3);
    color: {COLORS['text_primary']};
}}
QHeaderView::section {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_muted']};
    padding: 10px 12px;
    border: none;
    border-right: 1px solid {COLORS['border']};
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QLabel {{
    background: transparent;
    color: {COLORS['text_primary']};
}}
QFrame {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}
QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border-radius: 3px;
    border: 1px solid {COLORS['border']};
    background: {COLORS['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_blue']};
    border-color: {COLORS['accent_blue']};
}}
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background: {COLORS['bg_card']};
}}
QTabBar::tab {{
    background: {COLORS['bg_input']};
    color: {COLORS['text_muted']};
    padding: 10px 20px;
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-radius: 6px 6px 0 0;
}}
QTabBar::tab:selected {{
    background: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border-bottom: 2px solid {COLORS['accent_blue']};
}}
QSplitter::handle {{
    background-color: {COLORS['border']};
}}
QToolTip {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}
"""

def card(parent=None) -> QFrame:
    f = QFrame(parent)
    f.setFrameShape(QFrame.Shape.StyledPanel)
    return f

def heading(text: str, size: int = 16, parent=None) -> QLabel:
    lbl = QLabel(text, parent)
    font = QFont()
    font.setPointSize(size)
    font.setBold(True)
    lbl.setFont(font)
    lbl.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; border: none;")
    return lbl

def subtext(text: str, parent=None) -> QLabel:
    lbl = QLabel(text, parent)
    lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent; border: none;")
    return lbl

def btn(text: str, cls: str = "", parent=None) -> QPushButton:
    b = QPushButton(text, parent)
    if cls:
        b.setProperty("class", cls)
    return b

def stat_card(title: str, value: str, color: str = COLORS["accent_blue"], parent=None) -> QFrame:
    f = QFrame(parent)
    f.setFixedHeight(110)
    f.setStyleSheet(f"""
        QFrame {{
            background-color: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            border-left: 4px solid {color};
        }}
    """)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(20, 16, 20, 16)
    lay.setSpacing(4)
    t = QLabel(title, f)
    t.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
    v = QLabel(value, f)
    v.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 700; background: transparent; border: none;")
    lay.addWidget(t)
    lay.addWidget(v)
    return f

def make_table(columns: list[str], parent=None) -> QTableWidget:
    t = QTableWidget(0, len(columns), parent)
    t.setHorizontalHeaderLabels(columns)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    t.setAlternatingRowColors(True)
    t.setStyleSheet(APP_STYLE + """
        QTableWidget { alternate-background-color: rgba(48, 54, 61, 0.5); }
    """)
    t.verticalHeader().setVisible(False)
    t.setShowGrid(False)
    return t

def fill_table(table: QTableWidget, rows: list[list]):
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            item = QTableWidgetItem(str(val) if val is not None else "—")
            item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            table.setItem(r, c, item)
    table.resizeRowsToContents()

def confirm_dialog(parent, title: str, message: str) -> bool:
    reply = QMessageBox.question(parent, title, message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No)
    return reply == QMessageBox.StandardButton.Yes

def show_error(parent, msg: str):
    QMessageBox.critical(parent, "Error", msg)

def show_success(parent, msg: str):
    QMessageBox.information(parent, "Success", msg)

class Badge(QLabel):
    STATUS_COLORS = {
        "Scheduled":  ("#dbeafe", "#1d4ed8"),
        "Completed":  ("#dcfce7", "#15803d"),
        "Cancelled":  ("#fee2e2", "#b91c1c"),
        "No Show":    ("#fef9c3", "#854d0e"),
        "Admitted":   ("#dbeafe", "#1d4ed8"),
        "Discharged": ("#dcfce7", "#15803d"),
        "Pending":    ("#fef9c3", "#854d0e"),
        "Partial":    ("#ffedd5", "#c2410c"),
        "Paid":       ("#dcfce7", "#15803d"),
        "Active":     ("#dcfce7", "#15803d"),
        "Inactive":   ("#fee2e2", "#b91c1c"),
    }

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        bg, fg = self.STATUS_COLORS.get(text, ("#e5e7eb", "#374151"))
        self.setStyleSheet(f"""
            background-color: {bg}; color: {fg};
            border-radius: 10px; padding: 2px 10px;
            font-size: 11px; font-weight: 600;
            border: none;
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
