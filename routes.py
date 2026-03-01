from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from models import (
    db,
    User,
    Student,
    Company,
    PlacementDrive,
    Application,
    AdminAction,
    APPROVAL_PENDING,
    APPROVAL_APPROVED,
    APPROVAL_REJECTED,
    ROLE_ADMIN,
    ROLE_STUDENT,
    ROLE_COMPANY,
    DRIVE_APPROVED,
    DRIVE_PENDING,
    DRIVE_REJECTED,
    DRIVE_CLOSED,
    ApplicationStatusHistory
)

bp = Blueprint("main", __name__)


# -------------------
# Helper
# -------------------
def _require_login(role: str):
    return session.get("user_id") and session.get("role") == role


# -------------------
# Landing Page
# -------------------
@bp.route("/")
def index():
    return render_template("index.html")


# -------------------
# Login
# -------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        if user.is_active == 0:
            flash("Your account is inactive.", "error")
            return render_template("login.html")

        # ================= STUDENT =================
        if user.role == ROLE_STUDENT:
            student = Student.query.filter_by(user_id=user.user_id).first()

            if not student:
                flash("Student profile not found.", "error")
                return render_template("login.html")

            if student.approval_status == APPROVAL_PENDING:
                flash("Your registration is awaiting admin approval.", "warning")
                return render_template("login.html")

            if student.approval_status == APPROVAL_REJECTED:
                flash("Your registration was rejected by admin.", "error")
                return render_template("login.html")

            if student.is_blacklisted == 1:
                flash("Your account is blacklisted.", "error")
                return render_template("login.html")

            session["user_id"] = user.user_id
            session["role"] = user.role
            return redirect(url_for("main.student_dashboard"))

        # ================= COMPANY =================
        if user.role == ROLE_COMPANY:
            company = Company.query.filter_by(user_id=user.user_id).first()

            if not company:
                flash("Company profile not found.", "error")
                return render_template("login.html")

            if company.approval_status == APPROVAL_PENDING:
                flash("Your registration is awaiting admin approval.", "warning")
                return render_template("login.html")

            if company.approval_status == APPROVAL_REJECTED:
                flash("Your registration was rejected by admin.", "error")
                return render_template("login.html")

            if company.is_blacklisted == 1:
                flash("Your company is blacklisted.", "error")
                return render_template("login.html")

            session["user_id"] = user.user_id
            session["role"] = user.role
            return redirect(url_for("main.company_dashboard"))

        # ================= ADMIN =================
        session["user_id"] = user.user_id
        session["role"] = user.role
        return redirect(url_for("main.admin_dashboard"))

    return render_template("login.html")


# -------------------
# Logout
# -------------------
@bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.login"))


# -------------------
# Student Registration
# -------------------
@bp.route("/studentregister", methods=["GET", "POST"])
def studentregister():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()

        email = request.form.get("email")
        phone = request.form.get("phone")
        department = request.form.get("department")
        degree = request.form.get("degree")
        cgpa = request.form.get("cgpa")
        graduation_year = request.form.get("graduation_year")

        # Prevent duplicate username
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return render_template("studentregister.html")

        user = User(username=username, role=ROLE_STUDENT, is_active=1)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Convert numeric fields safely
        cgpa_value = float(cgpa) if cgpa else None
        graduation_year_value = int(graduation_year) if graduation_year else None

        student = Student(
            user_id=user.user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            department=department,
            degree=degree,
            cgpa=cgpa_value,
            graduation_year=graduation_year_value,
            approval_status=APPROVAL_PENDING,
            is_blacklisted=0,
        )

        db.session.add(student)
        db.session.commit()

        flash("Student registration submitted.", "success")
        return redirect(url_for("main.login"))

    return render_template("studentregister.html")


# -------------------
# Company Registration
# -------------------
@bp.route("/companyregister", methods=["GET", "POST"])
def companyregister():
    if request.method == "POST":
        username = request.form.get("username").strip()
        password = request.form.get("password")
        company_name = request.form.get("company_name").strip()

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "error")
            return render_template("companyregister.html")

        user = User(username=username, role=ROLE_COMPANY, is_active=1)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.user_id,
            company_name=company_name,
            approval_status=APPROVAL_PENDING,
            is_blacklisted=0,
        )

        db.session.add(company)
        db.session.commit()

        flash("Company registration submitted.", "success")
        return redirect(url_for("main.login"))

    return render_template("companyregister.html")


# -------------------
# Student Dashboard
# -------------------
@bp.route("/student/dashboard")
def student_dashboard():
    if not _require_login(ROLE_STUDENT):
        return redirect(url_for("main.login"))

    student = Student.query.filter_by(user_id=session["user_id"]).first()

    approved_drives = PlacementDrive.query.filter_by(
        drive_status=DRIVE_APPROVED,
        is_active=1
    ).all()

    applications = Application.query.filter_by(
        student_id=student.student_id
    ).all()

    return render_template(
        "student_dashboard.html",
        student=student,
        approved_drives=approved_drives,
        applications=applications
    )


# -------------------
# Company Dashboard
# -------------------
@bp.route("/company/dashboard")
def company_dashboard():
    if not _require_login(ROLE_COMPANY):
        return redirect(url_for("main.login"))

    company = Company.query.filter_by(user_id=session["user_id"]).first()

    if company.is_blacklisted == 1:
        flash("Your company is blacklisted.", "error")
        return redirect(url_for("main.logout"))

    drives = PlacementDrive.query.filter_by(company_id=company.company_id).all()

    return render_template("company_dashboard.html", company=company, drives=drives)

# -------------------
# Student Apply
# -------------------
@bp.route("/student/apply/<int:drive_id>")
def apply_drive(drive_id):
    if not _require_login(ROLE_STUDENT):
        return redirect(url_for("main.login"))

    student = Student.query.filter_by(user_id=session["user_id"]).first()

    if student.is_blacklisted == 1:
        flash("You are blacklisted.", "error")
        return redirect(url_for("main.student_dashboard"))

    # ✅ FIRST fetch drive
    drive = PlacementDrive.query.get_or_404(drive_id)

    # ✅ Then check status
    if drive.is_active == 0 or drive.drive_status != DRIVE_APPROVED:
        flash("Drive is not active.", "warning")
        return redirect(url_for("main.student_dashboard"))

    # ✅ Deadline check (NOW drive exists)
    from datetime import date
    if drive.application_deadline and drive.application_deadline < date.today():
        flash("Application deadline has passed.", "error")
        return redirect(url_for("main.student_dashboard"))

    # ✅ Prevent duplicate application
    existing = Application.query.filter_by(
        student_id=student.student_id,
        drive_id=drive_id
    ).first()

    if existing:
        flash("Already applied.", "warning")
        return redirect(url_for("main.student_dashboard"))

    application = Application(
        student_id=student.student_id,
        drive_id=drive_id,
        status="APPLIED"
    )

    db.session.add(application)
    db.session.commit()

    flash("Application submitted.", "success")
    return redirect(url_for("main.student_dashboard"))


# -------------------
# View Applications (Company)
# -------------------
@bp.route("/company/drive/<int:drive_id>/applications")
def view_applications(drive_id):
    if not _require_login(ROLE_COMPANY):
        return redirect(url_for("main.login"))

    company = Company.query.filter_by(user_id=session["user_id"]).first()
    drive = PlacementDrive.query.get_or_404(drive_id)

    if drive.company_id != company.company_id:
        flash("Unauthorized access.", "error")
        return redirect(url_for("main.company_dashboard"))

    applications = Application.query.filter_by(drive_id=drive_id).all()

    return render_template(
        "company_applications.html",
        drive=drive,
        applications=applications
    )


# -------------------
# Update Application Status
# -------------------
@bp.route("/company/application/<int:application_id>/update/<string:status>")
def update_application_status(application_id, status):
    if not _require_login(ROLE_COMPANY):
        return redirect(url_for("main.login"))

    company = Company.query.filter_by(user_id=session["user_id"]).first()
    application = Application.query.get_or_404(application_id)

    #  SECURITY CHECK — ensure application belongs to this company
    if application.drive.company_id != company.company_id:
        flash("Unauthorized action.", "error")
        return redirect(url_for("main.company_dashboard"))

    allowed_status = ["SHORTLISTED", "REJECTED", "SELECTED"]

    if status not in allowed_status:
        flash("Invalid status.", "error")
        return redirect(url_for("main.company_dashboard"))

    old_status = application.status
    application.status = status

    # Add status history
    history = ApplicationStatusHistory(
        application_id=application.application_id,
        old_status=old_status,
        new_status=status,
        changed_by_user_id=session["user_id"]
    )

    db.session.add(history)
    db.session.commit()

    flash("Application status updated.", "success")
    return redirect(request.referrer)


# -------------------
# Company Create Drive
# -------------------
@bp.route("/company/create_drive", methods=["GET", "POST"])
def create_drive():
    if not _require_login(ROLE_COMPANY):
        return redirect(url_for("main.login"))

    company = Company.query.filter_by(user_id=session["user_id"]).first()

    if company.is_blacklisted == 1:
        flash("Blacklisted companies cannot create drives.", "error")
        return redirect(url_for("main.company_dashboard"))
    
    if company.approval_status != APPROVAL_APPROVED:
        flash("Only approved companies can create drives.", "error")
        return redirect(url_for("main.company_dashboard"))

    if request.method == "POST":
        from datetime import datetime

        job_title = request.form.get("job_title")
        job_description = request.form.get("job_description")
        eligibility = request.form.get("eligibility")
        deadline_str = request.form.get("deadline")

        # Convert deadline string → Python date
        deadline_value = None
        if deadline_str:
            deadline_value = datetime.strptime(deadline_str, "%Y-%m-%d").date()

        drive = PlacementDrive(
            company_id=company.company_id,
            job_title=job_title,
            job_description=job_description,
            eligibility_criteria=eligibility,
            application_deadline=deadline_value,
            drive_status=DRIVE_PENDING,
            is_active=1,
        )

        db.session.add(drive)
        db.session.commit()

        flash("Drive submitted for admin approval.", "success")
        return redirect(url_for("main.company_dashboard"))
    return render_template("create_drive.html")


# -------------------
# Close Drive (Company)
# -------------------
@bp.route("/company/drive/<int:drive_id>/close")
def close_drive(drive_id):
    if not _require_login(ROLE_COMPANY):
        return redirect(url_for("main.login"))

    company = Company.query.filter_by(user_id=session["user_id"]).first()
    drive = PlacementDrive.query.get_or_404(drive_id)

    # 🔒 Ensure drive belongs to company
    if drive.company_id != company.company_id:
        flash("Unauthorized action.", "error")
        return redirect(url_for("main.company_dashboard"))

    drive.drive_status = DRIVE_CLOSED
    drive.is_active = 0

    db.session.commit()

    flash("Drive closed successfully.", "warning")
    return redirect(url_for("main.company_dashboard"))
# -------------------
# Admin Approvals
# -------------------
@bp.route("/admin/student/<int:student_id>/approve")
def approve_student(student_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    student = Student.query.get_or_404(student_id)
    student.approval_status = APPROVAL_APPROVED

    db.session.add(AdminAction(
        admin_user_id=session["user_id"],
        action_type="APPROVE_STUDENT",
        target_type="STUDENT",
        target_id=student.student_id
    ))

    db.session.commit()
    flash("Student approved.", "success")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/company/<int:company_id>/approve")
def approve_company(company_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    company = Company.query.get_or_404(company_id)
    company.approval_status = APPROVAL_APPROVED

    db.session.add(AdminAction(
        admin_user_id=session["user_id"],
        action_type="APPROVE_COMPANY",
        target_type="COMPANY",
        target_id=company.company_id
    ))

    db.session.commit()
    flash("Company approved.", "success")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/drive/<int:drive_id>/approve")
def approve_drive(drive_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.drive_status = DRIVE_APPROVED

    db.session.add(AdminAction(
        admin_user_id=session["user_id"],
        action_type="APPROVE_DRIVE",
        target_type="DRIVE",
        target_id=drive.drive_id
    ))

    db.session.commit()
    flash("Drive approved.", "success")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/drive/<int:drive_id>/reject")
def reject_drive(drive_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.drive_status = DRIVE_REJECTED

    db.session.add(AdminAction(
        admin_user_id=session["user_id"],
        action_type="REJECT_DRIVE",
        target_type="DRIVE",
        target_id=drive.drive_id
    ))

    db.session.commit()
    flash("Drive rejected.", "warning")
    return redirect(url_for("main.admin_dashboard"))


# -------------------
# Admin Activate / Deactivate Drive
# -------------------
@bp.route("/admin/drive/<int:drive_id>/deactivate")
def deactivate_drive(drive_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.is_active = 0

    db.session.commit()
    flash("Drive deactivated.", "warning")
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/admin/drive/<int:drive_id>/activate")
def activate_drive(drive_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.is_active = 1

    db.session.commit()
    flash("Drive activated.", "success")
    return redirect(url_for("main.admin_dashboard"))


# -------------------
# Blacklist Student (Auto Reject Applications)
# -------------------
@bp.route("/admin/blacklist_student/<int:student_id>")
def blacklist_student(student_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = 1

    for app in student.applications:
        if app.status in ["APPLIED", "SHORTLISTED"]:
            app.status = "REJECTED"

    db.session.add(AdminAction(
        admin_user_id=session["user_id"],
        action_type="BLACKLIST_STUDENT",
        target_type="STUDENT",
        target_id=student.student_id
    ))

    db.session.commit()
    flash("Student blacklisted and applications rejected.", "warning")
    return redirect(url_for("main.admin_dashboard"))


# -------------------
# Blacklist Company (Deactivate Drives + Reject Applications)
# -------------------
@bp.route("/admin/blacklist_company/<int:company_id>")
def blacklist_company(company_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = 1

    for drive in company.drives:
        drive.is_active = 0
        drive.drive_status = DRIVE_REJECTED

        for app in drive.applications:
            if app.status in ["APPLIED", "SHORTLISTED"]:
                app.status = "REJECTED"

    db.session.add(AdminAction(
        admin_user_id=session["user_id"],
        action_type="BLACKLIST_COMPANY",
        target_type="COMPANY",
        target_id=company.company_id
    ))

    db.session.commit()
    flash("Company blacklisted. Drives deactivated and applications rejected.", "warning")
    return redirect(url_for("main.admin_dashboard"))


# -------------------
# Admin Search
# -------------------
@bp.route("/admin/search")
def admin_search():
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    query = request.args.get("q", "").strip()

    students = Student.query.filter(
        Student.full_name.ilike(f"%{query}%")
    ).all()

    companies = Company.query.filter(
        Company.company_name.ilike(f"%{query}%")
    ).all()

    return render_template(
        "admin_search.html",
        query=query,
        students=students,
        companies=companies,
    )

@bp.route("/admin/student/<int:student_id>/reject")
def reject_student(student_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    student = Student.query.get_or_404(student_id)
    student.approval_status = APPROVAL_REJECTED
    db.session.commit()

    flash("Student rejected.", "warning")
    return redirect(url_for("main.admin_dashboard"))

@bp.route("/admin/company/<int:company_id>/reject")
def reject_company(company_id):
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    company = Company.query.get_or_404(company_id)
    company.approval_status = APPROVAL_REJECTED
    db.session.commit()

    flash("Company rejected.", "warning")
    return redirect(url_for("main.admin_dashboard"))

@bp.route("/admin/dashboard")
def admin_dashboard():
    if not _require_login(ROLE_ADMIN):
        return redirect(url_for("main.login"))

    # ================= COUNTS =================
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()

    # ================= APPROVAL REQUESTS =================
    pending_students = Student.query.filter_by(
        approval_status=APPROVAL_PENDING
    ).all()

    pending_companies = Company.query.filter_by(
        approval_status=APPROVAL_PENDING
    ).all()

    pending_drives = PlacementDrive.query.filter_by(
        drive_status=DRIVE_PENDING
    ).all()

    # ================= REJECTED =================
    rejected_students = Student.query.filter_by(
        approval_status=APPROVAL_REJECTED
    ).all()

    rejected_companies = Company.query.filter_by(
        approval_status=APPROVAL_REJECTED
    ).all()

    rejected_drives = PlacementDrive.query.filter_by(
        drive_status=DRIVE_REJECTED
    ).all()

    # ================= ACTIVE =================
    active_students = Student.query.filter_by(
        approval_status=APPROVAL_APPROVED,
        is_blacklisted=0
    ).all()

    blacklisted_students = Student.query.filter_by(
        is_blacklisted=1
    ).all()

    active_companies = Company.query.filter_by(
        approval_status=APPROVAL_APPROVED,
        is_blacklisted=0
    ).all()

    blacklisted_companies = Company.query.filter_by(
        is_blacklisted=1
    ).all()

    active_drives = PlacementDrive.query.filter_by(
        drive_status=DRIVE_APPROVED,
        is_active=1
    ).all()

    all_drives = PlacementDrive.query.order_by(
        PlacementDrive.drive_id.desc()
    ).all()

    all_applications = Application.query.order_by(
        Application.application_id.desc()
    ).all()

    return render_template(
        "admin_dashboard.html",

        # COUNTS
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,

        # APPROVALS
        pending_students=pending_students,
        pending_companies=pending_companies,
        pending_drives=pending_drives,

        # REJECTED
        rejected_students=rejected_students,
        rejected_companies=rejected_companies,
        rejected_drives=rejected_drives,

        # ACTIVE
        active_students=active_students,
        blacklisted_students=blacklisted_students,
        active_companies=active_companies,
        blacklisted_companies=blacklisted_companies,
        active_drives=active_drives,
        all_drives=all_drives,
        all_applications=all_applications,
    )