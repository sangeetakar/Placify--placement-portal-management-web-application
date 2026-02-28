from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User, Student, Company

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")  # Landing page


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return render_template("login.html")

        # Block login if deactivated
        if user.is_active == 0:
            flash("Your account is inactive. Please contact admin.", "error")
            return render_template("login.html")

        # Approval / blacklist checks based on role
        if user.role == "STUDENT":
            student = Student.query.filter_by(user_id=user.user_id).first()
            if not student:
                flash("Student profile not found.", "error")
                return render_template("login.html")

            if student.approval_status != "APPROVED":
                flash("Your registration is pending admin approval.", "warning")
                return render_template("login.html")

            if student.is_blacklisted == 1:
                flash("Your account is blacklisted. Please contact admin.", "error")
                return render_template("login.html")

            session["user_id"] = user.user_id
            session["role"] = user.role
            return redirect(url_for("main.student_dashboard"))

        if user.role == "COMPANY":
            company = Company.query.filter_by(user_id=user.user_id).first()
            if not company:
                flash("Company profile not found.", "error")
                return render_template("login.html")

            if company.approval_status != "APPROVED":
                flash("Company registration is pending admin approval.", "warning")
                return render_template("login.html")

            if company.is_blacklisted == 1:
                flash("Your company is blacklisted. Please contact admin.", "error")
                return render_template("login.html")

            session["user_id"] = user.user_id
            session["role"] = user.role
            return redirect(url_for("main.company_dashboard"))

        # ADMIN
        session["user_id"] = user.user_id
        session["role"] = user.role
        return redirect(url_for("main.admin_dashboard"))

    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.login"))


@bp.route("/studentregister", methods=["GET", "POST"])
def studentregister():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        department = (request.form.get("department") or "").strip()
        degree = (request.form.get("degree") or "").strip()
        cgpa = request.form.get("cgpa")
        graduation_year = request.form.get("graduation_year")

        if not username or not password or not full_name:
            flash("Username, password and full name are required.", "error")
            return render_template("studentregister.html")

        if User.query.filter_by(username=username).first():
            flash("Username already exists. Choose another.", "error")
            return render_template("studentregister.html")

        # Create user
        user = User(username=username, role="STUDENT", is_active=1)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.user_id without committing

        # Create student profile (PENDING approval by default)
        student = Student(
            user_id=user.user_id,
            full_name=full_name,
            email=email,
            phone=phone,
            department=department,
            degree=degree,
            cgpa=float(cgpa) if cgpa else None,
            graduation_year=int(graduation_year) if graduation_year else None,
            resume_path=None,
            approval_status="PENDING",
            is_blacklisted=0,
        )
        db.session.add(student)
        db.session.commit()

        flash("Student registration submitted. Await admin approval.", "success")
        return redirect(url_for("main.login"))

    return render_template("studentregister.html")


@bp.route("/companyregister", methods=["GET", "POST"])
def companyregister():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        company_name = (request.form.get("company_name") or "").strip()
        hr_email = (request.form.get("hr_email") or "").strip()
        hr_phone = (request.form.get("hr_phone") or "").strip()
        website = (request.form.get("website") or "").strip()

        if not username or not password or not company_name:
            flash("Username, password and company name are required.", "error")
            return render_template("companyregister.html")

        if User.query.filter_by(username=username).first():
            flash("Username already exists. Choose another.", "error")
            return render_template("companyregister.html")

        user = User(username=username, role="COMPANY", is_active=1)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.user_id,
            company_name=company_name,
            hr_email=hr_email,
            hr_phone=hr_phone,
            website=website,
            approval_status="PENDING",
            is_blacklisted=0,
        )
        db.session.add(company)
        db.session.commit()

        flash("Company registration submitted. Await admin approval.", "success")
        return redirect(url_for("main.login"))

    return render_template("companyregister.html")


# -------------------
# Dummy dashboards (for now)
# -------------------
def _require_login(role: str):
    return session.get("user_id") and session.get("role") == role

@bp.route("/student/dashboard")
def student_dashboard():
    if not _require_login("STUDENT"):
        flash("Please login as student.", "error")
        return redirect(url_for("main.login"))
    return render_template("student_dashboard.html")

@bp.route("/company/dashboard")
def company_dashboard():
    if not _require_login("COMPANY"):
        flash("Please login as company.", "error")
        return redirect(url_for("main.login"))
    return render_template("company_dashboard.html")

@bp.route("/admin/dashboard")
def admin_dashboard():
    if not _require_login("ADMIN"):
        flash("Please login as admin.", "error")
        return redirect(url_for("main.login"))
    return render_template("admin_dashboard.html")