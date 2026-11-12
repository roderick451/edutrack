from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.forms import CourseForm
from app.models import Course, Student


courses_bp = Blueprint("courses", __name__)


@courses_bp.route("/courses")
@login_required
def list_courses():
    search_query = request.args.get("q", "", type=str).strip()
    query = Course.query
    if search_query:
        query = query.filter(
            Course.course_code.ilike(f"%{search_query}%")
            | Course.course_name.ilike(f"%{search_query}%")
            | Course.description.ilike(f"%{search_query}%")
        )
    courses = query.order_by(Course.course_name.asc()).all()
    return render_template("courses.html", courses=courses, search_query=search_query)


@courses_bp.route("/courses/new", methods=["GET", "POST"])
@login_required
def new_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            course_code=form.course_code.data.strip().upper(),
            course_name=form.course_name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created successfully.", "success")
        return redirect(url_for("courses.list_courses"))
    return render_template("course_form.html", form=form, title="Add Course")


@courses_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.course_code = form.course_code.data.strip().upper()
        course.course_name = form.course_name.data.strip()
        course.description = form.description.data.strip() if form.description.data else None
        db.session.commit()
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
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted successfully.", "success")
    return redirect(url_for("courses.list_courses"))
