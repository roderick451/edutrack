from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models import ActivityLog


activity_logs_bp = Blueprint("activity_logs", __name__)


@activity_logs_bp.route("/activity-logs")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc()).paginate(
        page=page,
        per_page=25,
        error_out=False,
    )
    return render_template("activity_logs.html", logs=logs)
