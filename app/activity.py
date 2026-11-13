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
