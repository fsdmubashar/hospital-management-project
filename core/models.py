"""
Hospital Management System - Database Models
SQLAlchemy ORM with SQLite (easily switchable to PostgreSQL/MySQL)
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Date, Text, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
import enum
import os

Base = declarative_base()

# ─────────────────────────────────────────────
#  Enums
# ─────────────────────────────────────────────
class Gender(str, enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"

class AdmissionStatus(str, enum.Enum):
    ADMITTED = "Admitted"
    DISCHARGED = "Discharged"

class PaymentStatus(str, enum.Enum):
    PENDING = "Pending"
    PARTIAL = "Partial"
    PAID = "Paid"

class BillType(str, enum.Enum):
    CONSULTATION = "Consultation"
    ADMISSION = "Admission"
    PHARMACY = "Pharmacy"
    LAB = "Lab Test"

class SalaryStatus(str, enum.Enum):
    PAID = "Paid"
    PENDING = "Pending"

# ─────────────────────────────────────────────
#  User & Roles
# ─────────────────────────────────────────────
class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = Column(JSON, default=list)          # list of module keys
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    email = Column(String(200))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)

# ─────────────────────────────────────────────
#  Doctor
# ─────────────────────────────────────────────
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(50), unique=True)
    full_name = Column(String(200), nullable=False)
    specialization = Column(String(200))
    phone = Column(String(20))
    email = Column(String(200))
    address = Column(Text)
    availability = Column(JSON, default=dict)         # {"Mon": "9:00-17:00", ...}
    consultation_fee = Column(Float, default=0.0)
    salary = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    joined_date = Column(Date)
    appointments = relationship("Appointment", back_populates="doctor")
    prescriptions = relationship("Prescription", back_populates="doctor")
    salary_records = relationship("SalaryRecord", back_populates="doctor")

# ─────────────────────────────────────────────
#  Patient
# ─────────────────────────────────────────────
class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), unique=True)
    full_name = Column(String(200), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(Enum(Gender))
    blood_group = Column(String(10))
    phone = Column(String(20))
    email = Column(String(200))
    address = Column(Text)
    emergency_contact = Column(String(200))
    emergency_phone = Column(String(20))
    allergies = Column(Text)
    medical_history = Column(Text)
    registered_at = Column(DateTime, server_default=func.now())
    appointments = relationship("Appointment", back_populates="patient")
    admissions = relationship("Admission", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    bills = relationship("Bill", back_populates="patient")

# ─────────────────────────────────────────────
#  Appointment
# ─────────────────────────────────────────────
class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(String(50), unique=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    appointment_date = Column(DateTime, nullable=False)
    reason = Column(Text)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

# ─────────────────────────────────────────────
#  Admission / Discharge
# ─────────────────────────────────────────────
class Ward(Base):
    __tablename__ = "wards"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    ward_type = Column(String(100))
    total_beds = Column(Integer, default=0)
    charge_per_day = Column(Float, default=0.0)
    admissions = relationship("Admission", back_populates="ward")

class Admission(Base):
    __tablename__ = "admissions"
    id = Column(Integer, primary_key=True)
    admission_id = Column(String(50), unique=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    ward_id = Column(Integer, ForeignKey("wards.id"))
    bed_number = Column(String(20))
    admission_date = Column(DateTime, nullable=False)
    discharge_date = Column(DateTime)
    diagnosis = Column(Text)
    status = Column(Enum(AdmissionStatus), default=AdmissionStatus.ADMITTED)
    total_charges = Column(Float, default=0.0)
    notes = Column(Text)
    patient = relationship("Patient", back_populates="admissions")
    ward = relationship("Ward", back_populates="admissions")

# ─────────────────────────────────────────────
#  Pharmacy
# ─────────────────────────────────────────────
class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True)
    medicine_id = Column(String(50), unique=True)
    name = Column(String(200), nullable=False)
    generic_name = Column(String(200))
    category = Column(String(100))
    unit = Column(String(50))
    unit_price = Column(Float, default=0.0)
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    expiry_date = Column(Date)
    manufacturer = Column(String(200))
    is_active = Column(Boolean, default=True)
    prescription_items = relationship("PrescriptionItem", back_populates="medicine")
    pharmacy_bill_items = relationship("PharmacyBillItem", back_populates="medicine")

# ─────────────────────────────────────────────
#  Prescription
# ─────────────────────────────────────────────
class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(Integer, primary_key=True)
    prescription_id = Column(String(50), unique=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    diagnosis = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    id = Column(Integer, primary_key=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    dosage = Column(String(100))
    frequency = Column(String(100))
    duration = Column(String(100))
    instructions = Column(Text)
    prescription = relationship("Prescription", back_populates="items")
    medicine = relationship("Medicine", back_populates="prescription_items")

# ─────────────────────────────────────────────
#  Billing
# ─────────────────────────────────────────────
class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True)
    bill_number = Column(String(50), unique=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    bill_type = Column(Enum(BillType))
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    reference_id = Column(Integer, nullable=True)   # FK to admission/appointment
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    patient = relationship("Patient", back_populates="bills")
    payments = relationship("Payment", back_populates="bill")
    pharmacy_items = relationship("PharmacyBillItem", back_populates="bill")

class PharmacyBillItem(Base):
    __tablename__ = "pharmacy_bill_items"
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)
    bill = relationship("Bill", back_populates="pharmacy_items")
    medicine = relationship("Medicine", back_populates="pharmacy_bill_items")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    amount = Column(Float, default=0.0)
    payment_method = Column(String(50))
    payment_date = Column(DateTime, server_default=func.now())
    reference = Column(String(200))
    bill = relationship("Bill", back_populates="payments")

# ─────────────────────────────────────────────
#  Salary
# ─────────────────────────────────────────────
class SalaryRecord(Base):
    __tablename__ = "salary_records"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    month = Column(Integer)
    year = Column(Integer)
    base_salary = Column(Float, default=0.0)
    bonus = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    net_salary = Column(Float, default=0.0)
    status = Column(Enum(SalaryStatus), default=SalaryStatus.PENDING)
    paid_date = Column(Date)
    notes = Column(Text)
    doctor = relationship("Doctor", back_populates="salary_records")

# ─────────────────────────────────────────────
#  DB setup
# ─────────────────────────────────────────────
DB_URL = os.environ.get("HMS_DB_URL", "sqlite:///hospital.db")
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()
