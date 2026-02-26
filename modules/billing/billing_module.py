"""Billing & Payments Module"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QDialog, QFormLayout,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from datetime import datetime
from core.models import Bill, Payment, PharmacyBillItem, Medicine, Patient, BillType, PaymentStatus, get_session
from utils.styles import (
    COLORS, heading, btn, make_table, fill_table, stat_card,
    confirm_dialog, show_error, show_success
)
from utils.helpers import gen_bill_number, generate_invoice_pdf, logger
from modules.patients.patient_module import PatientService
from modules.pharmacy.pharmacy_module import PharmacyService
import subprocess, os


class BillingService:
    @staticmethod
    def get_all(search="", status_filter=None) -> list[dict]:
        session = get_session()
        try:
            q = session.query(Bill)
            if status_filter and status_filter != "All":
                q = q.filter(Bill.payment_status == PaymentStatus(status_filter))
            bills = q.order_by(Bill.created_at.desc()).all()
            result = []
            for b in bills:
                pname = b.patient.full_name if b.patient else "—"
                if search and search.lower() not in pname.lower() and search.lower() not in (b.bill_number or "").lower():
                    continue
                balance = b.total_amount - b.paid_amount - b.discount
                result.append({
                    "id": b.id, "bill_number": b.bill_number, "patient_id": b.patient_id,
                    "patient_name": pname, "bill_type": b.bill_type.value if b.bill_type else "",
                    "total_amount": b.total_amount, "paid_amount": b.paid_amount,
                    "discount": b.discount, "balance": max(0, balance),
                    "payment_status": b.payment_status.value if b.payment_status else "",
                    "created_at": str(b.created_at)[:16] if b.created_at else "",
                    "notes": b.notes or "",
                    "pharmacy_items": [{
                        "desc": i.medicine.name if i.medicine else "—",
                        "qty": i.quantity, "unit_price": i.unit_price, "amount": i.subtotal
                    } for i in b.pharmacy_items]
                })
            return result
        finally:
            session.close()

    @staticmethod
    def create_bill(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            bill = Bill(
                bill_number=gen_bill_number(),
                patient_id=data["patient_id"],
                bill_type=BillType(data["bill_type"]),
                total_amount=data.get("total_amount", 0),
                paid_amount=0,
                discount=data.get("discount", 0),
                payment_status=PaymentStatus.PENDING,
                reference_id=data.get("reference_id"),
                notes=data.get("notes"),
            )
            session.add(bill)
            session.flush()

            # Pharmacy items
            for item in data.get("pharmacy_items", []):
                pi = PharmacyBillItem(
                    bill_id=bill.id,
                    medicine_id=item["medicine_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    subtotal=item["quantity"] * item["unit_price"],
                )
                session.add(pi)
                # Deduct stock
                med = session.query(Medicine).get(item["medicine_id"])
                if med:
                    med.stock_quantity = max(0, med.stock_quantity - item["quantity"])

            session.commit()
            logger.info(f"Bill created: {bill.bill_number}")
            return True, bill.bill_number
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def add_payment(bill_id: int, amount: float, method: str, reference: str = "") -> tuple[bool, str]:
        session = get_session()
        try:
            bill = session.query(Bill).get(bill_id)
            if not bill: return False, "Bill not found."
            payment = Payment(bill_id=bill_id, amount=amount, payment_method=method, reference=reference)
            session.add(payment)
            bill.paid_amount += amount
            balance = bill.total_amount - bill.paid_amount - bill.discount
            if balance <= 0:
                bill.payment_status = PaymentStatus.PAID
            elif bill.paid_amount > 0:
                bill.payment_status = PaymentStatus.PARTIAL
            session.commit()
            return True, f"Payment of ${amount:.2f} recorded."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def get_revenue_stats() -> dict:
        from sqlalchemy import func
        from datetime import date
        session = get_session()
        try:
            today = date.today()
            daily = session.query(func.sum(Payment.amount)).filter(
                func.date(Payment.payment_date) == today
            ).scalar() or 0
            monthly = session.query(func.sum(Payment.amount)).filter(
                func.extract('month', Payment.payment_date) == today.month,
                func.extract('year', Payment.payment_date) == today.year,
            ).scalar() or 0
            total = session.query(func.sum(Payment.amount)).scalar() or 0
            pending = session.query(func.sum(Bill.total_amount - Bill.paid_amount - Bill.discount)).filter(
                Bill.payment_status != PaymentStatus.PAID
            ).scalar() or 0
            return {"daily": daily, "monthly": monthly, "total": total, "pending": max(0, pending)}
        finally:
            session.close()


class BillDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Bill")
        self.setMinimumSize(620, 660)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._pharmacy_items = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(heading("Create New Bill", 14))

        form = QFormLayout(); form.setSpacing(10)

        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        self.patient_combo = QComboBox()
        self._patient_map = {}
        for p in PatientService.get_all():
            label = f"{p['patient_id']} — {p['full_name']}"
            self.patient_combo.addItem(label)
            self._patient_map[label] = p["id"]

        self.bill_type = QComboBox()
        self.bill_type.addItems(["Consultation", "Admission", "Pharmacy", "Lab Test"])
        self.bill_type.currentTextChanged.connect(self._on_type_change)

        self.total_amount = QLineEdit(); self.total_amount.setPlaceholderText("0.00")
        self.discount = QLineEdit(); self.discount.setPlaceholderText("0.00")
        self.notes = QLineEdit(); self.notes.setPlaceholderText("Optional notes")

        for label, widget in [("Patient *", self.patient_combo), ("Bill Type *", self.bill_type),
                               ("Amount ($)", self.total_amount), ("Discount ($)", self.discount),
                               ("Notes", self.notes)]:
            form.addRow(lbl(label), widget)
        lay.addLayout(form)

        # Pharmacy items section
        self.pharma_frame = QFrame()
        self.pharma_frame.setVisible(False)
        pf_lay = QVBoxLayout(self.pharma_frame)
        pf_lay.setContentsMargins(0, 0, 0, 0)
        pf_lay.setSpacing(8)
        pf_lay.addWidget(heading("Add Medicines", 12))

        add_row = QHBoxLayout()
        self.med_combo = QComboBox()
        self._med_map = {}
        for med_id, med_label, price in PharmacyService.get_for_combo():
            self.med_combo.addItem(med_label)
            self._med_map[med_label] = (med_id, price)
        self.med_qty = QLineEdit(); self.med_qty.setPlaceholderText("Qty"); self.med_qty.setFixedWidth(70)
        add_med_b = btn("Add", "success"); add_med_b.setFixedWidth(70)
        add_med_b.clicked.connect(self._add_medicine)
        add_row.addWidget(self.med_combo, 1)
        add_row.addWidget(self.med_qty)
        add_row.addWidget(add_med_b)
        pf_lay.addLayout(add_row)

        self.med_table = make_table(["Medicine", "Qty", "Unit Price", "Subtotal", ""])
        self.med_table.setMaximumHeight(200)
        pf_lay.addWidget(self.med_table)
        lay.addWidget(self.pharma_frame)

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLORS['success']}; background: transparent; border: none;")
        lay.addWidget(self.total_label)

        btns = QHBoxLayout()
        save_b = btn("Create Bill", "success")
        cancel_b = btn("Cancel", "ghost")
        save_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(save_b)
        lay.addLayout(btns)

    def _on_type_change(self, t):
        self.pharma_frame.setVisible(t == "Pharmacy")

    def _add_medicine(self):
        med_label = self.med_combo.currentText()
        med_id, price = self._med_map.get(med_label, (None, 0))
        if not med_id: return
        try: qty = int(self.med_qty.text() or 1)
        except: qty = 1
        name = med_label.split(" (")[0]
        self._pharmacy_items.append({"medicine_id": med_id, "name": name, "quantity": qty, "unit_price": price})
        self._refresh_med_table()

    def _refresh_med_table(self):
        rows = [[i["name"], str(i["quantity"]), f"${i['unit_price']:.2f}", f"${i['quantity']*i['unit_price']:.2f}", "✕"] for i in self._pharmacy_items]
        fill_table(self.med_table, rows)
        total = sum(i["quantity"] * i["unit_price"] for i in self._pharmacy_items)
        self.total_amount.setText(f"{total:.2f}")
        self._update_total()

    def _update_total(self):
        try: total = float(self.total_amount.text() or 0)
        except: total = 0
        try: disc = float(self.discount.text() or 0)
        except: disc = 0
        self.total_label.setText(f"Total: ${total - disc:.2f}")

    def save(self):
        patient_label = self.patient_combo.currentText()
        patient_id = self._patient_map.get(patient_label)
        if not patient_id: show_error(self, "Select a patient."); return
        try: total = float(self.total_amount.text() or 0)
        except: show_error(self, "Invalid amount."); return
        try: disc = float(self.discount.text() or 0)
        except: disc = 0
        self.result_data = {
            "patient_id": patient_id,
            "bill_type": self.bill_type.currentText(),
            "total_amount": total,
            "discount": disc,
            "notes": self.notes.text().strip(),
            "pharmacy_items": self._pharmacy_items,
        }
        self.accept()


class PaymentDialog(QDialog):
    def __init__(self, parent=None, bill_data: dict = None):
        super().__init__(parent)
        self.bill_data = bill_data
        self.setWindowTitle("Record Payment")
        self.setFixedSize(420, 320)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)
        lay.addWidget(heading("Record Payment", 14))
        if self.bill_data:
            balance = self.bill_data.get("balance", 0)
            lay.addWidget(QLabel(f"Balance Due: ${balance:.2f}"))

        form = QFormLayout(); form.setSpacing(10)
        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        self.amount = QLineEdit(); self.amount.setPlaceholderText("0.00")
        if self.bill_data:
            self.amount.setText(f"{self.bill_data.get('balance', 0):.2f}")
        self.method = QComboBox(); self.method.addItems(["Cash", "Credit Card", "Debit Card", "Bank Transfer", "Insurance", "Other"])
        self.reference = QLineEdit(); self.reference.setPlaceholderText("Reference/Receipt number")

        for label, widget in [("Amount ($) *", self.amount), ("Method", self.method), ("Reference", self.reference)]:
            form.addRow(lbl(label), widget)
        lay.addLayout(form)

        btns = QHBoxLayout()
        ok_b = btn("Record Payment", "success")
        cancel_b = btn("Cancel", "ghost")
        ok_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(ok_b)
        lay.addLayout(btns)

    def save(self):
        try: self.amount_val = float(self.amount.text())
        except: show_error(self, "Invalid amount."); return
        self.method_val = self.method.currentText()
        self.reference_val = self.reference.text().strip()
        self.accept()


class BillingModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = None
        self._bills = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(heading("Billing & Payments", 18))
        header.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search bills...")
        self.search.setFixedWidth(260)
        self.search.textChanged.connect(self.refresh)
        header.addWidget(self.search)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Partial", "Paid"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.status_filter)
        add_b = btn("+ Create Bill")
        add_b.clicked.connect(self.create_bill)
        header.addWidget(add_b)
        lay.addLayout(header)

        stats_frame = __import__('PyQt6.QtWidgets', fromlist=['QFrame']).QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")
        self.stats_row = QHBoxLayout(stats_frame)
        self.stats_row.setContentsMargins(0, 0, 0, 0)
        self.stats_row.setSpacing(12)
        self.stat_daily   = stat_card("Today's Revenue",  "$0.00", COLORS["success"])
        self.stat_monthly = stat_card("Monthly Revenue",  "$0.00", COLORS["accent_blue"])
        self.stat_pending = stat_card("Pending",          "$0.00", COLORS["warning"])
        self.stat_total   = stat_card("Total Collected",  "$0.00", COLORS["teal"])
        self.stats_row.addWidget(self.stat_daily)
        self.stats_row.addWidget(self.stat_monthly)
        self.stats_row.addWidget(self.stat_pending)
        self.stats_row.addWidget(self.stat_total)
        lay.addWidget(stats_frame)

        self.table = make_table(["Bill #", "Patient", "Type", "Total", "Paid", "Balance", "Status", "Date"])
        self.table.setMinimumHeight(400)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        lay.addWidget(self.table)

        actions = QHBoxLayout()
        for text, cls, cb in [
            ("💳 Add Payment", "success", self.add_payment),
            ("🖨 Print Invoice", "ghost", self.print_invoice),
        ]:
            b = btn(text, cls); b.clicked.connect(cb); actions.addWidget(b)
        actions.addStretch()
        lay.addLayout(actions)

    def refresh(self):
        s = self.search.text() if hasattr(self, 'search') else ""
        sf = self.status_filter.currentText() if hasattr(self, 'status_filter') else "All"
        self._bills = BillingService.get_all(s, sf)
        rows = [[b["bill_number"], b["patient_name"], b["bill_type"],
                 f"${b['total_amount']:.2f}", f"${b['paid_amount']:.2f}",
                 f"${b['balance']:.2f}", b["payment_status"], b["created_at"]] for b in self._bills]
        fill_table(self.table, rows)

        # Stats (update in-place)
        stats = BillingService.get_revenue_stats()
        from PyQt6.QtWidgets import QLabel
        for card_attr, val in [
            (self.stat_daily,   f"${stats['daily']:,.2f}"),
            (self.stat_monthly, f"${stats['monthly']:,.2f}"),
            (self.stat_pending, f"${stats['pending']:,.2f}"),
            (self.stat_total,   f"${stats['total']:,.2f}"),
        ]:
            for child in card_attr.findChildren(QLabel):
                if "font-size: 26px" in child.styleSheet():
                    child.setText(val); break

    def _on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self._bills):
                self._selected_id = self._bills[row]["id"]
        else:
            self._selected_id = None

    def create_bill(self):
        dlg = BillDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = BillingService.create_bill(dlg.result_data)
            if ok: show_success(self, f"Bill created! #{msg}"); self.refresh()
            else: show_error(self, msg)

    def add_payment(self):
        if not self._selected_id: show_error(self, "Select a bill first."); return
        bill = next((b for b in self._bills if b["id"] == self._selected_id), None)
        if not bill: return
        if bill["payment_status"] == "Paid":
            show_error(self, "This bill is already fully paid."); return
        dlg = PaymentDialog(self, bill)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = BillingService.add_payment(self._selected_id, dlg.amount_val, dlg.method_val, dlg.reference_val)
            if ok: show_success(self, msg); self.refresh()
            else: show_error(self, msg)

    def print_invoice(self):
        if not self._selected_id: show_error(self, "Select a bill first."); return
        bill = next((b for b in self._bills if b["id"] == self._selected_id), None)
        if not bill: return
        bill_data = {
            "bill_number": bill["bill_number"],
            "patient_name": bill["patient_name"],
            "bill_type": bill["bill_type"],
            "total_amount": bill["total_amount"],
            "paid_amount": bill["paid_amount"],
            "discount": bill["discount"],
            "items": bill.get("pharmacy_items", []) or [
                {"desc": bill["bill_type"], "qty": 1, "unit_price": bill["total_amount"], "amount": bill["total_amount"]}
            ],
        }
        path = generate_invoice_pdf(bill_data)
        if not path:
            show_error(self, "Failed to generate PDF. Check reportlab is installed.")
            return
        from utils.printing import PrintDialog
        dlg = PrintDialog(self, pdf_path=path, title=f"Invoice #{bill['bill_number']}")
        dlg.exec()