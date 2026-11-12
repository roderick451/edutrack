from io import StringIO

from flask import Blueprint, Response, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.forms import StudentForm
from app.models import Course, Student


students_bp = Blueprint("students", __name__)


def _student_query():
    query = Student.query.join(Course).add_columns(Course.course_name)
    return query


@students_bp.route("/students")
@login_required
def list_students():
    search_query = request.args.get("q", "", type=str).strip()
    course_filter = request.args.get("course_id", "", type=str)
    year_filter = request.args.get("year_level", "", type=str)
    sort_by = request.args.get("sort", "created_at")
    page = request.args.get("page", 1, type=int)

    query = Student.query.join(Course)

    if search_query:
        query = query.filter(
            (Student.first_name.ilike(f"%{search_query}%"))
            | (Student.last_name.ilike(f"%{search_query}%"))
            | (Student.student_id.ilike(f"%{search_query}%"))
        )

    if course_filter:
        query = query.filter(Student.course_id == int(course_filter))

    if year_filter:
        query = query.filter(Student.year_level == year_filter)

    sort_column = {
        "student_id": Student.student_id,
        "first_name": Student.first_name,
        "last_name": Student.last_name,
        "course": Course.course_name,
        "year_level": Student.year_level,
        "created_at": Student.created_at,
    }.get(sort_by, Student.created_at)

    students = query.order_by(sort_column.asc()).paginate(page=page, per_page=10, error_out=False)
    courses = Course.query.order_by(Course.course_name.asc()).all()
    return render_template("students.html", students=students, courses=courses, search_query=search_query, course_filter=course_filter, year_filter=year_filter, sort_by=sort_by)


@students_bp.route("/students/new", methods=["GET", "POST"])
@login_required
def new_student():
    form = StudentForm()
    form.course_id.choices = [(course.id, course.course_name) for course in Course.query.order_by(Course.course_name).all()]
    if form.validate_on_submit():
        student = Student(
            student_id=form.student_id.data.strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=form.phone.data.strip(),
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            course_id=form.course_id.data,
            year_level=form.year_level.data,
            enrollment_status=form.enrollment_status.data,
        )
        db.session.add(student)
        db.session.commit()
        flash("Student record created successfully.", "success")
        return redirect(url_for("students.list_students"))
    return render_template("student_form.html", form=form, title="Add Student")


@students_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = StudentForm(obj=student)
    form.course_id.choices = [(course.id, course.course_name) for course in Course.query.order_by(Course.course_name).all()]
    if form.validate_on_submit():
        student.student_id = form.student_id.data.strip()
        student.first_name = form.first_name.data.strip()
        student.last_name = form.last_name.data.strip()
        student.email = form.email.data.strip().lower()
        student.phone = form.phone.data.strip()
        student.date_of_birth = form.date_of_birth.data
        student.gender = form.gender.data
        student.course_id = form.course_id.data
        student.year_level = form.year_level.data
        student.enrollment_status = form.enrollment_status.data
        db.session.commit()
        flash("Student record updated successfully.", "success")
        return redirect(url_for("students.list_students"))
    return render_template("student_form.html", form=form, title="Edit Student", student=student)


@students_bp.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully.", "success")
    return redirect(url_for("students.list_students"))


@students_bp.route("/students/<int:student_id>")
@login_required
def student_profile(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template("student_profile.html", student=student)


@students_bp.route("/students/export")
@login_required
def export_students():
    output = StringIO()
    output.write("student_id,first_name,last_name,email,phone,date_of_birth,gender,course,year_level,enrollment_status\n")
    for student in Student.query.join(Course).all():
        output.write(
            f"{student.student_id},{student.first_name},{student.last_name},{student.email},{student.phone},{student.date_of_birth},{student.gender or ''},{student.course.course_name},{student.year_level},{student.enrollment_status}\n"
        )
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=students.csv"
    return response
