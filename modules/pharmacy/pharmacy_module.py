"""Pharmacy Management Module"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QDateEdit, QDialog,
    QFormLayout, QScrollArea, QFrame, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from datetime import date
from core.models import Medicine, get_session
from utils.styles import (
    COLORS, heading, btn, make_table, fill_table, stat_card,
    confirm_dialog, show_error, show_success
)
from utils.helpers import gen_medicine_id, logger


class PharmacyService:
    @staticmethod
    def get_all(search="") -> list[dict]:
        session = get_session()
        try:
            q = session.query(Medicine)
            if search:
                like = f"%{search}%"
                q = q.filter(Medicine.name.ilike(like) | Medicine.generic_name.ilike(like) | Medicine.medicine_id.ilike(like))
            meds = q.order_by(Medicine.name).all()
            return [PharmacyService._to_dict(m) for m in meds]
        finally:
            session.close()

    @staticmethod
    def _to_dict(m: Medicine) -> dict:
        return {
            "id": m.id, "medicine_id": m.medicine_id, "name": m.name,
            "generic_name": m.generic_name or "", "category": m.category or "",
            "unit": m.unit or "", "unit_price": m.unit_price,
            "stock_quantity": m.stock_quantity, "reorder_level": m.reorder_level,
            "expiry_date": str(m.expiry_date) if m.expiry_date else "",
            "manufacturer": m.manufacturer or "", "is_active": m.is_active,
            "low_stock": m.stock_quantity <= m.reorder_level
        }

    @staticmethod
    def add(data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            m = Medicine(
                medicine_id=gen_medicine_id(),
                name=data["name"],
                generic_name=data.get("generic_name"),
                category=data.get("category"),
                unit=data.get("unit"),
                unit_price=data.get("unit_price", 0),
                stock_quantity=data.get("stock_quantity", 0),
                reorder_level=data.get("reorder_level", 10),
                expiry_date=data.get("expiry_date"),
                manufacturer=data.get("manufacturer"),
            )
            session.add(m)
            session.commit()
            logger.info(f"Medicine added: {m.medicine_id}")
            return True, m.medicine_id
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def update(med_id: int, data: dict) -> tuple[bool, str]:
        session = get_session()
        try:
            m = session.query(Medicine).get(med_id)
            if not m: return False, "Medicine not found."
            for k, v in data.items():
                if hasattr(m, k): setattr(m, k, v)
            session.commit()
            return True, "Medicine updated."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def restock(med_id: int, quantity: int) -> tuple[bool, str]:
        session = get_session()
        try:
            m = session.query(Medicine).get(med_id)
            if not m: return False, "Medicine not found."
            m.stock_quantity += quantity
            session.commit()
            return True, f"Stock updated. New quantity: {m.stock_quantity}"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def get_low_stock() -> list[dict]:
        session = get_session()
        try:
            meds = session.query(Medicine).filter(
                Medicine.stock_quantity <= Medicine.reorder_level, Medicine.is_active == True
            ).all()
            return [PharmacyService._to_dict(m) for m in meds]
        finally:
            session.close()

    @staticmethod
    def get_for_combo() -> list[tuple[int, str, float]]:
        session = get_session()
        try:
            meds = session.query(Medicine).filter(Medicine.is_active == True, Medicine.stock_quantity > 0).order_by(Medicine.name).all()
            return [(m.id, f"{m.name} ({m.unit}) - ${m.unit_price:.2f}", m.unit_price) for m in meds]
        finally:
            session.close()


MEDICINE_CATEGORIES = ["Antibiotic", "Analgesic", "Antihypertensive", "Antidiabetic",
                        "Antihistamine", "Antacid", "Vitamin", "Anticoagulant", "Steroid", "Other"]

UNITS = ["Tablet", "Capsule", "Syrup (ml)", "Injection (ml)", "Drops", "Cream (g)", "Ointment (g)", "Patch", "Sachet"]


class MedicineDialog(QDialog):
    def __init__(self, parent=None, data: dict = None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("Add Medicine" if not data else "Edit Medicine")
        self.setMinimumSize(500, 540)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._build()
        if data: self._populate(data)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)
        lay.addWidget(heading("Medicine Information", 14))

        form = QFormLayout(); form.setSpacing(12)

        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;"); return l

        self.name = QLineEdit(); self.name.setPlaceholderText("Brand name")
        self.generic = QLineEdit(); self.generic.setPlaceholderText("Generic name")
        self.category = QComboBox(); self.category.addItems(MEDICINE_CATEGORIES)
        self.unit = QComboBox(); self.unit.addItems(UNITS); self.unit.setEditable(True)
        self.price = QLineEdit(); self.price.setPlaceholderText("0.00")
        self.stock = QLineEdit(); self.stock.setPlaceholderText("0")
        self.reorder = QLineEdit(); self.reorder.setPlaceholderText("10")
        self.expiry = QDateEdit(); self.expiry.setCalendarPopup(True)
        self.expiry.setDate(QDate.currentDate().addYears(1))
        self.manufacturer = QLineEdit(); self.manufacturer.setPlaceholderText("Manufacturer name")

        for label, widget in [
            ("Name *", self.name), ("Generic Name", self.generic), ("Category", self.category),
            ("Unit", self.unit), ("Unit Price ($)", self.price), ("Stock Qty", self.stock),
            ("Reorder Level", self.reorder), ("Expiry Date", self.expiry), ("Manufacturer", self.manufacturer),
        ]:
            form.addRow(lbl(label), widget)

        lay.addLayout(form)

        btns = QHBoxLayout()
        save_b = btn("Save", "success")
        cancel_b = btn("Cancel", "ghost")
        save_b.clicked.connect(self.save)
        cancel_b.clicked.connect(self.reject)
        btns.addWidget(cancel_b); btns.addWidget(save_b)
        lay.addLayout(btns)

    def _populate(self, d: dict):
        self.name.setText(d.get("name", ""))
        self.generic.setText(d.get("generic_name", ""))
        idx = self.category.findText(d.get("category", ""))
        if idx >= 0: self.category.setCurrentIndex(idx)
        self.unit.setCurrentText(d.get("unit", ""))
        self.price.setText(str(d.get("unit_price", 0)))
        self.stock.setText(str(d.get("stock_quantity", 0)))
        self.reorder.setText(str(d.get("reorder_level", 10)))
        self.manufacturer.setText(d.get("manufacturer", ""))

    def save(self):
        if not self.name.text().strip():
            show_error(self, "Medicine name is required."); return
        try: price = float(self.price.text() or 0)
        except: price = 0
        try: stock = int(self.stock.text() or 0)
        except: stock = 0
        try: reorder = int(self.reorder.text() or 10)
        except: reorder = 10
        qd = self.expiry.date()
        self.result_data = {
            "name": self.name.text().strip(),
            "generic_name": self.generic.text().strip(),
            "category": self.category.currentText(),
            "unit": self.unit.currentText(),
            "unit_price": price,
            "stock_quantity": stock,
            "reorder_level": reorder,
            "expiry_date": date(qd.year(), qd.month(), qd.day()),
            "manufacturer": self.manufacturer.text().strip(),
        }
        self.accept()


class PharmacyModule(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_id = None
        self._medicines = []
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(heading("Pharmacy & Inventory", 18))
        header.addStretch()
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Search medicines...")
        self.search.setFixedWidth(280)
        self.search.textChanged.connect(self.refresh)
        header.addWidget(self.search)
        add_b = btn("+ Add Medicine")
        add_b.clicked.connect(self.add_medicine)
        header.addWidget(add_b)
        lay.addLayout(header)

        # Low stock alert
        self.alert_label = QLabel("")
        self.alert_label.setStyleSheet(f"""
            background: rgba(210, 153, 34, 0.15);
            border: 1px solid {COLORS['warning']};
            border-radius: 6px;
            padding: 10px 16px;
            color: {COLORS['warning']};
            font-weight: 600;
        """)
        self.alert_label.setVisible(False)
        lay.addWidget(self.alert_label)

        stats_frame = __import__('PyQt6.QtWidgets', fromlist=['QFrame']).QFrame()
        stats_frame.setStyleSheet("border: none; background: transparent;")
        self.stats_row = QHBoxLayout(stats_frame)
        self.stats_row.setContentsMargins(0, 0, 0, 0)
        self.stats_row.setSpacing(12)
        self.stat_total = stat_card("Total Items", "0", COLORS["accent_blue"])
        self.stat_low   = stat_card("Low Stock",   "0", COLORS["warning"])
        self.stat_val   = stat_card("Inventory Value", "$0.00", COLORS["success"])
        self.stats_row.addWidget(self.stat_total)
        self.stats_row.addWidget(self.stat_low)
        self.stats_row.addWidget(self.stat_val)
        lay.addWidget(stats_frame)

        self.table = make_table(["Med ID", "Name", "Generic", "Category", "Unit", "Price", "Stock", "Reorder", "Expiry", "Status"])
        self.table.setMinimumHeight(400)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.cellDoubleClicked.connect(lambda row, _: self.edit_medicine())
        lay.addWidget(self.table)

        actions = QHBoxLayout()
        for text, cls, cb in [
            ("✏  Edit", "ghost", self.edit_medicine),
            ("📦  Restock", "success", self.restock),
        ]:
            b = btn(text, cls); b.clicked.connect(cb); actions.addWidget(b)
        actions.addStretch()
        lay.addLayout(actions)

    def refresh(self):
        s = self.search.text() if hasattr(self, 'search') else ""
        self._medicines = PharmacyService.get_all(s)
        rows = [[m["medicine_id"], m["name"], m["generic_name"], m["category"],
                 m["unit"], f"${m['unit_price']:.2f}", str(m["stock_quantity"]),
                 str(m["reorder_level"]), m["expiry_date"],
                 "⚠ Low" if m["low_stock"] else "OK"] for m in self._medicines]
        fill_table(self.table, rows)

        # Color low-stock rows
        for row, m in enumerate(self._medicines):
            if m["low_stock"]:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setForeground(QColor(COLORS["warning"]))

        # Alert
        low_stock = PharmacyService.get_low_stock()
        if low_stock:
            names = ", ".join(m["name"] for m in low_stock[:5])
            more = f" and {len(low_stock)-5} more" if len(low_stock) > 5 else ""
            self.alert_label.setText(f"⚠ Low Stock Alert: {names}{more}")
            self.alert_label.setVisible(True)
        else:
            self.alert_label.setVisible(False)

        # Stats (update in-place)
        total     = len(self._medicines)
        low       = sum(1 for m in self._medicines if m["low_stock"])
        total_val = sum(m["unit_price"] * m["stock_quantity"] for m in self._medicines)
        from PyQt6.QtWidgets import QLabel
        for card_attr, val in [(self.stat_total, str(total)),
                               (self.stat_low,   str(low)),
                               (self.stat_val,   f"${total_val:,.2f}")]:
            for child in card_attr.findChildren(QLabel):
                if "font-size: 26px" in child.styleSheet():
                    child.setText(val); break

    def _on_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self._medicines):
                self._selected_id = self._medicines[row]["id"]
        else:
            self._selected_id = None

    def add_medicine(self):
        dlg = MedicineDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = PharmacyService.add(dlg.result_data)
            if ok: show_success(self, f"Medicine added! ID: {msg}"); self.refresh()
            else: show_error(self, msg)

    def edit_medicine(self):
        if not self._selected_id: show_error(self, "Select a medicine first."); return
        data = next((m for m in self._medicines if m["id"] == self._selected_id), None)
        if not data: return
        dlg = MedicineDialog(self, data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            ok, msg = PharmacyService.update(self._selected_id, dlg.result_data)
            if ok: show_success(self, msg); self.refresh()
            else: show_error(self, msg)

    def restock(self):
        if not self._selected_id: show_error(self, "Select a medicine first."); return
        data = next((m for m in self._medicines if m["id"] == self._selected_id), None)
        if not data: return
        dlg = QDialog(self)
        dlg.setWindowTitle("Restock Medicine")
        dlg.setFixedSize(360, 200)
        dlg.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.addWidget(heading(f"Restock: {data['name']}", 13))
        qty_input = QLineEdit(); qty_input.setPlaceholderText("Quantity to add")
        lay.addWidget(qty_input)
        btns = QHBoxLayout()
        ok_b = btn("Restock", "success")
        cancel_b = btn("Cancel", "ghost")
        ok_b.clicked.connect(dlg.accept)
        cancel_b.clicked.connect(dlg.reject)
        btns.addWidget(cancel_b); btns.addWidget(ok_b)
        lay.addLayout(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                qty = int(qty_input.text())
                ok, msg = PharmacyService.restock(self._selected_id, qty)
                if ok: show_success(self, msg); self.refresh()
                else: show_error(self, msg)
            except:
                show_error(self, "Enter a valid quantity.")