import os
from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models import Course, Student, User


@pytest.fixture
def app():
    os.environ['SECRET_KEY'] = 'test-secret'
    os.environ['DATABASE_URL'] = 'sqlite:///' + os.path.join(os.getcwd(), 'test_edutrack.db')
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Remember me' in response.data
    assert b'Forgot password?' in response.data


def test_protected_dashboard_requires_login(client):
    response = client.get('/dashboard')
    assert response.status_code == 302


def test_authenticated_dashboard_renders_reference_sections(app, client):
    with app.app_context():
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'data-greeting>Good morning</span>, Admin!' in response.data
    assert b'Student Distribution by Course' in response.data
    assert b'/reports' in response.data
    assert b'/settings' in response.data


def test_admin_can_update_account_settings(app, client):
    with app.app_context():
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.post('/settings', data={
        'username': 'newadmin',
        'email': 'newadmin@example.com',
        'current_password': 'admin123',
        'new_password': 'newpassword123',
        'confirm_password': 'newpassword123',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account settings updated successfully.' in response.data
    with app.app_context():
        user = User.query.get(user_id)
        assert user.username == 'newadmin'
        assert user.email == 'newadmin@example.com'
        assert user.verify_password('newpassword123')


def test_reports_and_password_help_pages(client):
    assert client.get('/forgot-password').status_code == 200


def test_create_admin_account(client):
    response = client.post('/setup-admin', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert response.status_code == 200
    assert User.query.filter_by(username='admin').count() == 1


def test_student_crud_flow(app, client):
    with app.app_context():
        course = Course(course_code='CS101', course_name='Intro to Computing', description='Basic computing')
        db.session.add(course)
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(user)
        db.session.commit()
        course_id = course.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/students/new')
    assert response.status_code == 200
    assert b'Personal Information' in response.data

    response = client.post('/students/new', data={
        'student_id': 'STU-001',
        'first_name': 'Jane',
        'last_name': 'Doe',
        'email': 'jane@example.com',
        'phone': '09171234567',
        'date_of_birth': '2001-06-10',
        'gender': 'Female',
        'course_id': str(course_id),
        'year_level': '1st Year',
        'enrollment_status': 'Active',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert Student.query.filter_by(student_id='STU-001').count() == 1


def test_duplicate_student_id_prevention(app, client):
    with app.app_context():
        course = Course(course_code='CS201', course_name='Data Structures', description='Data structures basics')
        db.session.add(course)
        db.session.commit()
        course_id = course.id
        existing = Student(student_id='STU-021', first_name='Old', last_name='Student', email='old@example.com', phone='0987654321', date_of_birth=date(2000, 1, 1), gender='Male', course_id=course_id, year_level='2nd Year', enrollment_status='Active')
        db.session.add(existing)
        db.session.commit()

    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True

    response = client.post('/students/new', data={
        'student_id': 'STU-021',
        'first_name': 'New',
        'last_name': 'Student',
        'email': 'new@example.com',
        'phone': '09121234567',
        'date_of_birth': '2002-02-02',
        'gender': 'Female',
        'course_id': str(course_id),
        'year_level': '1st Year',
        'enrollment_status': 'Active',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert Student.query.filter_by(student_id='STU-021').count() == 1


def test_course_crud(app, client):
    with app.app_context():
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/courses')
    assert response.status_code == 200
    assert b'Course Management' in response.data
    response = client.get('/courses?q=algorithm')
    assert response.status_code == 200
    assert b'No courses match your search.' in response.data

    response = client.post('/courses/new', data={'course_code': 'CS102', 'course_name': 'Algorithms', 'description': 'Algorithm design'}, follow_redirects=True)
    assert response.status_code == 200
    assert Course.query.filter_by(course_code='CS102').count() == 1
    assert client.get('/reports').status_code == 200


def test_search_and_filtering(app, client):
    with app.app_context():
        user = User(username='searcher', email='searcher@example.com', password_hash=generate_password_hash('secret123'))
        db.session.add(user)
        course = Course(course_code='MATH101', course_name='Mathematics', description='Math course')
        db.session.add(course)
        db.session.commit()
        course_id = course.id
        student = Student(student_id='STU-099', first_name='Lina', last_name='Martinez', email='lina@example.com', phone='09111111111', date_of_birth=date(2003, 11, 20), gender='Female', course_id=course_id, year_level='2nd Year', enrollment_status='Active')
        db.session.add(student)
        inactive_student = Student(student_id='STU-100', first_name='Kai', last_name='Santos', email='kai@example.com', phone='09112223333', date_of_birth=date(2002, 8, 15), gender='Male', course_id=course_id, year_level='3rd Year', enrollment_status='Inactive')
        db.session.add(inactive_student)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get(f'/students?q=Lina&course_id={course_id}&year_level=2nd+Year&status=Active')
    assert response.status_code == 200
    assert b'Lina' in response.data

    response = client.get('/students?status=Inactive')
    assert response.status_code == 200
    assert b'Kai' in response.data
    assert b'Lina' not in response.data
