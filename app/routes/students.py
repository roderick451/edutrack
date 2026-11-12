from io import StringIO

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.forms import StudentForm
from app.models import Course, Student


students_bp = Blueprint("students", __name__)


def _student_query():
    query = Student.query.join(Course).add_columns(Course.course_name)
    return query


def _create_student(form):
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


def _update_student(student, form):
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


def _student_form(student=None, prefix=None, course_choices=None):
    form = StudentForm(obj=student, prefix=prefix) if prefix else StudentForm(obj=student)
    form.course_id.choices = course_choices if course_choices is not None else [
        (course.id, course.course_name) for course in Course.query.order_by(Course.course_name).all()
    ]
    if student:
        form.student_id_value = student.id
        form.student_email_value = student.id
    return form


@students_bp.route("/students", methods=["GET", "POST"])
@login_required
def list_students():
    search_query = request.args.get("q", "", type=str).strip()
    course_filter = request.args.get("course_id", "", type=str)
    year_filter = request.args.get("year_level", "", type=str)
    status_filter = request.args.get("status", "", type=str)
    sort_by = request.args.get("sort", "created_at")
    page = request.args.get("page", 1, type=int)
    editing_student_id = request.form.get("editing_student_id", type=int)
    modal_student_id = request.args.get("id", type=int) if request.args.get("modal") == "edit" else editing_student_id

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

    if status_filter in {"Active", "Inactive", "Graduated"}:
        query = query.filter(Student.enrollment_status == status_filter)

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
    course_choices = [(course.id, course.course_name) for course in courses]
    form = _student_form(course_choices=course_choices)
    open_student_modal = request.args.get("modal") == "add"
    modal_to_open = "student-modal" if open_student_modal else None

    edit_forms = {}
    if modal_student_id:
        edit_student = db.session.get(Student, modal_student_id)
        if edit_student and edit_student in students.items:
            edit_form = _student_form(edit_student, prefix=f"student-{edit_student.id}", course_choices=course_choices)
            edit_forms[edit_student.id] = edit_form
            modal_to_open = f"edit-student-{edit_student.id}"

    if request.method == "POST":
        student = db.session.get(Student, editing_student_id) if editing_student_id else None
        if editing_student_id and student is None:
            abort(404)
        form = _student_form(student, prefix=f"student-{student.id}", course_choices=course_choices) if student else form
        if form.validate_on_submit():
            if student:
                _update_student(student, form)
                flash("Student record updated successfully.", "success")
            else:
                _create_student(form)
                flash("Student record created successfully.", "success")
            return redirect(url_for("students.list_students"))
        if student:
            modal_student_id = student.id
            modal_to_open = f"edit-student-{student.id}"
            edit_forms[student.id] = form
        else:
            open_student_modal = True
            modal_to_open = "student-modal"

    for student in students.items:
        if student.id not in edit_forms:
            edit_forms[student.id] = _student_form(student, prefix=f"student-{student.id}", course_choices=course_choices)

    return render_template(
        "students.html",
        students=students,
        courses=courses,
        form=form,
        edit_forms=edit_forms,
        open_student_modal=open_student_modal,
        modal_to_open=modal_to_open,
        search_query=search_query,
        course_filter=course_filter,
        year_filter=year_filter,
        status_filter=status_filter,
        sort_by=sort_by,
    )


@students_bp.route("/students/new", methods=["GET", "POST"])
@login_required
def new_student():
    form = _student_form()
    if form.validate_on_submit():
        _create_student(form)
        flash("Student record created successfully.", "success")
        return redirect(url_for("students.list_students"))
    return render_template("student_form.html", form=form, title="Add Student")


@students_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = _student_form(student)
    if form.validate_on_submit():
        _update_student(student, form)
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
