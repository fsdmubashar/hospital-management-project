"""Utility helpers"""
import logging
import os
import shutil
import random
import string
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path

# ─── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
PRODUCTION_LOG = LOG_DIR / "production.log"

_file_handler = RotatingFileHandler(
    PRODUCTION_LOG,
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
_file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[_file_handler], force=True)
logger = logging.getLogger("HMS")

# ─── ID generators ─────────────────────────────────────────────────────────────
def gen_id(prefix: str, length: int = 6) -> str:
    suffix = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}{datetime.now().strftime('%y%m')}{suffix}"

def gen_patient_id():   return gen_id("PAT")
def gen_doctor_id():    return gen_id("DOC")
def gen_appointment_id(): return gen_id("APT")
def gen_admission_id(): return gen_id("ADM")
def gen_bill_number():  return gen_id("BILL")
def gen_prescription_id(): return gen_id("RX")
def gen_medicine_id():  return gen_id("MED")

# ─── Backup / Restore ──────────────────────────────────────────────────────────
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

def backup_database(db_path: str = "hospital.db") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"hospital_backup_{ts}.db"
    shutil.copy2(db_path, dest)
    logger.info(f"Database backed up to {dest}")
    return str(dest)

def restore_database(backup_path: str, db_path: str = "hospital.db") -> bool:
    try:
        shutil.copy2(backup_path, db_path)
        logger.info(f"Database restored from {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False

def list_backups() -> list[dict]:
    backups = []
    for f in sorted(BACKUP_DIR.glob("*.db"), reverse=True):
        backups.append({"name": f.name, "path": str(f), "size": f.stat().st_size,
                        "modified": datetime.fromtimestamp(f.stat().st_mtime)})
    return backups

# ─── PDF generation ────────────────────────────────────────────────────────────
REPORTS_DIR = Path("reports_output")
REPORTS_DIR.mkdir(exist_ok=True)

def generate_invoice_pdf(bill_data: dict, output_path: str = None) -> str:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import cm

        if not output_path:
            output_path = str(REPORTS_DIR / f"invoice_{bill_data.get('bill_number','BILL')}.pdf")

        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=1.5*cm)
        styles = getSampleStyleSheet()
        story = []

        # Header
        title_style = ParagraphStyle('title', parent=styles['Title'], fontSize=20,
                                     textColor=colors.HexColor('#1a3a5c'))
        sub_style = ParagraphStyle('sub', parent=styles['Normal'], fontSize=10,
                                   textColor=colors.HexColor('#666666'))

        story.append(Paragraph("🏥 City General Hospital", title_style))
        story.append(Paragraph("123 Medical Ave, Healthcare City | Tel: +1-555-0100", sub_style))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"<b>INVOICE</b> #{bill_data.get('bill_number','')}", styles['Heading2']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d %B %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        # Patient info
        story.append(Paragraph(f"<b>Patient:</b> {bill_data.get('patient_name','')}", styles['Normal']))
        story.append(Paragraph(f"<b>Type:</b> {bill_data.get('bill_type','')}", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        # Items table
        items = bill_data.get('items', [])
        if items:
            table_data = [["Description", "Qty", "Unit Price", "Amount"]]
            for item in items:
                table_data.append([item.get('desc',''), str(item.get('qty',1)),
                                   f"${item.get('unit_price',0):.2f}",
                                   f"${item.get('amount',0):.2f}"])
            t = Table(table_data, colWidths=[9*cm, 2*cm, 3*cm, 3*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f0f4f8'), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ccddee')),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*cm))

        # Totals
        totals = [
            ["Subtotal", f"${bill_data.get('total_amount', 0):.2f}"],
            ["Discount", f"${bill_data.get('discount', 0):.2f}"],
            ["Paid", f"${bill_data.get('paid_amount', 0):.2f}"],
            ["Balance Due", f"${max(0, bill_data.get('total_amount', 0) - bill_data.get('paid_amount', 0) - bill_data.get('discount', 0)):.2f}"],
        ]
        tt = Table(totals, colWidths=[13*cm, 4*cm])
        tt.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#1a3a5c')),
        ]))
        story.append(tt)
        story.append(Spacer(1, cm))
        story.append(Paragraph("Thank you for choosing City General Hospital.", sub_style))

        doc.build(story)
        return output_path
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return ""

def generate_prescription_pdf(rx_data: dict, output_path: str = None) -> str:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
        from reportlab.lib.units import cm

        if not output_path:
            output_path = str(REPORTS_DIR / f"rx_{rx_data.get('prescription_id','RX')}.pdf")

        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('title', parent=styles['Title'], fontSize=18,
                                     textColor=colors.HexColor('#1a3a5c'))
        story.append(Paragraph("🏥 City General Hospital", title_style))
        story.append(Paragraph("123 Medical Ave | Tel: +1-555-0100 | www.cityhospital.com",
                                styles['Normal']))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a3a5c')))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("<b>PRESCRIPTION</b>", styles['Heading2']))
        story.append(Paragraph(f"Rx# {rx_data.get('prescription_id','')}", styles['Normal']))
        story.append(Paragraph(f"Date: {rx_data.get('date', datetime.now().strftime('%d %B %Y'))}", styles['Normal']))
        story.append(Spacer(1, 0.3*cm))

        info = [
            [f"<b>Patient:</b> {rx_data.get('patient_name','')}", f"<b>Age:</b> {rx_data.get('age','')}"],
            [f"<b>Doctor:</b> Dr. {rx_data.get('doctor_name','')}", f"<b>Specialization:</b> {rx_data.get('specialization','')}"],
        ]
        it = Table([[Paragraph(c, styles['Normal']) for c in row] for row in info], colWidths=[9*cm, 8*cm])
        story.append(it)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"<b>Diagnosis:</b> {rx_data.get('diagnosis','')}", styles['Normal']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#aaaaaa')))
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("<b>Medications:</b>", styles['Heading3']))
        meds = rx_data.get('medications', [])
        if meds:
            med_data = [["#", "Medicine", "Dosage", "Frequency", "Duration", "Instructions"]]
            for i, m in enumerate(meds, 1):
                med_data.append([str(i), m.get('name',''), m.get('dosage',''),
                                  m.get('frequency',''), m.get('duration',''), m.get('instructions','')])
            mt = Table(med_data, colWidths=[0.8*cm, 4*cm, 2.5*cm, 3*cm, 2.5*cm, 4*cm])
            mt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a3a5c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#eef2f7'), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ]))
            story.append(mt)

        story.append(Spacer(1, cm))
        if rx_data.get('notes'):
            story.append(Paragraph(f"<b>Notes:</b> {rx_data['notes']}", styles['Normal']))
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph("____________________________", styles['Normal']))
        story.append(Paragraph(f"Dr. {rx_data.get('doctor_name','')}", styles['Normal']))
        story.append(Paragraph(rx_data.get('specialization',''), styles['Normal']))

        doc.build(story)
        return output_path
    except Exception as e:
        logger.error(f"Prescription PDF failed: {e}")
        return ""
