"""
Hospital Management System — Main Application
Entry point: main.py
"""
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QStackedWidget,
    QMessageBox, QDialog, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QLinearGradient

from utils.styles import APP_STYLE, COLORS, heading, btn
from core.models import init_db
from core.auth import AuthService, seed_default_data, ALL_MODULES
from utils.helpers import logger, backup_database, restore_database, list_backups


# ─── Login Screen ───────────────────────────────────────────────────────────────
class LoginScreen(QWidget):
    def __init__(self, on_login):
        super().__init__()
        self.on_login = on_login
        self._build()

    def _build(self):
        # Full-screen gradient background
        self.setStyleSheet(f"""
            QWidget#LoginScreen {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0d1117, stop:0.5 #0d1f3c, stop:1 #0d1117);
            }}
        """)
        self.setObjectName("LoginScreen")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch()

        # Card
        card = QFrame()
        card.setFixedSize(440, 520)
        card.setStyleSheet(f"""
            QFrame {{
                background: rgba(22, 27, 34, 0.95);
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(40, 40, 40, 40)
        card_lay.setSpacing(20)
        card_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo / title area
        logo_lbl = QLabel("🏥")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        card_lay.addWidget(logo_lbl)

        title = QLabel("City General Hospital")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 20px; font-weight: 700; background: transparent; border: none;")
        card_lay.addWidget(title)

        subtitle = QLabel("Hospital Management System")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; background: transparent; border: none;")
        card_lay.addWidget(subtitle)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none;")
        card_lay.addWidget(sep)

        # Form
        user_lbl = QLabel("Username")
        user_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent; border: none;")
        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter username")
        self.username.setMinimumHeight(44)
        self.username.setText("admin")

        pass_lbl = QLabel("Password")
        pass_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent; border: none;")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setMinimumHeight(44)
        self.password.returnPressed.connect(self.do_login)

        card_lay.addWidget(user_lbl)
        card_lay.addWidget(self.username)
        card_lay.addWidget(pass_lbl)
        card_lay.addWidget(self.password)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px; background: transparent; border: none;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(self.error_lbl)

        login_btn = QPushButton("Sign In →")
        login_btn.setMinimumHeight(46)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_blue']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: #388bfd; }}
            QPushButton:pressed {{ background: #1158c7; }}
        """)
        login_btn.clicked.connect(self.do_login)
        card_lay.addWidget(login_btn)

        hint = QLabel("Default: admin / admin123")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent; border: none;")
        card_lay.addWidget(hint)

        outer.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        outer.addStretch()

    def do_login(self):
        ok, msg = AuthService.login(self.username.text(), self.password.text())
        if ok:
            self.on_login()
        else:
            self.error_lbl.setText(f"⚠ {msg}")


# ─── Sidebar Navigation ─────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("dashboard",     "⬛", "Dashboard",       True),
    ("patients",      "👥", "Patients",         False),
    ("doctors",       "👨‍⚕️", "Doctors",          False),
    ("appointments",  "📅", "Appointments",     False),
    ("admissions",    "🏥", "Admissions",       False),
    ("pharmacy",      "💊", "Pharmacy",         False),
    ("billing",       "💰", "Billing",          False),
    ("salary",        "💵", "Salary",           False),
    ("prescriptions", "📋", "Prescriptions",    False),
    ("reports",       "📊", "Reports",          False),
    ("users",         "🔐", "User Management",  True),  # admin_only=True
]

class SidebarButton(QPushButton):
    def __init__(self, key: str, icon: str, label: str, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self.key = key
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style(False)

    def _update_style(self, active: bool):
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['sidebar_sel']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 13px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {COLORS['text_muted']};
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_hover']};
                    color: {COLORS['text_primary']};
                }}
            """)

    def setActive(self, active: bool):
        self.setChecked(active)
        self._update_style(active)


class Sidebar(QFrame):
    def __init__(self, on_navigate, parent=None):
        super().__init__(parent)
        self.on_navigate = on_navigate
        self.setFixedWidth(220)
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['sidebar_bg']};
                border: none;
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        self._buttons: dict[str, SidebarButton] = {}
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 16, 12, 16)
        lay.setSpacing(4)

        # Hospital name
        name_lbl = QLabel("City\nGeneral\nHospital")
        name_lbl.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 15px;
            font-weight: 800;
            line-height: 1.3;
            background: transparent;
            padding: 8px 12px;
        """)
        lay.addWidget(name_lbl)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLORS['border']}; border: none; margin: 8px 0;")
        lay.addWidget(sep)

        is_admin = AuthService.is_admin()

        for key, icon, label, admin_only in NAV_ITEMS:
            if admin_only and key == "users" and not is_admin:
                continue
            if not admin_only and key != "dashboard" and not AuthService.has_permission(key) and not is_admin:
                continue
            sb = SidebarButton(key, icon, label)
            sb.clicked.connect(lambda checked, k=key: self.on_navigate(k))
            self._buttons[key] = sb
            lay.addWidget(sb)

        lay.addStretch()

        # User info
        user = AuthService.current_user()
        if user:
            user_frame = QFrame()
            user_frame.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 8px;
                }}
            """)
            uf_lay = QVBoxLayout(user_frame)
            uf_lay.setContentsMargins(12, 10, 12, 10)
            uf_lay.setSpacing(2)
            uname = QLabel(user.full_name or user.username)
            uname.setStyleSheet(f"color:{COLORS['text_primary']}; font-weight:600; font-size:12px; background:transparent; border:none;")
            role_lbl = QLabel("Administrator" if user.is_admin else "Staff")
            role_lbl.setStyleSheet(f"color:{COLORS['accent_blue']}; font-size:11px; background:transparent; border:none;")
            uf_lay.addWidget(uname)
            uf_lay.addWidget(role_lbl)
            lay.addWidget(user_frame)

        # Logout
        logout_btn = QPushButton("← Logout")
        logout_btn.setFixedHeight(38)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']};
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba(218, 54, 51, 0.1);
            }}
        """)
        logout_btn.clicked.connect(self._logout)
        lay.addWidget(logout_btn)

    def set_active(self, key: str):
        for k, b in self._buttons.items():
            b.setActive(k == key)

    def _logout(self):
        reply = QMessageBox.question(self, "Logout", "Are you sure you want to logout?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            AuthService.logout()
            self.window().show_login()


# ─── Main Window ────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("City General Hospital — Management System")
        self.setMinimumSize(1200, 750)
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)
        self.setStyleSheet(APP_STYLE)
        self._login_screen = None
        self._main_widget = None
        self.show_login()

    def show_login(self):
        if self._main_widget:
            self._stack.removeWidget(self._main_widget)
            self._main_widget.deleteLater()
            self._main_widget = None

        self._login_screen = LoginScreen(self.on_login)
        self._login_screen.setStyleSheet(APP_STYLE + f"""
            QWidget#LoginScreen {{
                background: {COLORS['bg_dark']};
            }}
        """)
        self._stack.addWidget(self._login_screen)
        self._stack.setCurrentWidget(self._login_screen)

    def on_login(self):
        if self._login_screen:
            self._stack.removeWidget(self._login_screen)
            self._login_screen.deleteLater()
            self._login_screen = None
        self._build_main()

    def _build_main(self):
        self._main_widget = QWidget()
        main_lay = QHBoxLayout(self._main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar(self._navigate)
        main_lay.addWidget(self._sidebar)

        # Content area
        self._content_stack = QStackedWidget()
        self._content_stack.setStyleSheet(f"background: {COLORS['bg_dark']};")
        main_lay.addWidget(self._content_stack, 1)

        # Build modules
        self._modules = {}
        self._load_modules()
        self._navigate("dashboard")

        self._stack.addWidget(self._main_widget)
        self._stack.setCurrentWidget(self._main_widget)

    def _load_modules(self):
        # Dashboard always loaded
        from modules.reports.reports_module import DashboardWidget
        self._modules["dashboard"] = DashboardWidget()
        self._content_stack.addWidget(self._modules["dashboard"])

        if AuthService.has_permission("patients") or AuthService.is_admin():
            from modules.patients.patient_module import PatientModule
            self._modules["patients"] = PatientModule()
            self._content_stack.addWidget(self._modules["patients"])

        if AuthService.has_permission("doctors") or AuthService.is_admin():
            from modules.doctors.doctor_module import DoctorModule
            self._modules["doctors"] = DoctorModule()
            self._content_stack.addWidget(self._modules["doctors"])

        if AuthService.has_permission("appointments") or AuthService.is_admin():
            from modules.appointments.appointment_module import AppointmentModule
            self._modules["appointments"] = AppointmentModule()
            self._content_stack.addWidget(self._modules["appointments"])

        if AuthService.has_permission("admissions") or AuthService.is_admin():
            from modules.other_modules import AdmissionModule
            self._modules["admissions"] = AdmissionModule()
            self._content_stack.addWidget(self._modules["admissions"])

        if AuthService.has_permission("pharmacy") or AuthService.is_admin():
            from modules.pharmacy.pharmacy_module import PharmacyModule
            self._modules["pharmacy"] = PharmacyModule()
            self._content_stack.addWidget(self._modules["pharmacy"])

        if AuthService.has_permission("billing") or AuthService.is_admin():
            from modules.billing.billing_module import BillingModule
            self._modules["billing"] = BillingModule()
            self._content_stack.addWidget(self._modules["billing"])

        if AuthService.has_permission("salary") or AuthService.is_admin():
            from modules.other_modules import SalaryModule
            self._modules["salary"] = SalaryModule()
            self._content_stack.addWidget(self._modules["salary"])

        if AuthService.has_permission("prescriptions") or AuthService.is_admin():
            from modules.other_modules import PrescriptionModule
            self._modules["prescriptions"] = PrescriptionModule()
            self._content_stack.addWidget(self._modules["prescriptions"])

        if AuthService.has_permission("reports") or AuthService.is_admin():
            from modules.reports.reports_module import ReportsModule
            self._modules["reports"] = ReportsModule()
            self._content_stack.addWidget(self._modules["reports"])

        if AuthService.is_admin():
            from modules.auth.user_management import UserManagementModule
            self._modules["users"] = UserManagementModule()
            self._content_stack.addWidget(self._modules["users"])

    def _navigate(self, key: str):
        if key in self._modules:
            self._content_stack.setCurrentWidget(self._modules[key])
            self._sidebar.set_active(key)
            # Refresh module data
            mod = self._modules[key]
            if hasattr(mod, 'refresh'):
                mod.refresh()
        else:
            from utils.styles import show_error
            show_error(self, f"You don't have access to the '{key}' module.")


# ─── Entry Point ────────────────────────────────────────────────────────────────
def main():
    try:
        # Initialize database before GUI boot.
        init_db()
        seed_default_data()
        logger.info("Hospital Management System starting...")

        app = QApplication(sys.argv)
        app.setApplicationName("Hospital Management System")
        app.setApplicationVersion("1.0.0")
        app.setStyleSheet(APP_STYLE)

        # Set default font
        font = QFont("Segoe UI", 10)
        app.setFont(font)

        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception:
        logger.exception("Fatal startup failure.")
        raise


if __name__ == "__main__":
    main()
