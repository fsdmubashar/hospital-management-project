"""
Print Utility — sends PDFs directly to the system printer.
Works on Windows, Linux, and macOS.
"""
import os
import sys
import subprocess
import platform
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QCheckBox, QPushButton, QFrame
)
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo, QPrintDialog
from PyQt6.QtGui import QPageSize
from PyQt6.QtCore import Qt
from utils.styles import COLORS, heading, btn, show_error, show_success


def get_available_printers() -> list[str]:
    """Returns list of printer names available on the system."""
    printers = [p.printerName() for p in QPrinterInfo.availablePrinters()]
    return printers


def print_pdf_direct(pdf_path: str, printer_name: str = None, copies: int = 1) -> tuple[bool, str]:
    """
    Send a PDF file directly to a printer without opening a viewer.
    Falls back to system default if printer_name is None.
    """
    if not os.path.exists(pdf_path):
        return False, f"PDF file not found: {pdf_path}"

    system = platform.system()

    try:
        if system == "Windows":
            # Windows: use SumatraPDF (silent print) if available, else ShellExecute
            sumatra_paths = [
                r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
            ]
            sumatra = next((p for p in sumatra_paths if os.path.exists(p)), None)
            if sumatra:
                cmd = [sumatra, "-print-to-default" if not printer_name else f"-print-to", ]
                if printer_name:
                    cmd.append(printer_name)
                cmd += ["-print-settings", f"{copies}x", pdf_path]
                subprocess.run(cmd, check=True)
            else:
                # Fallback: open with default app (user prints manually)
                os.startfile(pdf_path, "print")
            return True, "Sent to printer."

        elif system == "Linux":
            # Linux: use lp (CUPS)
            cmd = ["lp"]
            if printer_name:
                cmd += ["-d", printer_name]
            if copies > 1:
                cmd += ["-n", str(copies)]
            cmd.append(pdf_path)
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, f"Sent to printer. {result.stdout.strip()}"
            else:
                return False, result.stderr.strip() or "lp command failed."

        elif system == "Darwin":  # macOS
            cmd = ["lpr"]
            if printer_name:
                cmd += ["-P", printer_name]
            if copies > 1:
                cmd += ["-#", str(copies)]
            cmd.append(pdf_path)
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Sent to printer."
            else:
                return False, result.stderr.strip()

        else:
            return False, f"Unsupported OS: {system}"

    except FileNotFoundError as e:
        return False, f"Print command not found. Is a printer/CUPS installed? ({e})"
    except Exception as e:
        return False, str(e)


def open_pdf(pdf_path: str):
    """Open PDF in the default viewer (for preview before printing)."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(pdf_path)
        elif system == "Linux":
            subprocess.Popen(["xdg-open", pdf_path])
        elif system == "Darwin":
            subprocess.Popen(["open", pdf_path])
    except Exception as e:
        pass


class PrintDialog(QDialog):
    """
    Print dialog that shows available printers and print options.
    Usage:
        dlg = PrintDialog(parent, pdf_path="/path/to/file.pdf", title="Invoice #BILL001")
        dlg.exec()
    """
    def __init__(self, parent=None, pdf_path: str = "", title: str = "Print Document"):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.setWindowTitle("Print")
        self.setFixedSize(420, 340)
        self.setStyleSheet(f"background:{COLORS['bg_dark']}; color:{COLORS['text_primary']};")
        self._build(title)

    def _build(self, title: str):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        lay.addWidget(heading(f"🖨  {title}", 13))

        # File info
        fname = os.path.basename(self.pdf_path)
        file_lbl = QLabel(f"File: {fname}")
        file_lbl.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:12px; background:transparent; border:none;")
        lay.addWidget(file_lbl)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{COLORS['border']}; border:none;")
        lay.addWidget(sep)

        # Printer selection
        printer_lbl = QLabel("Printer")
        printer_lbl.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:12px; background:transparent; border:none;")
        lay.addWidget(printer_lbl)

        self.printer_combo = QComboBox()
        printers = get_available_printers()
        if printers:
            self.printer_combo.addItem("System Default")
            self.printer_combo.addItems(printers)
        else:
            self.printer_combo.addItem("No printers found")
        lay.addWidget(self.printer_combo)

        # Copies
        copies_row = QHBoxLayout()
        copies_lbl = QLabel("Copies:")
        copies_lbl.setStyleSheet(f"color:{COLORS['text_muted']}; background:transparent; border:none;")
        self.copies_spin = QSpinBox()
        self.copies_spin.setMinimum(1)
        self.copies_spin.setMaximum(99)
        self.copies_spin.setValue(1)
        self.copies_spin.setFixedWidth(80)
        copies_row.addWidget(copies_lbl)
        copies_row.addWidget(self.copies_spin)
        copies_row.addStretch()
        lay.addLayout(copies_row)

        # No printers warning
        if not printers:
            warn = QLabel("⚠  No printers detected. PDF will open in viewer instead.")
            warn.setWordWrap(True)
            warn.setStyleSheet(f"color:{COLORS['warning']}; font-size:11px; background:transparent; border:none;")
            lay.addWidget(warn)

        lay.addStretch()

        # Buttons
        btns = QHBoxLayout()
        preview_b = btn("👁  Preview", "ghost")
        print_b = btn("🖨  Print", "success")
        cancel_b = btn("Cancel", "ghost")

        preview_b.clicked.connect(self._preview)
        print_b.clicked.connect(self._print)
        cancel_b.clicked.connect(self.reject)

        btns.addWidget(cancel_b)
        btns.addWidget(preview_b)
        btns.addWidget(print_b)
        lay.addLayout(btns)

        self._printers = printers

    def _preview(self):
        open_pdf(self.pdf_path)

    def _print(self):
        if not self._printers:
            # No printer — just open for manual print
            open_pdf(self.pdf_path)
            show_success(self, "PDF opened. Use File → Print in the viewer.")
            self.accept()
            return

        selected = self.printer_combo.currentText()
        printer_name = None if selected == "System Default" else selected
        copies = self.copies_spin.value()

        ok, msg = print_pdf_direct(self.pdf_path, printer_name, copies)
        if ok:
            show_success(self, f"✓ {msg}")
            self.accept()
        else:
            show_error(self, f"Print failed: {msg}\n\nOpening PDF for manual print...")
            open_pdf(self.pdf_path)