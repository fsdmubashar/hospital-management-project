"""Doctor Management Module"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QDateEdit, QDialog,
    QFormLayout, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from datetime import date
from core.models import Doctor, get_session
from utils.styles import (
    COLORS, heading, btn, make_table, fill_table, stat_card,
    confirm_dialog, show_error, show_success
)
from utils.helpers import gen_doctor_id, logger


class DoctorService:
    @staticmethod
    def get_all(search="") -> list[dict]:
        session = get_session()
        try:
            q = session.query(Doctor)
            if search:
                like = f"%{search}%"
                q = q.filter(Doctor.full_name.ilike(like) | Doctor.specialization.ilike(like) | Doctor.employee_id.ilike(like))
            docs = q.order_by(Doctor.full_name).all()
            return [DoctorService._to_dict(d) for d in docs]
        finally:
            session.close()

    @staticmethod
    def _to_dict(d: Doctor) -> dict:
        return {
            "id": d.id, "employee_id": d.employee_id, "full_name": d.full_name,
            "specialization": d.specialization or "", "phone": d.phone or "",
            "email": d.email or "", "address": d.address or "",
            "availability": d.availability or {}, "consultation_fee": d.consultation_fee,
            "salary": d.salary, "is_active": d.is_active,
            "joined_date": str(d.joined_date) if d.joined_date else ""
        }

    @staticmethod
    def add(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            doc = Doctor(
                employee_id=gen_doctor_id(),
                full_name=data["full_name"],
                specialization=data.get("specialization"),
                phone=data.get("phone"),
                email=data.get("email"),
                address=data.get("address"),
                availability=data.get("availability", {}),
                consultation_fee=data.get("consultation_fee", 0),
                salary=data.get("salary", 0),
                is_active=True,
                joined_date=data.get("joined_date"),
            )
            session.add(doc)
            session.commit()
            logger.info(f"Doctor added: {doc.employee_id}")
            return True, doc.employee_id
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def update(doc_id: int, data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            d = session.query(Doctor).get(doc_id)
            if not d: return False, "Doctor not found."
            for k, v in data.items():
                if hasattr(d, k): setattr(d, k, v)
            session.commit()
            return True, "Doctor updated."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def delete(doc_id: int) -> tuple[bool, str]:
        session = get_session()
        try:
            d = session.query(Doctor).get(doc_id)
            if not d: return False, "Not found."
            d.is_active = False  # Soft delete
            session.commit()
            return True, "Doctor deactivated."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def get_for_combo() -> list[tuple[int, str]]:
        session = get_session()
        try:
            docs = session.query(Doctor).filter_by(is_active=True).order_by(Doctor.full_name).all()
            return [(d.id, f"Dr. {d.full_name} ({d.specialization})") for d in docs]
        finally:
            session.close()


SPECIALIZATIONS = [
    "General Physician", "Cardiologist", "Neurologist", "Orthopedic", "Pediatrician",
    "Gynecologist", "Dermatologist", "ENT Specialist", "Ophthalmologist", "Dentist",
    "Psychiatrist", "Oncologist", "Radiologist", "Anesthesiologist", "Urologist",
    "Gastroenterologist", "Pulmonologist", "Endocrinologist", "Nephrologist", "Surgeon"
]


class DoctorDialog(QDialog):
    def __init__(self, parent=None, data: dict = None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Add Doctor" if not data else "Edit Doctor")
        self.setMinimumSize(560, 620)
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']}; color: {COLORS['text_primary']};")
        self._build()
        if data: self._populate(data)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)
        lay.addWidget(heading("Doctor Information", 15))

        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border:none;")
        content = QWidget()
        form = QFormLayout(content); form.setSpacing(12)

        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        self.name = QLineEdit(); self.name.setPlaceholderText("Full name")
        self.spec = QComboBox(); self.spec.addItems(SPECIALIZATIONS); self.spec.setEditable(True)
        self.phone = QLineEdit(); self.phone.setPlaceholderText("Phone")
        self.email = QLineEdit(); self.email.setPlaceholderText("Email")
        self.address = QTextEdit(); self.address.setMaximumHeight(70)
        self.fee = QLineEdit(); self.fee.setPlaceholderText("0.00")
        self.salary = QLineEdit(); self.salary.setPlaceholderText("0.00")
        self.joined = QDateEdit(); self.joined.setCalendarPopup(True); self.joined.setDate(QDate.currentDate())

        # Availability days
        self.avail_frame = QWidget()
        avail_lay = QHBoxLayout(self.avail_frame)
        avail_lay.setContentsMargins(0, 0, 0, 0)
        avail_lay.setSpacing(6)
        self.day_checks = {}
        from PyQt6.QtWidgets import QCheckBox
        for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            cb = QCheckBox(day)
            cb.setStyleSheet(f"color:{COLORS['text_primary']}; background:transparent; border:none;")
            avail_lay.addWidget(cb)
            self.day_checks[day] = cb

        for label, widget in [
            ("Full Name *", self.name), ("Specialization", self.spec),
            ("Phone", self.phone), ("Email", self.email), ("Address", self.address),
            ("Consultation Fee ($)", self.fee), ("Monthly Salary ($)", self.salary),
            ("Joined Date", self.joined), ("Availability", self.avail_frame),
        ]:
            form.addRow(lbl(label), widget)

        scroll.setWidget(content)
        lay.addWidget(scroll)

        btns = QHBoxLayout()
        save_b = btn("Save Doctor", "success")
        cancel_b = btn("Cancel", "ghost")
        save_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(save_b)
        lay.addLayout(btns)

    def _populate(self, d: dict):
        self.name.setText(d.get("full_name", ""))
        idx = self.spec.findText(d.get("specialization", ""))
        if idx >= 0: self.spec.setCurrentIndex(idx)
        else: self.spec.setCurrentText(d.get("specialization", ""))
        self.phone.setText(d.get("phone", ""))
        self.email.setText(d.get("email", ""))
        self.address.setText(d.get("address", ""))
        self.fee.setText(str(d.get("consultation_fee", 0)))
        self.salary.setText(str(d.get("salary", 0)))
        avail = d.get("availability", {})
        for day, cb in self.day_checks.items():
            cb.setChecked(day in avail)

    def save(self):
        if not self.name.text().strip():
            show_error(self, "Doctor name is required."); return
        try: fee = float(self.fee.text() or 0)
        except: fee = 0
        try: salary = float(self.salary.text() or 0)
        except: salary = 0
        qd = self.joined.date()
        avail = {day: "9:00-17:00" for day, cb in self.day_checks.items() if cb.isChecked()}
        self.result_data = {
            "full_name": self.name.text().strip(),
            "specialization": self.spec.currentText(),
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
            "address": self.address.toPlainText().strip(),
            "consultation_fee": fee,
            "salary": salary,
            "joined_date": date(qd.year(), qd.month(), qd.day()),
            "availability": avail,
        }
        self.accept()


class DoctorModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = None
        self._doctors = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(heading("Doctor Management", 18))
        header.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search doctors...")
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(self.refresh)
        header.addWidget(self.search)
        add_b = btn("+ Add Doctor")
        add_b.clicked.connect(self.add_doctor)
        header.addWidget(add_b)
        lay.addLayout(header)

        stats_frame = __import__('PyQt6.QtWidgets', fromlist=['QFrame']).QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")
        self.stats_row = QHBoxLayout(stats_frame)
        self.stats_row.setContentsMargins(0, 0, 0, 0)
        self.stats_row.setSpacing(12)
        self.stat_total   = stat_card("Total Doctors", "0", COLORS["accent_blue"])
        self.stat_active  = stat_card("Active", "0", COLORS["success"])
        self.stat_inactive= stat_card("Inactive", "0", COLORS["danger"])
        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_active)
        self.stats_row.addWidget(self.stat_inactive)
        lay.addWidget(stats_frame)

        self.table = make_table(["Emp ID", "Name", "Specialization", "Phone", "Fee", "Salary", "Status"])
        self.table.setMinimumHeight(420)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(lambda row, _: self.edit_doctor())
        lay.addWidget(self.table)

        actions = QHBoxLayout()
        for text, cls, cb in [("✏  Edit", "ghost", self.edit_doctor),
                               ("🚫  Deactivate", "danger", self.deactivate_doctor)]:
            b = btn(text, cls); b.clicked.connect(cb); actions.addWidget(b)
        actions.addStretch()
        lay.addLayout(actions)

    def refresh(self):
        search = self.search.text() if hasattr(self, 'search') else ""
        self._doctors = DoctorService.get_all(search)
        rows = [[d["employee_id"], d["full_name"], d["specialization"], d["phone"],
                 f"${d['consultation_fee']:.2f}", f"${d['salary']:.2f}",
                 "Active" if d["is_active"] else "Inactive"] for d in self._doctors]
        fill_table(self.table, rows)
        # Stats (update in-place)
        active = sum(1 for d in self._doctors if d["is_active"])
        from PyQt6.QtWidgets import QLabel
        for card_attr, val in [(self.stat_total, str(len(self._doctors))),
                               (self.stat_active, str(active)),
                               (self.stat_inactive, str(len(self._doctors) - active))]:
            for child in card_attr.findChildren(QLabel):
                if "font-size: 26px" in child.styleSheet():
                    child.setText(val); break

    def _on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self._doctors):
                self._selected_id = self._doctors[row]["id"]
        else:
            self._selected_id = None

    def add_doctor(self):
        dlg = DoctorDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = DoctorService.add(dlg.result_data)
            if ok: show_success(self, f"Doctor added! ID: {msg}"); self.refresh()
            else: show_error(self, msg)

    def edit_doctor(self):
        if not self._selected_id: show_error(self, "Select a doctor first."); return
        data = next((d for d in self._doctors if d["id"] == self._selected_id), None)
        if not data: return
        dlg = DoctorDialog(self, data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = DoctorService.update(self._selected_id, dlg.result_data)
            if ok: show_success(self, msg); self.refresh()
            else: show_error(self, msg)

    def deactivate_doctor(self):
        if not self._selected_id: show_error(self, "Select a doctor first."); return
        if confirm_dialog(self, "Deactivate Doctor", "Deactivate this doctor?"):
            ok, msg = DoctorService.delete(self._selected_id)
            if ok: self._selected_id = None; show_success(self, msg); self.refresh()
            else: show_error(self, msg)