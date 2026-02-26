"""User & Role Management Module (Admin Only)"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCheckBox, QDialog, QFormLayout,
    QFrame, QScrollArea, QTabWidget
)
from PyQt6.QtCore import Qt
from core.auth import AuthService, ALL_MODULES
from utils.styles import (
    COLORS, heading, btn, make_table, fill_table,
    confirm_dialog, show_error, show_success
)

MODULE_LABELS = {
    "doctors": "👨‍⚕️ Doctor Management",
    "patients": "👥 Patient Management",
    "appointments": "📅 Appointments",
    "admissions": "🏥 Admissions",
    "pharmacy": "💊 Pharmacy",
    "billing": "💰 Billing",
    "salary": "💵 Salary",
    "prescriptions": "📋 Prescriptions",
    "reports": "📊 Reports",
}


class UserDialog(QDialog):
    def __init__(self, parent=None, user_data: dict = None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle("Add User" if not user_data else "Edit User")
        self.setMinimumSize(500, 500)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._build()
        if user_data: self._populate(user_data)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(heading("User Information", 14))

        form = QFormLayout(); form.setSpacing(10)
        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        self.username = QLineEdit(); self.username.setPlaceholderText("Username")
        self.password = QLineEdit(); self.password.setPlaceholderText("Password (leave blank to keep)")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.full_name = QLineEdit(); self.full_name.setPlaceholderText("Full name")
        self.email = QLineEdit(); self.email.setPlaceholderText("Email")
        self.is_admin = QCheckBox("Admin (Full access)")
        self.is_admin.setStyleSheet(f"color:{COLORS['text_primary']}; background:transparent; border:none;")
        self.is_active = QCheckBox("Active")
        self.is_active.setChecked(True)
        self.is_active.setStyleSheet(f"color:{COLORS['text_primary']}; background:transparent; border:none;")

        self.role_combo = QComboBox()
        self._role_map = {}
        for role in AuthService.get_all_roles():
            self.role_combo.addItem(role["name"])
            self._role_map[role["name"]] = role["id"]

        for label, widget in [("Username *", self.username), ("Password", self.password),
                               ("Full Name", self.full_name), ("Email", self.email),
                               ("Role", self.role_combo), ("", self.is_admin), ("", self.is_active)]:
            form.addRow(lbl(label), widget)
        lay.addLayout(form)

        btns = QHBoxLayout()
        ok_b = btn("Save User", "success")
        cancel_b = btn("Cancel", "ghost")
        ok_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(ok_b)
        lay.addLayout(btns)

    def _populate(self, d: dict):
        self.username.setText(d.get("username", ""))
        self.full_name.setText(d.get("full_name", ""))
        self.email.setText(d.get("email", ""))
        self.is_admin.setChecked(d.get("is_admin", False))
        self.is_active.setChecked(d.get("is_active", True))
        idx = self.role_combo.findText(d.get("role_name", ""))
        if idx >= 0: self.role_combo.setCurrentIndex(idx)

    def save(self):
        if not self.username.text().strip():
            show_error(self, "Username required."); return
        role_name = self.role_combo.currentText()
        self.result_data = {
            "username": self.username.text().strip(),
            "password": self.password.text(),
            "full_name": self.full_name.text().strip(),
            "email": self.email.text().strip(),
            "is_admin": self.is_admin.isChecked(),
            "is_active": self.is_active.isChecked(),
            "role_id": self._role_map.get(role_name),
        }
        self.accept()


class RoleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Role")
        self.setMinimumSize(440, 480)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(heading("New Role", 14))

        lbl_n = QLabel("Role Name *")
        lbl_n.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;")
        self.name_input = QLineEdit(); self.name_input.setPlaceholderText("e.g. Receptionist")
        lay.addWidget(lbl_n)
        lay.addWidget(self.name_input)

        perm_lbl = QLabel("Permissions:")
        perm_lbl.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;")
        lay.addWidget(perm_lbl)

        self.perm_checks = {}
        for module, label in MODULE_LABELS.items():
            cb = QCheckBox(label)
            cb.setStyleSheet(f"color:{COLORS['text_primary']}; background:transparent; border:none;")
            lay.addWidget(cb)
            self.perm_checks[module] = cb

        btns = QHBoxLayout()
        ok_b = btn("Create Role", "success")
        cancel_b = btn("Cancel", "ghost")
        ok_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(ok_b)
        lay.addLayout(btns)

    def save(self):
        if not self.name_input.text().strip():
            show_error(self, "Role name required."); return
        self.result_data = {
            "name": self.name_input.text().strip(),
            "permissions": [m for m, cb in self.perm_checks.items() if cb.isChecked()]
        }
        self.accept()


class UserManagementModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_user_id = None
        self._users = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(heading("User & Role Management", 18))
        header.addStretch()
        add_user_b = btn("+ Add User")
        add_role_b = btn("+ Add Role", "ghost")
        add_user_b.clicked.connect(self.add_user)
        add_role_b.clicked.connect(self.add_role)
        header.addWidget(add_role_b)
        header.addWidget(add_user_b)
        lay.addLayout(header)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"background:{COLORS['bg_dark']};")

        # Users tab
        users_widget = QWidget()
        ul = QVBoxLayout(users_widget)
        ul.setContentsMargins(0, 16, 0, 0)
        self.users_table = make_table(["ID", "Username", "Full Name", "Email", "Admin", "Active", "Role", "Last Login"])
        self.users_table.cellClicked.connect(lambda r, _: self._select_user(r))
        ul.addWidget(self.users_table)
        user_actions = QHBoxLayout()
        for text, cls, cb in [("✏ Edit", "ghost", self.edit_user), ("🔒 Toggle Active", "warning", self.toggle_active)]:
            b = btn(text, cls); b.clicked.connect(cb); user_actions.addWidget(b)
        user_actions.addStretch()
        ul.addLayout(user_actions)
        tabs.addTab(users_widget, "Users")

        # Roles tab
        roles_widget = QWidget()
        rl = QVBoxLayout(roles_widget)
        rl.setContentsMargins(0, 16, 0, 0)
        self.roles_table = make_table(["ID", "Role Name", "Permissions"])
        rl.addWidget(self.roles_table)
        tabs.addTab(roles_widget, "Roles")

        lay.addWidget(tabs)

    def refresh(self):
        self._users = AuthService.get_all_users()
        rows = [[str(u["id"]), u["username"], u["full_name"] or "—", u["email"] or "—",
                 "Yes" if u["is_admin"] else "No",
                 "Active" if u["is_active"] else "Inactive",
                 u["role_name"],
                 str(u["last_login"])[:16] if u["last_login"] else "Never"] for u in self._users]
        fill_table(self.users_table, rows)

        roles = AuthService.get_all_roles()
        role_rows = [[str(r["id"]), r["name"], ", ".join(
            MODULE_LABELS.get(p, p) for p in r["permissions"]
        )] for r in roles]
        fill_table(self.roles_table, role_rows)

    def _select_user(self, row):
        if row < len(self._users):
            self._selected_user_id = self._users[row]["id"]

    def add_user(self):
        dlg = UserDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data
            ok, msg = AuthService.create_user(d["username"], d["password"], d["full_name"],
                                               d["email"], d["is_admin"], d.get("role_id"))
            if ok: show_success(self, msg); self.refresh()
            else: show_error(self, msg)

    def edit_user(self):
        if not self._selected_user_id: show_error(self, "Select a user first."); return
        user = next((u for u in self._users if u["id"] == self._selected_user_id), None)
        if not user: return
        dlg = UserDialog(self, user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.result_data
            ok, msg = AuthService.update_user(self._selected_user_id, **d)
            if ok: show_success(self, msg); self.refresh()
            else: show_error(self, msg)

    def toggle_active(self):
        if not self._selected_user_id: show_error(self, "Select a user."); return
        user = next((u for u in self._users if u["id"] == self._selected_user_id), None)
        if not user: return
        new_val = not user["is_active"]
        ok, msg = AuthService.update_user(self._selected_user_id, is_active=new_val)
        if ok: show_success(self, msg); self.refresh()
        else: show_error(self, msg)

    def add_role(self):
        dlg = RoleDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = AuthService.create_role(dlg.result_data["name"], dlg.result_data["permissions"])
            if ok: show_success(self, msg); self.refresh()
            else: show_error(self, msg)
