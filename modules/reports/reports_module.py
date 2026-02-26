"""Reports & Dashboard Module"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGridLayout, QComboBox, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime, date, timedelta
from sqlalchemy import func
from core.models import (
    Patient, Doctor, Appointment, Admission, Bill, Payment,
    AppointmentStatus, AdmissionStatus, PaymentStatus, get_session
)
from utils.styles import COLORS, heading, subtext, stat_card, make_table, fill_table, btn


class ReportService:
    @staticmethod
    def dashboard_stats() -> dict:
        session = get_session()
        try:
            today = date.today()
            total_patients = session.query(Patient).count()
            total_doctors = session.query(Doctor).filter_by(is_active=True).count()
            today_appointments = session.query(Appointment).filter(
                func.date(Appointment.appointment_date) == today
            ).count()
            admitted = session.query(Admission).filter_by(status=AdmissionStatus.ADMITTED).count()
            today_revenue = session.query(func.sum(Payment.amount)).filter(
                func.date(Payment.payment_date) == today
            ).scalar() or 0
            monthly_revenue = session.query(func.sum(Payment.amount)).filter(
                func.extract('month', Payment.payment_date) == today.month,
                func.extract('year', Payment.payment_date) == today.year,
            ).scalar() or 0
            pending_bills = session.query(Bill).filter(
                Bill.payment_status != PaymentStatus.PAID
            ).count()
            return {
                "total_patients": total_patients,
                "total_doctors": total_doctors,
                "today_appointments": today_appointments,
                "admitted": admitted,
                "today_revenue": today_revenue,
                "monthly_revenue": monthly_revenue,
                "pending_bills": pending_bills,
            }
        finally:
            session.close()

    @staticmethod
    def recent_appointments(limit=10) -> list[dict]:
        session = get_session()
        try:
            appts = session.query(Appointment).order_by(
                Appointment.appointment_date.desc()
            ).limit(limit).all()
            return [{
                "patient": a.patient.full_name if a.patient else "—",
                "doctor": f"Dr. {a.doctor.full_name}" if a.doctor else "—",
                "date": str(a.appointment_date)[:16] if a.appointment_date else "",
                "status": a.status.value
            } for a in appts]
        finally:
            session.close()

    @staticmethod
    def revenue_by_type() -> list[dict]:
        from sqlalchemy import case
        session = get_session()
        try:
            results = session.query(Bill.bill_type, func.sum(Bill.paid_amount)).group_by(Bill.bill_type).all()
            return [{"type": str(r[0].value) if r[0] else "—", "amount": r[1] or 0} for r in results]
        finally:
            session.close()

    @staticmethod
    def monthly_revenue_trend() -> list[dict]:
        session = get_session()
        try:
            results = session.query(
                func.extract('month', Payment.payment_date).label('month'),
                func.extract('year', Payment.payment_date).label('year'),
                func.sum(Payment.amount).label('total')
            ).group_by('year', 'month').order_by('year', 'month').limit(12).all()
            import calendar
            return [{"label": f"{calendar.month_abbr[int(r.month)]} {int(r.year)}", "amount": r.total or 0} for r in results]
        finally:
            session.close()

    @staticmethod
    def top_doctors(limit=5) -> list[dict]:
        session = get_session()
        try:
            results = session.query(
                Doctor.full_name,
                Doctor.specialization,
                func.count(Appointment.id).label('count')
            ).join(Appointment, Appointment.doctor_id == Doctor.id, isouter=True).group_by(Doctor.id).order_by(
                func.count(Appointment.id).desc()
            ).limit(limit).all()
            return [{"name": r[0], "spec": r[1] or "—", "appointments": r[2]} for r in results]
        finally:
            session.close()


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()
        # Auto-refresh every 60 seconds
        self._timer = QTimer()
        self._timer.timeout.connect(self.refresh)
        self._timer.start(60000)

    def _build(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        self.title_label = heading(f"Dashboard — {date.today().strftime('%A, %d %B %Y')}", 20)
        header.addWidget(self.title_label)
        header.addStretch()
        refresh_b = btn("↻ Refresh", "ghost")
        refresh_b.setFixedWidth(100)
        refresh_b.clicked.connect(self.refresh)
        header.addWidget(refresh_b)
        main_layout.addLayout(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(20)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Placeholder for dynamic content
        self.stats_grid = QGridLayout()
        self.content_layout.addLayout(self.stats_grid)

        # Bottom row
        bottom = QHBoxLayout()
        bottom.setSpacing(16)

        # Recent Appointments
        appt_frame = QFrame()
        appt_frame.setStyleSheet(f"background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:10px;")
        appt_lay = QVBoxLayout(appt_frame)
        appt_lay.setContentsMargins(16, 16, 16, 16)
        appt_lay.addWidget(heading("Recent Appointments", 13))
        self.appt_table = make_table(["Patient", "Doctor", "Date", "Status"])
        self.appt_table.setMaximumHeight(280)
        appt_lay.addWidget(self.appt_table)
        bottom.addWidget(appt_frame, 2)

        # Revenue by type
        rev_frame = QFrame()
        rev_frame.setStyleSheet(f"background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:10px;")
        rev_lay = QVBoxLayout(rev_frame)
        rev_lay.setContentsMargins(16, 16, 16, 16)
        rev_lay.addWidget(heading("Revenue by Type", 13))
        self.rev_table = make_table(["Type", "Amount"])
        self.rev_table.setMaximumHeight(280)
        rev_lay.addWidget(self.rev_table)
        bottom.addWidget(rev_frame, 1)

        # Top Doctors
        doc_frame = QFrame()
        doc_frame.setStyleSheet(f"background:{COLORS['bg_card']}; border:1px solid {COLORS['border']}; border-radius:10px;")
        doc_lay = QVBoxLayout(doc_frame)
        doc_lay.setContentsMargins(16, 16, 16, 16)
        doc_lay.addWidget(heading("Top Doctors", 13))
        self.doc_table = make_table(["Doctor", "Specialization", "Appointments"])
        self.doc_table.setMaximumHeight(280)
        doc_lay.addWidget(self.doc_table)
        bottom.addWidget(doc_frame, 1)

        self.content_layout.addLayout(bottom)

    def refresh(self):
        stats = ReportService.dashboard_stats()
        # Clear stats grid
        for i in reversed(range(self.stats_grid.count())):
            w = self.stats_grid.itemAt(i).widget()
            if w: w.setParent(None)

        stat_items = [
            ("Total Patients", str(stats["total_patients"]), COLORS["accent_blue"]),
            ("Active Doctors", str(stats["total_doctors"]), COLORS["teal"]),
            ("Today's Appointments", str(stats["today_appointments"]), COLORS["info"]),
            ("Currently Admitted", str(stats["admitted"]), COLORS["warning"]),
            ("Today's Revenue", f"${stats['today_revenue']:,.2f}", COLORS["success"]),
            ("Monthly Revenue", f"${stats['monthly_revenue']:,.2f}", COLORS["accent"]),
            ("Pending Bills", str(stats["pending_bills"]), COLORS["danger"]),
        ]
        for i, (title, value, color) in enumerate(stat_items):
            card = stat_card(title, value, color)
            self.stats_grid.addWidget(card, i // 4, i % 4)

        # Tables
        appts = ReportService.recent_appointments()
        fill_table(self.appt_table, [[a["patient"], a["doctor"], a["date"], a["status"]] for a in appts])

        rev = ReportService.revenue_by_type()
        fill_table(self.rev_table, [[r["type"], f"${r['amount']:,.2f}"] for r in rev])

        docs = ReportService.top_doctors()
        fill_table(self.doc_table, [[d["name"], d["spec"], str(d["appointments"])] for d in docs])

        self.title_label.setText(f"Dashboard — {date.today().strftime('%A, %d %B %Y')}")


class ReportsModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(heading("Reports", 18))
        header.addStretch()
        self.report_type = QComboBox()
        self.report_type.addItems(["Daily Revenue", "Monthly Revenue", "Patient Statistics", "Doctor Performance"])
        self.report_type.currentTextChanged.connect(self.refresh)
        header.addWidget(self.report_type)
        refresh_b = btn("Generate", "ghost")
        refresh_b.clicked.connect(self.refresh)
        header.addWidget(refresh_b)
        lay.addLayout(header)

        self.table = make_table(["Metric", "Value"])
        self.table.setMinimumHeight(500)
        lay.addWidget(self.table)

    def refresh(self):
        rtype = self.report_type.currentText() if hasattr(self, 'report_type') else "Daily Revenue"
        session = get_session()
        try:
            rows = []
            if rtype == "Daily Revenue":
                today = date.today()
                for i in range(30):
                    d = today - timedelta(days=i)
                    rev = session.query(func.sum(Payment.amount)).filter(
                        func.date(Payment.payment_date) == d
                    ).scalar() or 0
                    rows.append([d.strftime("%d %b %Y"), f"${rev:,.2f}"])
            elif rtype == "Monthly Revenue":
                import calendar
                for month in range(1, 13):
                    rev = session.query(func.sum(Payment.amount)).filter(
                        func.extract('month', Payment.payment_date) == month,
                        func.extract('year', Payment.payment_date) == datetime.now().year,
                    ).scalar() or 0
                    rows.append([calendar.month_name[month], f"${rev:,.2f}"])
            elif rtype == "Patient Statistics":
                from core.models import Gender
                total = session.query(Patient).count()
                male = session.query(Patient).filter(Patient.gender == Gender.MALE).count()
                female = session.query(Patient).filter(Patient.gender == Gender.FEMALE).count()
                today = date.today()
                this_month = session.query(Patient).filter(
                    func.extract('month', Patient.registered_at) == today.month,
                    func.extract('year', Patient.registered_at) == today.year,
                ).count()
                rows = [["Total Patients", str(total)], ["Male", str(male)], ["Female", str(female)],
                        ["Registered This Month", str(this_month)]]
            elif rtype == "Doctor Performance":
                results = session.query(
                    Doctor.full_name, Doctor.specialization,
                    func.count(Appointment.id).label('appts')
                ).join(Appointment, Appointment.doctor_id == Doctor.id, isouter=True).group_by(Doctor.id).all()
                self.table.setColumnCount(3)
                self.table.setHorizontalHeaderLabels(["Doctor", "Specialization", "Appointments"])
                fill_table(self.table, [[r[0], r[1] or "—", str(r[2])] for r in results])
                return

            fill_table(self.table, rows)
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["Metric", "Value"])
        finally:
            session.close()
