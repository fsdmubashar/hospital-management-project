"""Admissions, Prescriptions, and Salary Modules"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QDateTimeEdit, QDialog,
    QFormLayout, QScrollArea, QFrame, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QDateTime, QDate
from datetime import datetime, date
from core.models import (
    Admission, Ward, Doctor, Patient, AdmissionStatus,
    Prescription, PrescriptionItem, Medicine, SalaryRecord, SalaryStatus, get_session
)
from utils.styles import (
    COLORS, heading, btn, make_table, fill_table, stat_card,
    confirm_dialog, show_error, show_success
)
from utils.helpers import gen_admission_id, gen_prescription_id, logger, generate_prescription_pdf
from modules.patients.patient_module import PatientService
from modules.doctors.doctor_module import DoctorService
from modules.pharmacy.pharmacy_module import PharmacyService
import subprocess, os

# ══════════════════════════════════════════════════════════════
#  ADMISSIONS
# ══════════════════════════════════════════════════════════════

class AdmissionService:
    @staticmethod
    def get_all(search="", status_filter=None) -> list[dict]:
        session = get_session()
        try:
            q = session.query(Admission)
            if status_filter and status_filter != "All":
                q = q.filter(Admission.status == AdmissionStatus(status_filter))
            admissions = q.order_by(Admission.admission_date.desc()).all()
            result = []
            for a in admissions:
                pname = a.patient.full_name if a.patient else "—"
                if search and search.lower() not in pname.lower() and search.lower() not in (a.admission_id or "").lower():
                    continue
                days = 0
                if a.admission_date:
                    end = a.discharge_date or datetime.now()
                    days = max(0, (end - a.admission_date).days)
                result.append({
                    "id": a.id, "admission_id": a.admission_id,
                    "patient_id": a.patient_id, "patient_name": pname,
                    "ward": a.ward.name if a.ward else "—",
                    "ward_id": a.ward_id, "bed_number": a.bed_number or "",
                    "doctor": f"Dr. {a.ward.admissions}" if False else (
                        session.query(Doctor).get(a.doctor_id).full_name if a.doctor_id else "—"),
                    "admission_date": str(a.admission_date)[:16] if a.admission_date else "",
                    "discharge_date": str(a.discharge_date)[:16] if a.discharge_date else "",
                    "diagnosis": a.diagnosis or "", "status": a.status.value,
                    "days_stay": days, "total_charges": a.total_charges
                })
            return result
        finally:
            session.close()

    @staticmethod
    def admit(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            admission = Admission(
                admission_id=gen_admission_id(),
                patient_id=data["patient_id"],
                doctor_id=data.get("doctor_id"),
                ward_id=data["ward_id"],
                bed_number=data.get("bed_number"),
                admission_date=data.get("admission_date", datetime.now()),
                diagnosis=data.get("diagnosis"),
                status=AdmissionStatus.ADMITTED,
            )
            session.add(admission)
            session.commit()
            return True, admission.admission_id
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def discharge(admission_id: int) -> tuple[bool, str]:
        session = get_session()
        try:
            a = session.query(Admission).get(admission_id)
            if not a: return False, "Not found."
            a.discharge_date = datetime.now()
            a.status = AdmissionStatus.DISCHARGED
            ward = session.query(Ward).get(a.ward_id)
            if ward and a.admission_date:
                days = max(1, (a.discharge_date - a.admission_date).days)
                a.total_charges = days * ward.charge_per_day
            session.commit()
            return True, f"Patient discharged. Charges: ${a.total_charges:.2f}"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def get_wards() -> list[tuple[int, str]]:
        session = get_session()
        try:
            wards = session.query(Ward).all()
            return [(w.id, f"{w.name} (${w.charge_per_day}/day)") for w in wards]
        finally:
            session.close()


class AdmitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admit Patient")
        self.setMinimumSize(500, 440)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(heading("Admit Patient", 14))

        form = QFormLayout(); form.setSpacing(10)
        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        self.patient_combo = QComboBox()
        self._patient_map = {}
        for p in PatientService.get_all():
            label = f"{p['patient_id']} — {p['full_name']}"
            self.patient_combo.addItem(label)
            self._patient_map[label] = p["id"]

        self.doctor_combo = QComboBox()
        self._doctor_map = {}
        for doc_id, doc_label in DoctorService.get_for_combo():
            self.doctor_combo.addItem(doc_label)
            self._doctor_map[doc_label] = doc_id

        self.ward_combo = QComboBox()
        self._ward_map = {}
        for ward_id, ward_label in AdmissionService.get_wards():
            self.ward_combo.addItem(ward_label)
            self._ward_map[ward_label] = ward_id

        self.bed = QLineEdit(); self.bed.setPlaceholderText("Bed/Room number")
        self.diagnosis = QTextEdit(); self.diagnosis.setMaximumHeight(80); self.diagnosis.setPlaceholderText("Initial diagnosis")

        for label, widget in [("Patient *", self.patient_combo), ("Doctor", self.doctor_combo),
                               ("Ward *", self.ward_combo), ("Bed Number", self.bed), ("Diagnosis", self.diagnosis)]:
            form.addRow(lbl(label), widget)
        lay.addLayout(form)

        btns = QHBoxLayout()
        ok_b = btn("Admit Patient", "success")
        cancel_b = btn("Cancel", "ghost")
        ok_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(ok_b)
        lay.addLayout(btns)

    def save(self):
        pl = self.patient_combo.currentText()
        wl = self.ward_combo.currentText()
        dl = self.doctor_combo.currentText()
        self.result_data = {
            "patient_id": self._patient_map.get(pl),
            "doctor_id": self._doctor_map.get(dl),
            "ward_id": self._ward_map.get(wl),
            "bed_number": self.bed.text().strip(),
            "diagnosis": self.diagnosis.toPlainText().strip(),
        }
        self.accept()


class AdmissionModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = None
        self._admissions = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(heading("Admissions & Discharges", 18))
        header.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search...")
        self.search.setFixedWidth(240)
        self.search.textChanged.connect(self.refresh)
        header.addWidget(self.search)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Admitted", "Discharged"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.status_filter)
        add_b = btn("+ Admit Patient")
        add_b.clicked.connect(self.admit)
        header.addWidget(add_b)
        lay.addLayout(header)

        stats_frame = __import__('PyQt6.QtWidgets', fromlist=['QFrame']).QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")
        self.stats_row = QHBoxLayout(stats_frame)
        self.stats_row.setContentsMargins(0, 0, 0, 0)
        self.stats_row.setSpacing(12)
        self.stat_admitted   = stat_card("Currently Admitted", "0", COLORS["warning"])
        self.stat_discharged = stat_card("Discharged", "0", COLORS["success"])
        self.stats_row.addWidget(self.stat_admitted)
        self.stats_row.addWidget(self.stat_discharged)
        lay.addWidget(stats_frame)

        self.table = make_table(["Adm ID", "Patient", "Ward", "Bed", "Admitted", "Discharged", "Days", "Charges", "Status"])
        self.table.setMinimumHeight(420)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        lay.addWidget(self.table)

        actions = QHBoxLayout()
        dis_b = btn("🏠 Discharge", "warning")
        dis_b.clicked.connect(self.discharge)
        actions.addWidget(dis_b)
        actions.addStretch()
        lay.addLayout(actions)

    def refresh(self):
        s = self.search.text() if hasattr(self, 'search') else ""
        sf = self.status_filter.currentText() if hasattr(self, 'status_filter') else "All"
        self._admissions = AdmissionService.get_all(s, sf)
        rows = [[a["admission_id"], a["patient_name"], a["ward"], a["bed_number"],
                 a["admission_date"], a["discharge_date"], str(a["days_stay"]),
                 f"${a['total_charges']:.2f}", a["status"]] for a in self._admissions]
        fill_table(self.table, rows)
        all_adm    = AdmissionService.get_all()
        admitted   = sum(1 for a in all_adm if a["status"] == "Admitted")
        discharged = sum(1 for a in all_adm if a["status"] == "Discharged")
        from PyQt6.QtWidgets import QLabel
        for card_attr, val in [(self.stat_admitted, str(admitted)),
                               (self.stat_discharged, str(discharged))]:
            for child in card_attr.findChildren(QLabel):
                if "font-size: 26px" in child.styleSheet():
                    child.setText(val); break

    def _on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self._admissions):
                self._selected_id = self._admissions[row]["id"]
        else:
            self._selected_id = None

    def admit(self):
        dlg = AdmitDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = AdmissionService.admit(dlg.result_data)
            if ok: show_success(self, f"Patient admitted! ID: {msg}"); self.refresh()
            else: show_error(self, msg)

    def discharge(self):
        if not self._selected_id: show_error(self, "Select an admission first."); return
        adm = next((a for a in self._admissions if a["id"] == self._selected_id), None)
        if not adm: return
        if adm["status"] == "Discharged": show_error(self, "Already discharged."); return
        if confirm_dialog(self, "Discharge", f"Discharge {adm['patient_name']} from {adm['ward']}?"):
            ok, msg = AdmissionService.discharge(self._selected_id)
            if ok: show_success(self, msg); self.refresh()
            else: show_error(self, msg)


# ══════════════════════════════════════════════════════════════
#  PRESCRIPTIONS
# ══════════════════════════════════════════════════════════════

class PrescriptionService:
    @staticmethod
    def get_all(search="") -> list[dict]:
        session = get_session()
        try:
            rxs = session.query(Prescription).order_by(Prescription.created_at.desc()).all()
            result = []
            for rx in rxs:
                pname = rx.patient.full_name if rx.patient else "—"
                dname = rx.doctor.full_name if rx.doctor else "—"
                if search and search.lower() not in pname.lower() and search.lower() not in (rx.prescription_id or "").lower():
                    continue
                age = ""
                if rx.patient and rx.patient.date_of_birth:
                    today = date.today()
                    dob = rx.patient.date_of_birth
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                spec = rx.doctor.specialization if rx.doctor else ""
                result.append({
                    "id": rx.id, "prescription_id": rx.prescription_id,
                    "patient_id": rx.patient_id, "patient_name": pname,
                    "patient_age": age,
                    "doctor_id": rx.doctor_id, "doctor_name": dname,
                    "doctor_spec": spec,
                    "diagnosis": rx.diagnosis or "", "notes": rx.notes or "",
                    "date": str(rx.created_at)[:16] if rx.created_at else "",
                    "medications": [{
                        "name": i.medicine.name if i.medicine else "—",
                        "dosage": i.dosage or "", "frequency": i.frequency or "",
                        "duration": i.duration or "", "instructions": i.instructions or ""
                    } for i in rx.items]
                })
            return result
        finally:
            session.close()

    @staticmethod
    def create(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            rx = Prescription(
                prescription_id=gen_prescription_id(),
                patient_id=data["patient_id"],
                doctor_id=data["doctor_id"],
                diagnosis=data.get("diagnosis"),
                notes=data.get("notes"),
            )
            session.add(rx)
            session.flush()
            for med in data.get("medications", []):
                item = PrescriptionItem(
                    prescription_id=rx.id,
                    medicine_id=med["medicine_id"],
                    dosage=med.get("dosage"),
                    frequency=med.get("frequency"),
                    duration=med.get("duration"),
                    instructions=med.get("instructions"),
                )
                session.add(item)
            session.commit()
            return True, rx.prescription_id
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()


class PrescriptionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Prescription")
        self.setMinimumSize(680, 700)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._meds = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)
        lay.addWidget(heading("Create Prescription", 14))

        top_form = QFormLayout(); top_form.setSpacing(10)
        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        self.patient_combo = QComboBox()
        self._patient_map = {}
        for p in PatientService.get_all():
            label = f"{p['patient_id']} — {p['full_name']}"
            self.patient_combo.addItem(label)
            self._patient_map[label] = p["id"]

        self.doctor_combo = QComboBox()
        self._doctor_map = {}
        for doc_id, doc_label in DoctorService.get_for_combo():
            self.doctor_combo.addItem(doc_label)
            self._doctor_map[doc_label] = doc_id

        self.diagnosis = QLineEdit(); self.diagnosis.setPlaceholderText("Diagnosis / Chief complaint")
        self.notes = QTextEdit(); self.notes.setMaximumHeight(60); self.notes.setPlaceholderText("Additional notes...")

        for label, widget in [("Patient *", self.patient_combo), ("Doctor *", self.doctor_combo),
                               ("Diagnosis", self.diagnosis), ("Notes", self.notes)]:
            top_form.addRow(lbl(label), widget)
        lay.addLayout(top_form)

        lay.addWidget(heading("Add Medications", 12))
        med_add_row = QHBoxLayout()
        self.med_combo = QComboBox()
        self._med_id_map = {}
        for med_id, med_label, _ in PharmacyService.get_for_combo():
            self.med_combo.addItem(med_label.split(" - $")[0])
            self._med_id_map[med_label.split(" - $")[0]] = med_id
        self.dosage_in = QLineEdit(); self.dosage_in.setPlaceholderText("Dosage (e.g. 500mg)")
        self.freq_in = QLineEdit(); self.freq_in.setPlaceholderText("Frequency (e.g. TID)")
        self.dur_in = QLineEdit(); self.dur_in.setPlaceholderText("Duration (e.g. 7 days)")
        add_med_b = btn("+ Add", "success"); add_med_b.setFixedWidth(80)
        add_med_b.clicked.connect(self._add_med)
        for w in [self.med_combo, self.dosage_in, self.freq_in, self.dur_in, add_med_b]:
            med_add_row.addWidget(w)
        lay.addLayout(med_add_row)

        self.med_table = make_table(["Medicine", "Dosage", "Frequency", "Duration"])
        self.med_table.setMaximumHeight(200)
        lay.addWidget(self.med_table)

        btns = QHBoxLayout()
        ok_b = btn("Save Prescription", "success")
        cancel_b = btn("Cancel", "ghost")
        ok_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(ok_b)
        lay.addLayout(btns)

    def _add_med(self):
        label = self.med_combo.currentText()
        med_id = self._med_id_map.get(label)
        if not med_id: return
        self._meds.append({
            "medicine_id": med_id, "name": label,
            "dosage": self.dosage_in.text(), "frequency": self.freq_in.text(),
            "duration": self.dur_in.text(), "instructions": ""
        })
        fill_table(self.med_table, [[m["name"], m["dosage"], m["frequency"], m["duration"]] for m in self._meds])

    def save(self):
        pl = self.patient_combo.currentText()
        dl = self.doctor_combo.currentText()
        if not self._patient_map.get(pl): show_error(self, "Select patient."); return
        self.result_data = {
            "patient_id": self._patient_map.get(pl),
            "doctor_id": self._doctor_map.get(dl),
            "diagnosis": self.diagnosis.text().strip(),
            "notes": self.notes.toPlainText().strip(),
            "medications": self._meds,
        }
        self.accept()


class PrescriptionModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = None
        self._rxs = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(heading("Prescriptions", 18))
        header.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search...")
        self.search.setFixedWidth(260)
        self.search.textChanged.connect(self.refresh)
        header.addWidget(self.search)
        add_b = btn("+ New Prescription")
        add_b.clicked.connect(self.new_rx)
        header.addWidget(add_b)
        lay.addLayout(header)

        self.table = make_table(["Rx ID", "Patient", "Doctor", "Diagnosis", "Meds", "Date"])
        self.table.setMinimumHeight(450)
        self.table.itemSelectionChanged.connect(self._on_sel_changed)
        lay.addWidget(self.table)

        actions = QHBoxLayout()
        print_b = btn("🖨 Print PDF", "ghost")
        print_b.clicked.connect(self.print_rx)
        actions.addWidget(print_b)
        actions.addStretch()
        lay.addLayout(actions)

    def refresh(self):
        s = self.search.text() if hasattr(self, 'search') else ""
        self._rxs = PrescriptionService.get_all(s)
        rows = [[rx["prescription_id"], rx["patient_name"], rx["doctor_name"],
                 rx["diagnosis"], str(len(rx["medications"])), rx["date"]] for rx in self._rxs]
        fill_table(self.table, rows)

    def _on_sel_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self._rxs):
                self._selected_id = self._rxs[row]["id"]
        else:
            self._selected_id = None

    def new_rx(self):
        dlg = PrescriptionDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = PrescriptionService.create(dlg.result_data)
            if ok: show_success(self, f"Prescription saved! {msg}"); self.refresh()
            else: show_error(self, msg)

    def print_rx(self):
        if not self._selected_id: show_error(self, "Select a prescription first."); return
        rx = next((r for r in self._rxs if r["id"] == self._selected_id), None)
        if not rx: return
        rx_data = {
            "prescription_id": rx["prescription_id"],
            "patient_name": rx["patient_name"],
            "age": rx.get("patient_age", ""),
            "doctor_name": rx["doctor_name"],
            "specialization": rx.get("doctor_spec", ""),
            "diagnosis": rx["diagnosis"],
            "notes": rx["notes"],
            "date": rx["date"],
            "medications": rx["medications"],
        }
        path = generate_prescription_pdf(rx_data)
        if not path:
            show_error(self, "PDF generation failed. Ensure reportlab is installed.")
            return
        from utils.printing import PrintDialog
        dlg = PrintDialog(self, pdf_path=path, title=f"Prescription {rx['prescription_id']}")
        dlg.exec()


# ══════════════════════════════════════════════════════════════
#  SALARY
# ══════════════════════════════════════════════════════════════

class SalaryService:
    @staticmethod
    def get_all(search="") -> list[dict]:
        session = get_session()
        try:
            records = session.query(SalaryRecord).order_by(SalaryRecord.year.desc(), SalaryRecord.month.desc()).all()
            result = []
            for r in records:
                dname = r.doctor.full_name if r.doctor else "—"
                if search and search.lower() not in dname.lower():
                    continue
                import calendar
                result.append({
                    "id": r.id, "doctor_id": r.doctor_id, "doctor_name": dname,
                    "month": calendar.month_name[r.month] if r.month else "", "year": r.year,
                    "base_salary": r.base_salary, "bonus": r.bonus,
                    "deductions": r.deductions, "net_salary": r.net_salary,
                    "status": r.status.value, "paid_date": str(r.paid_date) if r.paid_date else "",
                    "notes": r.notes or ""
                })
            return result
        finally:
            session.close()

    @staticmethod
    def add(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            net = data["base_salary"] + data.get("bonus", 0) - data.get("deductions", 0)
            r = SalaryRecord(
                doctor_id=data["doctor_id"],
                month=data["month"],
                year=data["year"],
                base_salary=data["base_salary"],
                bonus=data.get("bonus", 0),
                deductions=data.get("deductions", 0),
                net_salary=net,
                status=SalaryStatus.PENDING,
                notes=data.get("notes"),
            )
            session.add(r)
            session.commit()
            return True, "Salary record added."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def mark_paid(record_id: int) -> tuple[bool, str]:
        session = get_session()
        try:
            r = session.query(SalaryRecord).get(record_id)
            if not r: return False, "Not found."
            r.status = SalaryStatus.PAID
            r.paid_date = date.today()
            session.commit()
            return True, "Marked as paid."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()


class SalaryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Salary Record")
        self.setFixedSize(460, 440)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(heading("Salary Record", 14))

        form = QFormLayout(); form.setSpacing(10)
        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        self.doctor_combo = QComboBox()
        self._doctor_map = {}
        for doc_id, doc_label in DoctorService.get_for_combo():
            self.doctor_combo.addItem(doc_label)
            self._doctor_map[doc_label] = doc_id

        import calendar
        self.month_combo = QComboBox()
        self.month_combo.addItems([calendar.month_name[i] for i in range(1, 13)])
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.year_in = QLineEdit(); self.year_in.setText(str(datetime.now().year))
        self.base = QLineEdit(); self.base.setPlaceholderText("0.00")
        self.bonus = QLineEdit(); self.bonus.setPlaceholderText("0.00"); self.bonus.setText("0")
        self.deductions = QLineEdit(); self.deductions.setPlaceholderText("0.00"); self.deductions.setText("0")
        self.notes = QLineEdit(); self.notes.setPlaceholderText("Notes")

        self.net_label = QLabel("Net: $0.00")
        self.net_label.setStyleSheet(f"color:{COLORS['success']}; font-weight:700; font-size:16px; background:transparent; border:none;")

        for f in [self.base, self.bonus, self.deductions]:
            f.textChanged.connect(self._update_net)

        for label, widget in [("Doctor *", self.doctor_combo), ("Month", self.month_combo),
                               ("Year", self.year_in), ("Base Salary ($)", self.base),
                               ("Bonus ($)", self.bonus), ("Deductions ($)", self.deductions),
                               ("Notes", self.notes), ("", self.net_label)]:
            form.addRow(lbl(label), widget)
        lay.addLayout(form)

        btns = QHBoxLayout()
        ok_b = btn("Save", "success")
        cancel_b = btn("Cancel", "ghost")
        ok_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(ok_b)
        lay.addLayout(btns)

    def _update_net(self):
        try: base = float(self.base.text() or 0)
        except: base = 0
        try: bonus = float(self.bonus.text() or 0)
        except: bonus = 0
        try: ded = float(self.deductions.text() or 0)
        except: ded = 0
        self.net_label.setText(f"Net: ${base + bonus - ded:.2f}")

    def save(self):
        dl = self.doctor_combo.currentText()
        doc_id = self._doctor_map.get(dl)
        if not doc_id: show_error(self, "Select doctor."); return
        try: base = float(self.base.text())
        except: show_error(self, "Invalid base salary."); return
        import calendar
        month_num = list(calendar.month_name).index(self.month_combo.currentText())
        try: year = int(self.year_in.text())
        except: year = datetime.now().year
        self.result_data = {
            "doctor_id": doc_id, "month": month_num, "year": year,
            "base_salary": base,
            "bonus": float(self.bonus.text() or 0),
            "deductions": float(self.deductions.text() or 0),
            "notes": self.notes.text().strip(),
        }
        self.accept()


class SalaryModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = None
        self._records = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(heading("Salary Management", 18))
        header.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search by doctor...")
        self.search.setFixedWidth(260)
        self.search.textChanged.connect(self.refresh)
        header.addWidget(self.search)
        add_b = btn("+ Add Record")
        add_b.clicked.connect(self.add_record)
        header.addWidget(add_b)
        lay.addLayout(header)

        stats_frame = __import__('PyQt6.QtWidgets', fromlist=['QFrame']).QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")
        self.stats_row = QHBoxLayout(stats_frame)
        self.stats_row.setContentsMargins(0, 0, 0, 0)
        self.stats_row.setSpacing(12)
        self.stat_payroll = stat_card("Total Payroll", "$0.00", COLORS["accent_blue"])
        self.stat_paid    = stat_card("Paid",          "$0.00", COLORS["success"])
        self.stat_sal_pend= stat_card("Pending",       "$0.00", COLORS["warning"])
        self.stats_row.addWidget(self.stat_payroll)
        self.stats_row.addWidget(self.stat_paid)
        self.stats_row.addWidget(self.stat_sal_pend)
        lay.addWidget(stats_frame)

        self.table = make_table(["Doctor", "Month", "Year", "Base", "Bonus", "Deductions", "Net", "Status", "Paid Date"])
        self.table.setMinimumHeight(420)
        self.table.itemSelectionChanged.connect(self._on_salary_sel)
        lay.addWidget(self.table)

        actions = QHBoxLayout()
        pay_b = btn("✅ Mark as Paid", "success")
        pay_b.clicked.connect(self.mark_paid)
        actions.addWidget(pay_b)
        actions.addStretch()
        lay.addLayout(actions)

    def refresh(self):
        s = self.search.text() if hasattr(self, 'search') else ""
        self._records = SalaryService.get_all(s)
        rows = [[r["doctor_name"], r["month"], str(r["year"]),
                 f"${r['base_salary']:.2f}", f"${r['bonus']:.2f}",
                 f"${r['deductions']:.2f}", f"${r['net_salary']:.2f}",
                 r["status"], r["paid_date"]] for r in self._records]
        fill_table(self.table, rows)
        total   = sum(r["net_salary"] for r in self._records)
        paid    = sum(r["net_salary"] for r in self._records if r["status"] == "Paid")
        pending = sum(r["net_salary"] for r in self._records if r["status"] == "Pending")
        from PyQt6.QtWidgets import QLabel
        for card_attr, val in [(self.stat_payroll, f"${total:,.2f}"),
                               (self.stat_paid,    f"${paid:,.2f}"),
                               (self.stat_sal_pend,f"${pending:,.2f}")]:
            for child in card_attr.findChildren(QLabel):
                if "font-size: 26px" in child.styleSheet():
                    child.setText(val); break

    def _on_salary_sel(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self._records):
                self._selected_id = self._records[row]["id"]
        else:
            self._selected_id = None

    def add_record(self):
        dlg = SalaryDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = SalaryService.add(dlg.result_data)
            if ok: show_success(self, msg); self.refresh()
            else: show_error(self, msg)

    def mark_paid(self):
        if not self._selected_id: show_error(self, "Select a record first."); return
        ok, msg = SalaryService.mark_paid(self._selected_id)
        if ok: show_success(self, msg); self.refresh()
        else: show_error(self, msg)