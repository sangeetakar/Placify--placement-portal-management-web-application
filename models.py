from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event

db = SQLAlchemy()


# -----------------------------
# Constants (kept simple)
# -----------------------------
ROLE_ADMIN = "ADMIN"
ROLE_COMPANY = "COMPANY"
ROLE_STUDENT = "STUDENT"

APPROVAL_PENDING = "PENDING"
APPROVAL_APPROVED = "APPROVED"
APPROVAL_REJECTED = "REJECTED"

DRIVE_PENDING = "PENDING"
DRIVE_APPROVED = "APPROVED"
DRIVE_REJECTED = "REJECTED"
DRIVE_CLOSED = "CLOSED"

APP_APPLIED = "APPLIED"
APP_SHORTLISTED = "SHORTLISTED"
APP_SELECTED = "SELECTED"
APP_REJECTED = "REJECTED"
APP_WITHDRAWN = "WITHDRAWN"


# -----------------------------
# Models
# -----------------------------
class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.String(20),
        nullable=False,
        index=True,
    )

    is_active = db.Column(db.Integer, nullable=False, default=1)

    # Minimal but useful timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.CheckConstraint(role.in_([ROLE_ADMIN, ROLE_COMPANY, ROLE_STUDENT]), name="ck_users_role"),
        db.CheckConstraint("is_active IN (0,1)", name="ck_users_is_active"),
    )

    # Relationships (1-1 profiles)
    company_profile = db.relationship("Company", back_populates="user", uselist=False)
    student_profile = db.relationship("Student", back_populates="user", uselist=False)

    def set_password(self, plain_password: str) -> None:
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        return check_password_hash(self.password_hash, plain_password)

    def __repr__(self) -> str:
        return f"<User {self.user_id} {self.username} {self.role}>"


class Company(db.Model):
    __tablename__ = "companies"

    company_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False)

    company_name = db.Column(db.String(200), nullable=False)
    hr_email = db.Column(db.String(200), nullable=True)
    hr_phone = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(300), nullable=True)

    approval_status = db.Column(db.String(20), nullable=False, default=APPROVAL_PENDING)
    is_blacklisted = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.CheckConstraint(
            approval_status.in_([APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_REJECTED]),
            name="ck_companies_approval_status",
        ),
        db.CheckConstraint("is_blacklisted IN (0,1)", name="ck_companies_is_blacklisted"),
    )

    user = db.relationship("User", back_populates="company_profile")
    drives = db.relationship("PlacementDrive", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Company {self.company_id} {self.company_name}>"


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), unique=True, nullable=False)

    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(50), nullable=True)

    department = db.Column(db.String(150), nullable=True)
    degree = db.Column(db.String(150), nullable=True)
    cgpa = db.Column(db.Float, nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)

    # Option 1 resume storage: keep only path in DB

    approval_status = db.Column(db.String(20), nullable=False, default=APPROVAL_PENDING)
    is_blacklisted = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.CheckConstraint(
            approval_status.in_([APPROVAL_PENDING, APPROVAL_APPROVED, APPROVAL_REJECTED]),
            name="ck_students_approval_status",
        ),
        db.CheckConstraint("is_blacklisted IN (0,1)", name="ck_students_is_blacklisted"),
    )

    user = db.relationship("User", back_populates="student_profile")
    applications = db.relationship("Application", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Student {self.student_id} {self.full_name}>"


class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"

    drive_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.company_id"), nullable=False)

    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text, nullable=True)
    eligibility_criteria = db.Column(db.Text, nullable=True)
    application_deadline = db.Column(db.Date, nullable=True)

    drive_status = db.Column(db.String(20), nullable=False, default=DRIVE_PENDING)

    # If company is blacklisted -> set is_active=0 for all its drives
    is_active = db.Column(db.Integer, nullable=False, default=1)

    __table_args__ = (
        db.CheckConstraint(
            drive_status.in_([DRIVE_PENDING, DRIVE_APPROVED, DRIVE_REJECTED, DRIVE_CLOSED]),
            name="ck_drives_drive_status",
        ),
        db.CheckConstraint("is_active IN (0,1)", name="ck_drives_is_active"),
    )

    company = db.relationship("Company", back_populates="drives")
    applications = db.relationship("Application", back_populates="drive", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Drive {self.drive_id} {self.job_title} {self.drive_status}>"


class Application(db.Model):
    __tablename__ = "applications"

    application_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id"), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey("placement_drives.drive_id"), nullable=False)

    applied_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    status = db.Column(db.String(20), nullable=False, default=APP_APPLIED)
    remark = db.Column(db.Text, nullable=True)

    __table_args__ = (
        # Prevent multiple applications by same student to same drive
        db.UniqueConstraint("student_id", "drive_id", name="uq_applications_student_drive"),
        db.CheckConstraint(
            status.in_([APP_APPLIED, APP_SHORTLISTED, APP_SELECTED, APP_REJECTED, APP_WITHDRAWN]),
            name="ck_applications_status",
        ),
    )

    student = db.relationship("Student", back_populates="applications")
    drive = db.relationship("PlacementDrive", back_populates="applications")
    history = db.relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.changed_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<Application {self.application_id} student={self.student_id} drive={self.drive_id} {self.status}>"


class ApplicationStatusHistory(db.Model):
    __tablename__ = "application_status_history"

    history_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.application_id"), nullable=False)

    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)

    changed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint(
            "new_status IN ('APPLIED','SHORTLISTED','SELECTED','REJECTED','WITHDRAWN')",
            name="ck_app_status_history_new_status",
        ),
    )

    application = db.relationship("Application", back_populates="history")
    changed_by = db.relationship("User")

    def __repr__(self) -> str:
        return f"<AppHistory {self.history_id} app={self.application_id} {self.old_status}->{self.new_status}>"


class AdminAction(db.Model):
    __tablename__ = "admin_actions"

    action_id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    action_type = db.Column(db.String(50), nullable=False)  # e.g. APPROVE_COMPANY, BLACKLIST_STUDENT
    target_type = db.Column(db.String(30), nullable=False)  # COMPANY/STUDENT/DRIVE
    target_id = db.Column(db.Integer, nullable=False)

    action_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    admin_user = db.relationship("User")

    def __repr__(self) -> str:
        return f"<AdminAction {self.action_id} {self.action_type} {self.target_type}:{self.target_id}>"


# -----------------------------
# Business rule enforcement
# Company blacklist => drives inactive
# -----------------------------
@event.listens_for(Company, "after_update")
def company_blacklist_cascade(mapper, connection, target: Company):
    """
    If a company gets blacklisted, mark all its drives inactive.
    If unblacklisted, you can choose to reactivate drives, but usually you keep them inactive.
    Here we only enforce the 'blacklisted => inactive' rule.
    """
    if target.is_blacklisted == 1:
        connection.execute(
            PlacementDrive.__table__.update()
            .where(PlacementDrive.company_id == target.company_id)
            .values(is_active=0)
        )


# -----------------------------
# Optional helper: create all tables
# Call this once from a setup script / flask shell.
# -----------------------------
def init_db():
    db.create_all()

    # Check if admin already exists
    existing_admin = User.query.filter_by(role=ROLE_ADMIN).first()

    if not existing_admin:
        admin = User(
            username="admin",
            role=ROLE_ADMIN,
            is_active=1,
        )
        admin.set_password("password")

        db.session.add(admin)
        db.session.commit()

        print("Admin user created successfully.")
    else:
        print("Admin already exists.")
