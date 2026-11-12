from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.models import Course, Student


reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
@login_required
def index():
    total_students = Student.query.count()
    total_courses = Course.query.count()
    status_counts = {
        status: Student.query.filter_by(enrollment_status=status).count()
        for status in ("Active", "Inactive", "Graduated")
    }
    course_summary = (
        db.session.query(Course, func.count(Student.id).label("student_count"))
        .outerjoin(Student)
        .group_by(Course.id)
        .order_by(Course.course_name.asc())
        .all()
    )
    return render_template(
        "reports.html",
        total_students=total_students,
        total_courses=total_courses,
        status_counts=status_counts,
        course_summary=course_summary,
    )
