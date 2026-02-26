#!/usr/bin/env python3
"""
Setup script for Hospital Management System.
Run this once before starting the application.
"""
import subprocess
import sys
import os

def run(cmd):
    print(f"  → {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

print("=" * 60)
print("   HOSPITAL MANAGEMENT SYSTEM — SETUP")
print("=" * 60)
print()

print("[1/3] Installing Python dependencies...")
success = run(f"{sys.executable} -m pip install -r requirements.txt")
if not success:
    print("  ⚠  Some packages failed. Trying individually...")
    packages = ["PyQt6", "SQLAlchemy", "bcrypt", "reportlab", "Pillow", "python-dateutil"]
    for pkg in packages:
        run(f"{sys.executable} -m pip install {pkg}")

print()
print("[2/3] Initializing database...")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from core.models import init_db
    from core.auth import seed_default_data
    init_db()
    seed_default_data()
    print("  ✓ Database initialized successfully!")
    print("  ✓ Default admin account created: admin / admin123")
except Exception as e:
    print(f"  ✗ Database init failed: {e}")

print()
print("[3/3] Creating directories...")
for d in ["logs", "backups", "reports_output"]:
    os.makedirs(d, exist_ok=True)
    print(f"  ✓ {d}/")

print()
print("=" * 60)
print("   SETUP COMPLETE!")
print("=" * 60)
print()
print("  To start the application, run:")
print("    python main.py")
print()
print("  Default credentials:")
print("    Username: admin")
print("    Password: admin123")
print()
