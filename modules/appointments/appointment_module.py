"""Appointment Management Module"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QDateTimeEdit, QDialog,
    QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QDateTime
from datetime import datetime
from core.models import Appointment, Patient, Doctor, AppointmentStatus, get_session
from utils.styles import (
    COLORS, heading, btn, make_table, fill_table, stat_card,
    confirm_dialog, show_error, show_success, Badge
)
from utils.helpers import gen_appointment_id, logger
from modules.patients.patient_module import PatientService
from modules.doctors.doctor_module import DoctorService


class AppointmentService:
    @staticmethod
    def get_all(search="", status_filter=None) -> list[dict]:
        session = get_session()
        try:
            q = session.query(Appointment)
            if status_filter and status_filter != "All":
                q = q.filter(Appointment.status == AppointmentStatus(status_filter))
            appts = q.order_by(Appointment.appointment_date.desc()).all()
            result = []
            for a in appts:
                pname = a.patient.full_name if a.patient else "—"
                dname = f"Dr. {a.doctor.full_name}" if a.doctor else "—"
                if search:
                    s = search.lower()
                    if s not in pname.lower() and s not in dname.lower() and s not in (a.appointment_id or "").lower():
                        continue
                result.append({
                    "id": a.id, "appointment_id": a.appointment_id,
                    "patient_id": a.patient_id, "patient_name": pname,
                    "doctor_id": a.doctor_id, "doctor_name": dname,
                    "date": a.appointment_date.strftime("%Y-%m-%d %H:%M") if a.appointment_date else "",
                    "reason": a.reason or "", "status": a.status.value,
                    "notes": a.notes or ""
                })
            return result
        finally:
            session.close()

    @staticmethod
    def check_conflict(doctor_id: int, dt: datetime, exclude_id: int = None) -> bool:
        """Returns True if there's a conflict (within 30 mins)."""
        session = get_session()
        try:
            from datetime import timedelta
            start = dt - timedelta(minutes=29)
            end = dt + timedelta(minutes=29)
            q = session.query(Appointment).filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date.between(start, end),
                Appointment.status == AppointmentStatus.SCHEDULED
            )
            if exclude_id:
                q = q.filter(Appointment.id != exclude_id)
            return q.count() > 0
        finally:
            session.close()

    @staticmethod
    def add(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            dt = data["appointment_date"]
            if AppointmentService.check_conflict(data["doctor_id"], dt):
                return False, "Doctor already has an appointment within 30 minutes of this slot."
            appt = Appointment(
                appointment_id=gen_appointment_id(),
                patient_id=data["patient_id"],
                doctor_id=data["doctor_id"],
                appointment_date=dt,
                reason=data.get("reason"),
                status=AppointmentStatus.SCHEDULED,
                notes=data.get("notes"),
            )
            session.add(appt)
            session.commit()
            logger.info(f"Appointment booked: {appt.appointment_id}")
            return True, appt.appointment_id
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def update_status(appt_id: int, status: str) -> tuple[bool, str]:
        session = get_session()
        try:
            a = session.query(Appointment).get(appt_id)
            if not a: return False, "Not found."
            a.status = AppointmentStatus(status)
            session.commit()
            return True, f"Status updated to {status}."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def delete(appt_id: int) -> tuple[bool, str]:
        session = get_session()
        try:
            a = session.query(Appointment).get(appt_id)
            if not a: return False, "Not found."
            session.delete(a)
            session.commit()
            return True, "Appointment deleted."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()


class AppointmentDialog(QDialog):
    def __init__(self, parent=None, data: dict = None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Book Appointment" if not data else "Edit Appointment")
        self.setMinimumSize(520, 480)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)
        lay.addWidget(heading("Book Appointment", 14))

        form = QFormLayout(); form.setSpacing(12)

        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        # Patient combo
        self.patient_combo = QComboBox()
        patients = PatientService.get_all()
        self._patient_map = {}
        for p in patients:
            label = f"{p['patient_id']} — {p['full_name']}"
            self.patient_combo.addItem(label)
            self._patient_map[label] = p["id"]

        # Doctor combo
        self.doctor_combo = QComboBox()
        self._doctor_map = {}
        for doc_id, doc_label in DoctorService.get_for_combo():
            self.doctor_combo.addItem(doc_label)
            self._doctor_map[doc_label] = doc_id

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.reason = QLineEdit(); self.reason.setPlaceholderText("Reason for visit")
        self.notes = QTextEdit(); self.notes.setMaximumHeight(80); self.notes.setPlaceholderText("Additional notes...")

        for label, widget in [("Patient *", self.patient_combo), ("Doctor *", self.doctor_combo),
                                ("Date & Time *", self.datetime_edit), ("Reason", self.reason),
                                ("Notes", self.notes)]:
            form.addRow(lbl(label), widget)

        lay.addLayout(form)

        btns = QHBoxLayout()
        save_b = btn("Book Appointment", "success")
        cancel_b = btn("Cancel", "ghost")
        save_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(save_b)
        lay.addLayout(btns)

    def save(self):
        patient_label = self.patient_combo.currentText()
        doctor_label = self.doctor_combo.currentText()
        if not patient_label or not doctor_label:
            show_error(self, "Please select patient and doctor."); return
        qdt = self.datetime_edit.dateTime()
        self.result_data = {
            "patient_id": self._patient_map.get(patient_label),
            "doctor_id": self._doctor_map.get(doctor_label),
            "appointment_date": datetime(qdt.date().year(), qdt.date().month(), qdt.date().day(),
                                         qdt.time().hour(), qdt.time().minute()),
            "reason": self.reason.text().strip(),
            "notes": self.notes.toPlainText().strip(),
        }
        self.accept()


class AppointmentModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = None
        self._appointments = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.addWidget(heading("Appointments", 18))
        header.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search appointments...")
        self.search.setFixedWidth(260)
        self.search.textChanged.connect(self.refresh)
        header.addWidget(self.search)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Scheduled", "Completed", "Cancelled", "No Show"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.status_filter)
        add_b = btn("+ Book Appointment")
        add_b.clicked.connect(self.add_appointment)
        header.addWidget(add_b)
        lay.addLayout(header)

        stats_frame = __import__('PyQt6.QtWidgets', fromlist=['QFrame']).QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")
        self.stats_row = QHBoxLayout(stats_frame)
        self.stats_row.setContentsMargins(0, 0, 0, 0)
        self.stats_row.setSpacing(12)
        self.stat_sched = stat_card("Scheduled", "0", COLORS["info"])
        self.stat_comp  = stat_card("Completed", "0", COLORS["success"])
        self.stat_canc  = stat_card("Cancelled", "0", COLORS["danger"])
        self.stats_row.addWidget(self.stat_sched)
        self.stats_row.addWidget(self.stat_comp)
        self.stats_row.addWidget(self.stat_canc)
        lay.addWidget(stats_frame)

        self.table = make_table(["Apt ID", "Patient", "Doctor", "Date & Time", "Reason", "Status"])
        self.table.setMinimumHeight(420)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        lay.addWidget(self.table)

        actions = QHBoxLayout()
        for text, cls, cb in [
            ("✅ Complete", "success", lambda: self.set_status("Completed")),
            ("❌ Cancel", "danger", lambda: self.set_status("Cancelled")),
            ("🚫 No Show", "warning", lambda: self.set_status("No Show")),
            ("🗑  Delete", "danger", self.delete_appt),
        ]:
            b = btn(text, cls); b.clicked.connect(cb); actions.addWidget(b)
        actions.addStretch()
        lay.addLayout(actions)

    def refresh(self):
        s = self.search.text() if hasattr(self, 'search') else ""
        sf = self.status_filter.currentText() if hasattr(self, 'status_filter') else "All"
        self._appointments = AppointmentService.get_all(s, sf)
        rows = [[a["appointment_id"], a["patient_name"], a["doctor_name"],
                 a["date"], a["reason"], a["status"]] for a in self._appointments]
        fill_table(self.table, rows)
        # Stats
        all_a = AppointmentService.get_all()
        sched = sum(1 for a in all_a if a["status"] == "Scheduled")
        comp  = sum(1 for a in all_a if a["status"] == "Completed")
        canc  = sum(1 for a in all_a if a["status"] == "Cancelled")
        from PyQt6.QtWidgets import QLabel
        for card_attr, val in [(self.stat_sched, str(sched)),
                               (self.stat_comp, str(comp)),
                               (self.stat_canc, str(canc))]:
            for child in card_attr.findChildren(QLabel):
                if "font-size: 26px" in child.styleSheet():
                    child.setText(val); break

    def _on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self._appointments):
                self._selected_id = self._appointments[row]["id"]
        else:
            self._selected_id = None

    def add_appointment(self):
        dlg = AppointmentDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = AppointmentService.add(dlg.result_data)
            if ok: show_success(self, f"Appointment booked! ID: {msg}"); self.refresh()
            else: show_error(self, msg)

    def set_status(self, status: str):
        if not self._selected_id: show_error(self, "Select an appointment first."); return
        ok, msg = AppointmentService.update_status(self._selected_id, status)
        if ok: show_success(self, msg); self.refresh()
        else: show_error(self, msg)

    def delete_appt(self):
        if not self._selected_id: show_error(self, "Select an appointment first."); return
        if confirm_dialog(self, "Delete", "Delete this appointment?"):
            ok, msg = AppointmentService.delete(self._selected_id)
            if ok: self._selected_id = None; show_success(self, msg); self.refresh()
            else: show_error(self, msg)