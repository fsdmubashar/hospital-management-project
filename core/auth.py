"""Authentication & Authorization Service"""
import bcrypt
from datetime import datetime
from core.models import User, Role, get_session
from sqlalchemy.orm import joinedload

ALL_MODULES = [
    "doctors", "patients", "appointments", "admissions",
    "pharmacy", "billing", "salary", "prescriptions", "reports"
]

# Plain dataclass-style dict stored after login — no SQLAlchemy session needed
class _UserSession:
    """Holds session data without any SQLAlchemy attachment."""
    def __init__(self, user: User, role_permissions: list):
        self.id = user.id
        self.username = user.username
        self.full_name = user.full_name
        self.email = user.email
        self.is_admin = user.is_admin
        self.is_active = user.is_active
        self.role_id = user.role_id
        self.last_login = user.last_login
        self._permissions: list = role_permissions  # list of module keys

class AuthService:
    _current_user: _UserSession | None = None

    @classmethod
    def login(cls, username: str, password: str) -> tuple[bool, str]:
        session = get_session()
        try:
            # Eagerly load the role in the same query
            user = (session.query(User)
                    .options(joinedload(User.role))
                    .filter_by(username=username, is_active=True)
                    .first())
            if not user:
                return False, "Invalid username or password."
            if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
                return False, "Invalid username or password."
            user.last_login = datetime.now()
            session.commit()
            # Read everything we need while still inside the session
            permissions = list(user.role.permissions or []) if user.role else []
            cls._current_user = _UserSession(user, permissions)
            return True, "Login successful."
        finally:
            session.close()

    @classmethod
    def logout(cls):
        cls._current_user = None

    @classmethod
    def current_user(cls) -> _UserSession | None:
        return cls._current_user

    @classmethod
    def is_admin(cls) -> bool:
        return cls._current_user is not None and cls._current_user.is_admin

    @classmethod
    def has_permission(cls, module: str) -> bool:
        if cls._current_user is None:
            return False
        if cls._current_user.is_admin:
            return True
        return module in cls._current_user._permissions

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def create_user(username, password, full_name, email, is_admin, role_id=None) -> tuple[bool, str]:
        session = get_session()
        try:
            if session.query(User).filter_by(username=username).first():
                return False, "Username already exists."
            user = User(
                username=username,
                password_hash=AuthService.hash_password(password),
                full_name=full_name,
                email=email,
                is_admin=is_admin,
                role_id=role_id
            )
            session.add(user)
            session.commit()
            return True, "User created successfully."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def get_all_users():
        session = get_session()
        try:
            users = session.query(User).all()
            result = []
            for u in users:
                result.append({
                    "id": u.id, "username": u.username, "full_name": u.full_name,
                    "email": u.email, "is_admin": u.is_admin, "is_active": u.is_active,
                    "role_id": u.role_id,
                    "role_name": u.role.name if u.role else "—",
                    "last_login": u.last_login
                })
            return result
        finally:
            session.close()

    @staticmethod
    def get_all_roles():
        session = get_session()
        try:
            roles = session.query(Role).all()
            return [{"id": r.id, "name": r.name, "permissions": r.permissions or []} for r in roles]
        finally:
            session.close()

    @staticmethod
    def create_role(name: str, permissions: list) -> tuple[bool, str]:
        session = get_session()
        try:
            if session.query(Role).filter_by(name=name).first():
                return False, "Role already exists."
            role = Role(name=name, permissions=permissions)
            session.add(role)
            session.commit()
            return True, "Role created."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def update_user(user_id, **kwargs) -> tuple[bool, str]:
        session = get_session()
        try:
            user = session.query(User).get(user_id)
            if not user:
                return False, "User not found."
            if "password" in kwargs and kwargs["password"]:
                kwargs["password_hash"] = AuthService.hash_password(kwargs.pop("password"))
            else:
                kwargs.pop("password", None)
            for k, v in kwargs.items():
                setattr(user, k, v)
            session.commit()
            return True, "User updated."
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

def seed_default_data():
    """Seed admin user and default roles if DB is empty."""
    session = get_session()
    try:
        if session.query(User).count() == 0:
            # Admin role
            admin_role = Role(name="Admin", permissions=ALL_MODULES)
            session.add(admin_role)
            # Staff role
            staff_role = Role(name="Staff", permissions=["patients", "appointments"])
            session.add(staff_role)
            session.flush()
            # Admin user
            admin = User(
                username="admin",
                password_hash=AuthService.hash_password("admin123"),
                full_name="System Administrator",
                email="admin@hospital.com",
                is_admin=True,
                role_id=admin_role.id
            )
            session.add(admin)
            # Default wards
            from core.models import Ward
            wards = [
                Ward(name="General Ward", ward_type="General", total_beds=20, charge_per_day=500),
                Ward(name="ICU", ward_type="Intensive Care", total_beds=10, charge_per_day=3000),
                Ward(name="Private Ward", ward_type="Private", total_beds=15, charge_per_day=2000),
                Ward(name="Maternity", ward_type="Maternity", total_beds=10, charge_per_day=1500),
            ]
            session.add_all(wards)
            session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()