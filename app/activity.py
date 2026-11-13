from flask_login import current_user

from app import db
from app.models import ActivityLog


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


def remove_activity_baseline():
    baseline_details = "Record present when Activity Logs was enabled; earlier activity was not recorded."
    snapshots_removed = ActivityLog.query.filter(
        ActivityLog.username == "System",
        ActivityLog.action == "Initial snapshot",
        ActivityLog.entity_type.in_(("Student", "Course")),
        ActivityLog.details == baseline_details,
    ).delete(synchronize_session=False)
    baseline_marker_removed = ActivityLog.query.filter_by(
        username="System",
        action="Enabled",
        entity_type="System",
        entity_label="Activity Logs",
        details="Initial activity snapshot created.",
    ).delete(synchronize_session=False)
    historical_entries_removed = ActivityLog.query.filter(
        ActivityLog.action == "Created (historical)",
        ActivityLog.details.like(
            "Backfilled % from created_at; original actor and prior field values were not recorded."
        ),
    ).delete(synchronize_session=False)

    if snapshots_removed or baseline_marker_removed or historical_entries_removed:
        db.session.commit()
