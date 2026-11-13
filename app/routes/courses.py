from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.forms import CourseForm
from app.models import Course, Student


courses_bp = Blueprint("courses", __name__)


def _create_course(form):
    course = Course(
        course_code=form.course_code.data.strip().upper(),
        course_name=form.course_name.data.strip(),
        description=form.description.data.strip() if form.description.data else None,
    )
    db.session.add(course)
    db.session.commit()


def _update_course(course, form):
    course.course_code = form.course_code.data.strip().upper()
    course.course_name = form.course_name.data.strip()
    course.description = form.description.data.strip() if form.description.data else None
    db.session.commit()


def _course_form(course=None, prefix=None):
    form = CourseForm(obj=course, prefix=prefix) if prefix else CourseForm(obj=course)
    if course:
        form.course_id = course.id
    return form


@courses_bp.route("/courses", methods=["GET", "POST"])
@login_required
def list_courses():
    search_query = request.args.get("q", "", type=str).strip()
    editing_course_id = request.form.get("editing_course_id", type=int)
    modal_course_id = request.args.get("id", type=int) if request.args.get("modal") == "edit" else editing_course_id
    query = Course.query
    if search_query:
        query = query.filter(
            Course.course_code.ilike(f"%{search_query}%")
            | Course.course_name.ilike(f"%{search_query}%")
            | Course.description.ilike(f"%{search_query}%")
        )
    courses = query.order_by(Course.course_name.asc()).all()
    form = CourseForm()
    open_course_modal = request.args.get("modal") == "add"
    modal_to_open = "course-modal" if open_course_modal else None
    edit_forms = {}

    if modal_course_id:
        edit_course = db.session.get(Course, modal_course_id)
        if edit_course and edit_course in courses:
            edit_forms[edit_course.id] = _course_form(edit_course, prefix=f"course-{edit_course.id}")
            modal_to_open = f"edit-course-{edit_course.id}"

    if request.method == "POST":
        course = db.session.get(Course, editing_course_id) if editing_course_id else None
        if editing_course_id and course is None:
            abort(404)
        form = _course_form(course, prefix=f"course-{course.id}") if course else form
        if form.validate_on_submit():
            if course:
                _update_course(course, form)
                flash("Course updated successfully.", "success")
            else:
                _create_course(form)
                flash("Course created successfully.", "success")
            return redirect(url_for("courses.list_courses"))
        if course:
            edit_forms[course.id] = form
            modal_to_open = f"edit-course-{course.id}"
        else:
            open_course_modal = True
            modal_to_open = "course-modal"

    for course in courses:
        if course.id not in edit_forms:
            edit_forms[course.id] = _course_form(course, prefix=f"course-{course.id}")

    return render_template(
        "courses.html",
        courses=courses,
        form=form,
        edit_forms=edit_forms,
        open_course_modal=open_course_modal,
        modal_to_open=modal_to_open,
        search_query=search_query,
    )


@courses_bp.route("/courses/new", methods=["GET", "POST"])
@login_required
def new_course():
    form = CourseForm()
    if form.validate_on_submit():
        _create_course(form)
        flash("Course created successfully.", "success")
        return redirect(url_for("courses.list_courses"))
    return render_template("course_form.html", form=form, title="Add Course")


@courses_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = _course_form(course)
    if form.validate_on_submit():
        _update_course(course, form)
        flash("Course updated successfully.", "success")
        return redirect(url_for("courses.list_courses"))
    return render_template("course_form.html", form=form, title="Edit Course", course=course)


@courses_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    if Student.query.filter_by(course_id=course.id).count() > 0:
        flash("Cannot delete a course with assigned students.", "error")
        return redirect(url_for("courses.list_courses"))

    reason = request.form.get("reason", "").strip()
    if not 5 <= len(reason) <= 500:
        flash("Enter a reason of 5 to 500 characters before removing this course.", "error")
        return redirect(url_for("courses.list_courses"))

    db.session.delete(course)
    db.session.commit()
    flash("Course deleted successfully.", "success")
    return redirect(url_for("courses.list_courses"))
