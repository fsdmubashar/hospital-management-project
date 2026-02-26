# 🏥 Hospital Management System

A production-ready Desktop Hospital Management System built with **Python + PyQt6 + SQLAlchemy (SQLite/PostgreSQL)**.

---

## 📋 Feature Overview

| Module | Features |
|--------|----------|
| **Authentication** | Login, roles, permissions, session management |
| **Dashboard** | Live stats, revenue, appointment overview |
| **Doctor Management** | Add/edit/deactivate doctors, availability, fees |
| **Patient Management** | Register, search, visit history |
| **Appointments** | Book, track, prevent double-booking |
| **Admissions** | Admit/discharge, ward/bed assignment, auto-charges |
| **Pharmacy** | Inventory, restocking, low-stock alerts |
| **Billing** | Invoice creation, partial/full payments, PDF export |
| **Salary** | Staff salary records, payment tracking |
| **Prescriptions** | Digital prescriptions, PDF printing |
| **Reports** | Revenue, patient stats, doctor performance |
| **User Management** | Create users, assign roles, set permissions |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# 1. Navigate to the project directory
cd hospital_mgmt

# 2. Run the setup script (installs dependencies + initializes DB)
python setup.py

# 3. Launch the application
python main.py
```

### Default Login
```
Username: admin
Password: admin123
```

---

## 🗂 Project Structure

```
hospital_mgmt/
├── main.py                          # Entry point + MainWindow + Login
├── setup.py                         # One-time setup script
├── requirements.txt                 # Python dependencies
│
├── core/
│   ├── models.py                    # SQLAlchemy ORM models (all tables)
│   └── auth.py                      # Authentication & authorization service
│
├── modules/
│   ├── patients/
│   │   └── patient_module.py        # Patient CRUD + visit history
│   ├── doctors/
│   │   └── doctor_module.py         # Doctor CRUD + availability
│   ├── appointments/
│   │   └── appointment_module.py    # Booking + conflict detection
│   ├── pharmacy/
│   │   └── pharmacy_module.py       # Inventory + low stock alerts
│   ├── billing/
│   │   └── billing_module.py        # Bills + payments + PDF invoice
│   ├── reports/
│   │   └── reports_module.py        # Dashboard + analytics reports
│   ├── auth/
│   │   └── user_management.py       # User + role management (admin only)
│   └── other_modules.py             # Admissions, Prescriptions, Salary
│
└── utils/
    ├── styles.py                    # Global PyQt6 styles + UI components
    └── helpers.py                   # ID gen, PDF gen, backup/restore, logging
```

---

## 🗄 Database Schema

### Core Tables

```sql
-- Users & Roles (RBAC)
roles (id, name, permissions JSON)
users (id, username, password_hash, full_name, email, is_admin, role_id, ...)

-- Clinical
doctors (id, employee_id, full_name, specialization, availability JSON, salary, ...)
patients (id, patient_id, full_name, dob, gender, blood_group, medical_history, ...)
appointments (id, appointment_id, patient_id, doctor_id, appointment_date, status, ...)
admissions (id, admission_id, patient_id, ward_id, bed_number, admission_date, discharge_date, ...)
wards (id, name, ward_type, total_beds, charge_per_day)
prescriptions (id, prescription_id, patient_id, doctor_id, diagnosis, ...)
prescription_items (id, prescription_id, medicine_id, dosage, frequency, duration, ...)

-- Pharmacy
medicines (id, medicine_id, name, generic_name, category, unit_price, stock_quantity, reorder_level, ...)

-- Finance
bills (id, bill_number, patient_id, bill_type, total_amount, paid_amount, payment_status, ...)
payments (id, bill_id, amount, payment_method, payment_date, ...)
pharmacy_bill_items (id, bill_id, medicine_id, quantity, unit_price, subtotal)
salary_records (id, doctor_id, month, year, base_salary, bonus, deductions, net_salary, status, ...)
```

---

## 🔐 Role-Based Access Control

### How It Works
1. Every user has a **Role** with a list of allowed module keys.
2. **Admin users** bypass all permission checks — full access.
3. **Non-admin users** can only access modules listed in their role's `permissions`.

### Creating Custom Roles (as Admin)
1. Go to **User Management → Roles tab**
2. Click **+ Add Role**
3. Name the role and check module permissions
4. Assign the role when creating users

### Example Roles
```
Receptionist → patients, appointments
Nurse        → patients, appointments, admissions, prescriptions
Pharmacist   → pharmacy, billing
Accountant   → billing, salary, reports
```

---

## 💡 Key Technical Notes

### Switching to PostgreSQL / MySQL

Edit or set the environment variable before running:

```bash
# PostgreSQL
export HMS_DB_URL="postgresql://user:password@localhost/hospital_db"

# MySQL
export HMS_DB_URL="mysql+pymysql://user:password@localhost/hospital_db"

python main.py
```

Install the required driver:
```bash
pip install psycopg2-binary   # PostgreSQL
pip install pymysql           # MySQL
```

### PDF Generation
- Invoices and prescriptions use **reportlab**
- PDFs are saved to `reports_output/`
- Opens automatically after generation

### Backup & Restore
The system uses SQLite by default. Backups are plain `.db` file copies:

```python
from utils.helpers import backup_database, restore_database, list_backups

# Create backup
backup_path = backup_database("hospital.db")

# List backups
backups = list_backups()

# Restore
restore_database("backups/hospital_backup_20240225_143022.db")
```

### Logging
All actions are logged to `logs/hms.log`:
```
2024-02-25 14:30:22 [INFO] HMS: Patient added: PAT2402123456
2024-02-25 14:31:05 [INFO] HMS: Doctor added: DOC2402789012
2024-02-25 14:32:18 [INFO] HMS: Bill created: BILL2402345678
```

---

## 🎨 UI Design

- **Dark theme** inspired by GitHub's dark mode palette
- Clean card-based layout with consistent 8px border radius
- Color-coded status badges (Scheduled=Blue, Completed=Green, Cancelled=Red)
- Stat cards with colored left borders for quick scanning
- Auto-refreshing dashboard (every 60 seconds)

---

## 📦 Dependencies

```
PyQt6         - Modern Qt6 GUI framework
SQLAlchemy    - ORM for database abstraction
bcrypt        - Secure password hashing
reportlab     - PDF generation for invoices & prescriptions
Pillow        - Image processing
python-dateutil - Date parsing utilities
```

---

## 🔧 Extending the System

### Adding a New Module

1. Create `modules/mymodule/mymodule_module.py`
2. Add the module key to `ALL_MODULES` in `core/auth.py`
3. Add navigation entry in `NAV_ITEMS` in `main.py`
4. Load the module in `MainWindow._load_modules()`

### Adding a New Database Table

1. Add the SQLAlchemy model in `core/models.py`
2. Run `init_db()` or use Alembic for migrations in production

---

## 🏭 Production Deployment Checklist

- [ ] Switch from SQLite to PostgreSQL
- [ ] Set a strong `SECRET_KEY` environment variable
- [ ] Enable database connection pooling in SQLAlchemy
- [ ] Set up automated daily backups (cron job calling `backup_database()`)
- [ ] Configure log rotation for `logs/hms.log`
- [ ] Use a proper hospital logo in PDF templates (`utils/helpers.py`)
- [ ] Review and customize `charge_per_day` for wards
- [ ] Set up proper user roles before going live
- [ ] Test PDF generation on the target OS

---

## 📝 License

This project is provided as-is for educational and deployment purposes.
