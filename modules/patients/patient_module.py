"""Patient Management Module"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QDateEdit, QDialog,
    QFormLayout, QFrame, QScrollArea, QMessageBox, QTabWidget,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from datetime import date, datetime
from core.models import Patient, Appointment, Admission, get_session
from utils.styles import (
    COLORS, heading, subtext, btn, make_table, fill_table,
    confirm_dialog, show_error, show_success, stat_card, card
)
from utils.helpers import gen_patient_id, logger


class PatientService:
    @staticmethod
    def get_all(search="") -> list[dict]:
        session = get_session()
        try:
            q = session.query(Patient)
            if search:
                like = f"%{search}%"
                q = q.filter(
                    Patient.full_name.ilike(like) |
                    Patient.patient_id.ilike(like) |
                    Patient.phone.ilike(like)
                )
            patients = q.order_by(Patient.registered_at.desc()).all()
            return [PatientService._to_dict(p) for p in patients]
        finally:
            session.close()

    @staticmethod
    def _to_dict(p: Patient) -> dict:
        age = ""
        if p.date_of_birth:
            today = date.today()
            age = today.year - p.date_of_birth.year - (
                (today.month, today.day) < (p.date_of_birth.month, p.date_of_birth.day))
        return {
            "id": p.id,
            "patient_id": p.patient_id,
            "full_name": p.full_name,
            "age": age,
            "gender": p.gender.value if p.gender else "",
            "blood_group": p.blood_group or "",
            "phone": p.phone or "",
            "email": p.email or "",
            "address": p.address or "",
            "emergency_contact": p.emergency_contact or "",
            "emergency_phone": p.emergency_phone or "",
            "allergies": p.allergies or "",
            "medical_history": p.medical_history or "",
            "date_of_birth": p.date_of_birth,
            "registered_at": str(p.registered_at)[:16] if p.registered_at else ""
        }

    @staticmethod
    def add(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            patient = Patient(
                patient_id=gen_patient_id(),
                full_name=data["full_name"],
                date_of_birth=data.get("date_of_birth"),
                gender=data.get("gender"),
                blood_group=data.get("blood_group"),
                phone=data.get("phone"),
                email=data.get("email"),
                address=data.get("address"),
                emergency_contact=data.get("emergency_contact"),
                emergency_phone=data.get("emergency_phone"),
                allergies=data.get("allergies"),
                medical_history=data.get("medical_history"),
            )
            session.add(patient)
            session.commit()
            logger.info(f"Patient added: {patient.patient_id}")
            return True, patient.patient_id
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def update(patient_id: int, data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            p = session.query(Patient).get(patient_id)
            if not p:
                return False, "Patient not found."
            for k, v in data.items():
                if hasattr(p, k):
                    setattr(p, k, v)
            session.commit()
            return True, "Patient updated successfully."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def delete(patient_id: int) -> tuple[bool, str]:
        session = get_session()
        try:
            p = session.query(Patient).get(patient_id)
            if not p:
                return False, "Not found."
            session.delete(p)
            session.commit()
            return True, "Patient deleted."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def get_visit_history(patient_id: int) -> list[dict]:
        session = get_session()
        try:
            appts = session.query(Appointment).filter_by(patient_id=patient_id).order_by(
                Appointment.appointment_date.desc()).all()
            return [{
                "date": str(a.appointment_date)[:16],
                "doctor": a.doctor.full_name if a.doctor else "—",
                "reason": a.reason or "—",
                "status": a.status.value
            } for a in appts]
        finally:
            session.close()


# ─── Patient Form Dialog ────────────────────────────────────────────────────────
class PatientDialog(QDialog):
    def __init__(self, parent=None, patient_data: dict = None):
        super().__init__(parent)
        self.patient_data = patient_data
        self.result_data = {}
        self.setWindowTitle("Add Patient" if not patient_data else "Edit Patient")
        self.setMinimumSize(600, 680)
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']}; color: {COLORS['text_primary']};")
        self._build()
        if patient_data:
            self._populate(patient_data)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)
        lay.addWidget(heading("Add New Patient" if not self.patient_data else "Edit Patient", 15))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        def lbl(t):
            l = QLabel(t)
            l.setStyleSheet(f"color: {COLORS['text_muted']}; background: transparent; border: none;")
            return l

        self.name = QLineEdit()
        self.name.setPlaceholderText("Full name")

        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        self.dob.setDate(QDate(1990, 1, 1))

        self.gender = QComboBox()
        self.gender.addItems(["Male", "Female", "Other"])

        self.blood = QComboBox()
        self.blood.addItems(["—", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Phone number")

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")

        self.address = QTextEdit()
        self.address.setMaximumHeight(70)

        self.emg_contact = QLineEdit()
        self.emg_contact.setPlaceholderText("Emergency contact name")

        self.emg_phone = QLineEdit()
        self.emg_phone.setPlaceholderText("Emergency contact phone")

        self.allergies = QTextEdit()
        self.allergies.setMaximumHeight(60)
        self.allergies.setPlaceholderText("Known allergies...")

        self.med_history = QTextEdit()
        self.med_history.setMaximumHeight(80)
        self.med_history.setPlaceholderText("Past medical history...")

        for label, widget in [
            ("Full Name *", self.name),
            ("Date of Birth", self.dob),
            ("Gender", self.gender),
            ("Blood Group", self.blood),
            ("Phone", self.phone),
            ("Email", self.email),
            ("Address", self.address),
            ("Emergency Contact", self.emg_contact),
            ("Emergency Phone", self.emg_phone),
            ("Allergies", self.allergies),
            ("Medical History", self.med_history),
        ]:
            form.addRow(lbl(label), widget)

        scroll.setWidget(content)
        lay.addWidget(scroll)

        btns = QHBoxLayout()
        save_btn = btn("Save Patient", "success")
        cancel_btn = btn("Cancel", "ghost")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        btns.addWidget(save_btn)
        lay.addLayout(btns)

    def _populate(self, d: dict):
        self.name.setText(d.get("full_name", ""))
        dob = d.get("date_of_birth")
        if dob:
            if isinstance(dob, date):
                self.dob.setDate(QDate(dob.year, dob.month, dob.day))
            else:
                try:
                    from dateutil.parser import parse
                    dt = parse(str(dob))
                    self.dob.setDate(QDate(dt.year, dt.month, dt.day))
                except Exception:
                    pass
        idx = self.gender.findText(d.get("gender", "Male"))
        if idx >= 0:
            self.gender.setCurrentIndex(idx)
        idx = self.blood.findText(d.get("blood_group", "—"))
        if idx >= 0:
            self.blood.setCurrentIndex(idx)
        self.phone.setText(d.get("phone", ""))
        self.email.setText(d.get("email", ""))
        self.address.setPlainText(d.get("address", ""))
        self.emg_contact.setText(d.get("emergency_contact", ""))
        self.emg_phone.setText(d.get("emergency_phone", ""))
        self.allergies.setPlainText(d.get("allergies", ""))
        self.med_history.setPlainText(d.get("medical_history", ""))

    def _save(self):
        if not self.name.text().strip():
            show_error(self, "Patient name is required.")
            return
        qd = self.dob.date()
        blood = self.blood.currentText()
        self.result_data = {
            "full_name": self.name.text().strip(),
            "date_of_birth": date(qd.year(), qd.month(), qd.day()),
            "gender": self.gender.currentText(),
            "blood_group": blood if blood != "—" else None,
            "phone": self.phone.text().strip(),
            "email": self.email.text().strip(),
            "address": self.address.toPlainText().strip(),
            "emergency_contact": self.emg_contact.text().strip(),
            "emergency_phone": self.emg_phone.text().strip(),
            "allergies": self.allergies.toPlainText().strip(),
            "medical_history": self.med_history.toPlainText().strip(),
        }
        self.accept()


# ─── Patient Module Widget ──────────────────────────────────────────────────────
class PatientModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = None
        self._patients = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        # ── Header ──
        header = QHBoxLayout()
        header.addWidget(heading("Patient Management", 18))
        header.addStretch()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search by name, ID, phone...")
        self.search_box.setFixedWidth(300)
        self.search_box.textChanged.connect(self.refresh)
        header.addWidget(self.search_box)
        add_btn = btn("+ Add Patient")
        add_btn.clicked.connect(self.add_patient)
        header.addWidget(add_btn)
        lay.addLayout(header)

        # ── Stats row (fixed frame, no dynamic removal) ──
        stats_frame = QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")
        self.stats_row = QHBoxLayout(stats_frame)
        self.stats_row.setContentsMargins(0, 0, 0, 0)
        self.stats_row.setSpacing(12)
        self.stat_total = stat_card("Total Patients", "0", COLORS["accent_blue"])
        self.stat_male  = stat_card("Male", "0", COLORS["info"])
        self.stat_female = stat_card("Female", "0", COLORS["teal"])
        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_male)
        self.stats_row.addWidget(self.stat_female)
        lay.addWidget(stats_frame)

        # ── Table ──
        self.table = make_table(["Patient ID", "Name", "Age", "Gender", "Blood", "Phone", "Registered"])
        self.table.setMinimumHeight(400)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(lambda row, _: self.edit_patient())
        lay.addWidget(self.table)

        # ── Selection label ──
        self.sel_label = QLabel("No patient selected — click a row to select")
        self.sel_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent; border: none;")
        lay.addWidget(self.sel_label)

        # ── Action bar ──
        actions = QHBoxLayout()
        self.edit_btn = btn("✏  Edit", "ghost")
        self.del_btn  = btn("🗑  Delete", "danger")
        self.view_btn = btn("👁  View History", "ghost")
        self.edit_btn.clicked.connect(self.edit_patient)
        self.del_btn.clicked.connect(self.delete_patient)
        self.view_btn.clicked.connect(self.view_history)
        self.edit_btn.setEnabled(False)
        self.del_btn.setEnabled(False)
        self.view_btn.setEnabled(False)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.del_btn)
        actions.addWidget(self.view_btn)
        actions.addStretch()
        lay.addLayout(actions)

    def _on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self._patients):
                self._selected_id = self._patients[row]["id"]
                name = self._patients[row]["full_name"]
                pid  = self._patients[row]["patient_id"]
                self.sel_label.setText(f"Selected: {name}  ({pid})")
                self.sel_label.setStyleSheet(
                    f"color: {COLORS['accent_blue']}; font-size: 11px; background: transparent; border: none;")
                self.edit_btn.setEnabled(True)
                self.del_btn.setEnabled(True)
                self.view_btn.setEnabled(True)
        else:
            self._selected_id = None
            self.sel_label.setText("No patient selected — click a row to select")
            self.sel_label.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent; border: none;")
            self.edit_btn.setEnabled(False)
            self.del_btn.setEnabled(False)
            self.view_btn.setEnabled(False)

    def refresh(self):
        search = self.search_box.text() if hasattr(self, 'search_box') else ""
        self._patients = PatientService.get_all(search)
        rows = [[p["patient_id"], p["full_name"], p["age"], p["gender"],
                 p["blood_group"], p["phone"], p["registered_at"]]
                for p in self._patients]
        fill_table(self.table, rows)

        # Update stat labels in place (no widget removal needed)
        total  = len(self._patients)
        male   = sum(1 for p in self._patients if p["gender"] == "Male")
        female = sum(1 for p in self._patients if p["gender"] == "Female")
        # Find value labels inside each stat card and update them
        self._update_stat_card(self.stat_total,  str(total))
        self._update_stat_card(self.stat_male,   str(male))
        self._update_stat_card(self.stat_female, str(female))

        # Clear selection after refresh
        self._selected_id = None
        if hasattr(self, 'sel_label'):
            self.sel_label.setText("No patient selected — click a row to select")
            self.sel_label.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent; border: none;")
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setEnabled(False)
            self.del_btn.setEnabled(False)
            self.view_btn.setEnabled(False)

    @staticmethod
    def _update_stat_card(card_frame, new_value: str):
        """Update the value label inside a stat_card frame."""
        for child in card_frame.findChildren(QLabel):
            text = child.text()
            # The value label has large font-size style
            if "font-size: 26px" in child.styleSheet():
                child.setText(new_value)
                break

    def add_patient(self):
        dlg = PatientDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = PatientService.add(dlg.result_data)
            if ok:
                show_success(self, f"Patient registered! ID: {msg}")
                self.refresh()
            else:
                show_error(self, msg)

    def edit_patient(self):
        if not self._selected_id:
            show_error(self, "Please select a patient from the table first.")
            return
        data = next((p for p in self._patients if p["id"] == self._selected_id), None)
        if not data:
            show_error(self, "Could not find selected patient. Please refresh.")
            return
        dlg = PatientDialog(self, data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = PatientService.update(self._selected_id, dlg.result_data)
            if ok:
                show_success(self, msg)
                self.refresh()
            else:
                show_error(self, msg)

    def delete_patient(self):
        if not self._selected_id:
            show_error(self, "Please select a patient from the table first.")
            return
        data = next((p for p in self._patients if p["id"] == self._selected_id), {})
        name = data.get("full_name", "this patient")
        if confirm_dialog(self, "Delete Patient",
                          f"Are you sure you want to delete '{name}'?\nThis cannot be undone."):
            ok, msg = PatientService.delete(self._selected_id)
            if ok:
                self._selected_id = None
                show_success(self, msg)
                self.refresh()
            else:
                show_error(self, msg)

    def view_history(self):
        if not self._selected_id:
            show_error(self, "Please select a patient from the table first.")
            return
        history = PatientService.get_visit_history(self._selected_id)
        data = next((p for p in self._patients if p["id"] == self._selected_id), {})
        dlg = QDialog(self)
        dlg.setWindowTitle("Visit History")
        dlg.setMinimumSize(700, 400)
        dlg.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.addWidget(heading(f"Visit History: {data.get('full_name', '')}", 14))
        if not history:
            lay.addWidget(QLabel("No visit history found."))
        else:
            table = make_table(["Date", "Doctor", "Reason", "Status"])
            fill_table(table, [[h["date"], h["doctor"], h["reason"], h["status"]]
                               for h in history])
            lay.addWidget(table)
        close = btn("Close", "ghost")
        close.clicked.connect(dlg.accept)
        lay.addWidget(close)
        dlg.exec()