import os
from datetime import datetime

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash

from .config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id):
    from .models import User

    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .routes.auth import auth_bp
    from .routes.activity_logs import activity_logs_bp
    from .routes.dashboard import dashboard_bp
    from .routes.reports import reports_bp
    from .routes.students import students_bp
    from .routes.courses import courses_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(activity_logs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(courses_bp)

    @app.context_processor
    def inject_now():
        return {"current_year": datetime.utcnow().year}

    with app.app_context():
        db.create_all()

        from .activity import remove_activity_baseline
        from .models import User

        if User.query.first() is None:
            username = os.getenv("ADMIN_USERNAME", "admin")
            password = os.getenv("ADMIN_PASSWORD", "admin123")
            email = os.getenv("ADMIN_EMAIL", f"{username}@edutrack.local")
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()

        remove_activity_baseline()

    return app
