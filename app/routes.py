import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Student

bp = Blueprint("main", __name__)
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)


@bp.route("/")
def index():
    """Show the home page and the current student's login state."""
    student_id = session.get("student_id")
    student = (
        db.session.get(Student, student_id)
        if student_id is not None
        else None
    )
    return render_template("index.html", student=student)


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Create a student account after validating submitted fields."""
    if request.method == "GET":
        return render_template("register.html")

    student_id = request.form.get("student_id", "").strip()
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not student_id or not full_name or not email or not password:
        flash("All fields are required.", "error")
        return render_template("register.html"), 400
    if not EMAIL_PATTERN.fullmatch(email):
        flash("Enter a valid email address.", "error")
        return render_template("register.html"), 400
    if len(password) < 8:
        flash("Password must be at least 8 characters long.", "error")
        return render_template("register.html"), 400
    if Student.query.filter(
        (Student.student_id == student_id) | (Student.email == email)
    ).first():
        flash("An account with that student ID or email already exists.", "error")
        return render_template("register.html"), 400

    student = Student(
        student_id=student_id,
        full_name=full_name,
        email=email,
    )
    student.set_password(password)
    db.session.add(student)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("An account with that student ID or email already exists.", "error")
        return render_template("register.html"), 400

    flash("Registration successful. Please log in.", "success")
    return redirect(url_for("main.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a student and establish a session."""
    if request.method == "GET":
        return render_template("login.html")

    student_id = request.form.get("student_id", "").strip()
    password = request.form.get("password", "")
    student = Student.query.filter_by(student_id=student_id).first()
    if not student or not student.check_password(password):
        flash("Invalid student ID or password.", "error")
        return render_template("login.html"), 401

    session["student_id"] = student.id
    flash("You are now logged in.", "success")
    return redirect(url_for("main.index"))
