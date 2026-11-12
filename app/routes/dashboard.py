from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.models import Course, Student


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    total_students = Student.query.count()
    total_courses = Course.query.count()
    active_enrollments = Student.query.filter_by(enrollment_status="Active").count()
    new_this_week = Student.query.filter(Student.created_at >= datetime.utcnow() - timedelta(days=7)).count()

    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    course_distribution = db.session.query(Course.course_name, func.count(Student.id)).outerjoin(Student).group_by(Course.id).order_by(func.count(Student.id).desc()).all()
    year_distribution = db.session.query(Student.year_level, func.count(Student.id)).group_by(Student.year_level).all()

    return render_template(
        "dashboard.html",
        total_students=total_students,
        total_courses=total_courses,
        active_enrollments=active_enrollments,
        new_this_week=new_this_week,
        recent_students=recent_students,
        course_distribution=course_distribution,
        year_distribution=year_distribution,
    )
