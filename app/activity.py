from flask_login import current_user

from app import db
from app.models import ActivityLog, Course, Student


def record_activity(action, entity_type, entity_label, details=None):
    db.session.add(
        ActivityLog(
            user_id=current_user.id,
            username=current_user.username,
            action=action,
            entity_type=entity_type,
            entity_label=entity_label,
            details=details,
        )
    )


def seed_activity_baseline():
    if ActivityLog.query.first():
        return

    baseline_details = "Record present when Activity Logs was enabled; earlier activity was not recorded."
    entries = [
        ActivityLog(
            username="System",
            action="Enabled",
            entity_type="System",
            entity_label="Activity Logs",
            details="Initial activity snapshot created.",
        )
    ]

    for student in Student.query.order_by(Student.id).all():
        entries.append(
            ActivityLog(
                username="System",
                action="Initial snapshot",
                entity_type="Student",
                entity_label=f"{student.full_name} ({student.student_id})",
                details=baseline_details,
            )
        )

    for course in Course.query.order_by(Course.id).all():
        entries.append(
            ActivityLog(
                username="System",
                action="Initial snapshot",
                entity_type="Course",
                entity_label=f"{course.course_code} - {course.course_name}",
                details=baseline_details,
            )
        )

    db.session.add_all(entries)
    db.session.commit()
