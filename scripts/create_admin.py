import os

from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    if User.query.first():
        print('An admin account already exists.')
    else:
        username = os.getenv('ADMIN_USERNAME', 'admin')
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        email = os.getenv('ADMIN_EMAIL', 'admin@edutrack.local')
        user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        print(f'Admin {username} created successfully.')
