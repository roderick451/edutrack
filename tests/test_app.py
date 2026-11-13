import os
from datetime import date

import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.activity import remove_activity_baseline
from app.models import ActivityLog, Course, Student, User


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
    assert client.get('/activity-logs').status_code == 302


def test_activity_log_removes_synthetic_entries_and_preserves_real_actions(app):
    with app.app_context():
        ActivityLog.query.delete()
        db.session.add_all([
            ActivityLog(
                username='System',
                action='Initial snapshot',
                entity_type='Student',
                entity_label='Fake historical record',
                details='Record present when Activity Logs was enabled; earlier activity was not recorded.',
            ),
            ActivityLog(
                username='Not recorded',
                action='Created (historical)',
                entity_type='Course',
                entity_label='Fake backfilled course',
                details='Backfilled course record #1 from created_at; original actor and prior field values were not recorded.',
            ),
            ActivityLog(
                username='admin',
                action='Created',
                entity_type='Student',
                entity_label='Actual Student (STU-REAL-001)',
                details='Real creation already recorded.',
            ),
        ])
        db.session.commit()

        remove_activity_baseline()
        remove_activity_baseline()

        entries = ActivityLog.query.order_by(ActivityLog.id).all()
        assert len(entries) == 1
        assert entries[0].action == 'Created'
        assert entries[0].entity_label == 'Actual Student (STU-REAL-001)'


def test_student_csv_export_is_logged_as_a_real_activity(app, client):
    with app.app_context():
        course = Course(course_code='EXPORT101', course_name='Export Test Course')
        user = User(username='exporter', email='exporter@example.com', password_hash=generate_password_hash('secret123'))
        db.session.add_all([course, user])
        db.session.commit()
        student = Student(
            student_id='STU-EXPORT-001',
            first_name='Morgan',
            last_name='Reyes',
            email='morgan.reyes@example.com',
            phone='09111111111',
            date_of_birth=date(2003, 11, 20),
            course_id=course.id,
            year_level='1st Year',
            enrollment_status='Active',
        )
        db.session.add(student)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/students/export')
    assert response.status_code == 200
    assert b'STU-EXPORT-001' in response.data
    with app.app_context():
        activity = ActivityLog.query.filter_by(action='Exported', entity_type='Student').one()
        assert activity.username == 'exporter'
        assert activity.details == 'Exported 1 student record(s) to CSV.'


def test_activity_log_explains_when_no_real_actions_are_recorded(app, client):
    with app.app_context():
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/activity-logs')
    assert response.status_code == 200
    assert b'No real activity has been recorded yet.' in response.data


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
    assert b'class="sidebar-logout"' in response.data
    assert b'<span>Logout</span>' in response.data
    assert b'aria-label="Notifications"' in response.data
    assert b'/reports' in response.data
    assert b'/settings' in response.data
    welcome = response.data.split(b'<section class="dashboard-welcome">', 1)[1].split(b'</section>', 1)[0]
    assert b'Add Student' not in welcome
    assert b'/students?modal=add' in response.data
    assert b'/courses?modal=add' in response.data


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
        activity = ActivityLog.query.filter_by(entity_type='Account', action='Updated').one()
        assert activity.username == 'newadmin'


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
    with app.app_context():
        assert Student.query.filter_by(student_id='STU-001').count() == 1
        activity = ActivityLog.query.filter_by(entity_type='Student', action='Created').one()
        assert activity.entity_label == 'Jane Doe (STU-001)'
        assert activity.details == 'Enrolled in Intro to Computing.'


def test_student_list_modal_creates_student(app, client):
    with app.app_context():
        course = Course(course_code='CS101', course_name='Intro to Computing')
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add_all([course, user])
        db.session.commit()
        course_id = course.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/students?modal=add')
    assert response.status_code == 200
    assert b'id="student-modal"' in response.data
    assert b'data-open-on-load="true"' in response.data

    response = client.post('/students', data={
        'student_id': 'STU-101',
        'first_name': 'Alex',
        'last_name': 'Rivera',
        'email': 'alex.rivera@gmail.com',
        'phone': '09171234567',
        'date_of_birth': '2001-06-10',
        'gender': 'Other',
        'course_id': str(course_id),
        'year_level': '1st Year',
        'enrollment_status': 'Active',
        'submit': 'Add Student',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Student record created successfully.' in response.data
    assert Student.query.filter_by(email='alex.rivera@gmail.com').count() == 1


@pytest.mark.parametrize('phone', ['0912345678', '091234567890', '09123abc789'])
def test_student_phone_requires_exactly_11_digits(app, client, phone):
    with app.app_context():
        course = Course(course_code='CS101', course_name='Intro to Computing')
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add_all([course, user])
        db.session.commit()
        course_id = course.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.post('/students/new', data={
        'student_id': 'STU-103',
        'first_name': 'Alex',
        'last_name': 'Rivera',
        'email': 'alex.rivera@gmail.com',
        'phone': phone,
        'date_of_birth': '2001-06-10',
        'gender': 'Other',
        'course_id': str(course_id),
        'year_level': '1st Year',
        'enrollment_status': 'Active',
    })
    assert response.status_code == 200
    assert b'Phone number must contain exactly 11 digits.' in response.data
    with app.app_context():
        assert Student.query.filter_by(student_id='STU-103').count() == 0


def test_student_list_view_and_edit_modals(app, client):
    with app.app_context():
        course = Course(course_code='CS101', course_name='Intro to Computing')
        db.session.add(course)
        db.session.flush()
        student = Student(
            student_id='STU-102',
            first_name='Maya',
            last_name='Santos',
            email='maya.santos@gmail.com',
            phone='09171234567',
            date_of_birth=date(2002, 4, 10),
            gender='Female',
            course_id=course.id,
            year_level='2nd Year',
            enrollment_status='Active',
        )
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add_all([student, user])
        db.session.commit()
        student_id = student.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/students')
    assert response.status_code == 200
    assert f'id="view-student-{student_id}"'.encode() in response.data
    assert f'id="edit-student-{student_id}"'.encode() in response.data
    assert f'name="student-{student_id}-first_name"'.encode() in response.data
    assert b'Academic Information' in response.data
    assert b'maya.santos@gmail.com' in response.data

    response = client.get(f'/students?modal=edit&id={student_id}')
    assert response.status_code == 200
    edit_dialog = response.data.split(f'id="edit-student-{student_id}"'.encode(), 1)[1].split(b'>', 1)[0]
    assert b'data-open-on-load="true"' in edit_dialog

    response = client.post('/students', data={
        'editing_student_id': str(student_id),
        f'student-{student_id}-student_id': 'STU-102',
        f'student-{student_id}-first_name': 'Maya',
        f'student-{student_id}-last_name': 'Reyes',
        f'student-{student_id}-email': 'maya.reyes@gmail.com',
        f'student-{student_id}-phone': '09171234567',
        f'student-{student_id}-date_of_birth': '2002-04-10',
        f'student-{student_id}-gender': 'Female',
        f'student-{student_id}-course_id': '1',
        f'student-{student_id}-year_level': '2nd Year',
        f'student-{student_id}-enrollment_status': 'Active',
        f'student-{student_id}-submit': 'Save Changes',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Student record updated successfully.' in response.data
    with app.app_context():
        student = db.session.get(Student, student_id)
        assert student.last_name == 'Reyes'
        assert student.email == 'maya.reyes@gmail.com'


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
    activity = ActivityLog.query.filter_by(entity_type='Course', action='Created').one()
    assert activity.username == 'admin'
    assert activity.entity_label == 'CS102 - Algorithms'
    activity_page = client.get('/activity-logs')
    assert activity_page.status_code == 200
    assert b'Activity Logs' in activity_page.data
    assert b'CS102 - Algorithms' in activity_page.data
    assert activity_page.data.index(b'Activity Logs') < activity_page.data.index(b'Settings')
    assert client.get('/reports').status_code == 200


def test_course_list_modal_creates_course(app, client):
    with app.app_context():
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/courses?modal=add')
    assert response.status_code == 200
    assert b'id="course-modal"' in response.data
    assert b'data-open-on-load="true"' in response.data

    response = client.post('/courses', data={
        'course_code': 'bsit',
        'course_name': 'Information Technology',
        'description': 'Technology program',
        'submit': 'Add Course',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Course created successfully.' in response.data
    assert Course.query.filter_by(course_code='BSIT').count() == 1


def test_course_list_edit_modal_updates_course(app, client):
    with app.app_context():
        course = Course(course_code='BSIT', course_name='Information Technology', description='Original description')
        user = User(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add_all([course, user])
        db.session.commit()
        course_id = course.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.get('/courses')
    assert response.status_code == 200
    assert f'id="edit-course-{course_id}"'.encode() in response.data
    assert f'name="course-{course_id}-course_code"'.encode() in response.data

    response = client.get(f'/courses?modal=edit&id={course_id}')
    edit_dialog = response.data.split(f'id="edit-course-{course_id}"'.encode(), 1)[1].split(b'>', 1)[0]
    assert b'data-open-on-load="true"' in edit_dialog

    response = client.post('/courses', data={
        'editing_course_id': str(course_id),
        f'course-{course_id}-course_code': 'bsit',
        f'course-{course_id}-course_name': 'Bachelor of Science in Information Technology',
        f'course-{course_id}-description': 'Updated description',
        f'course-{course_id}-submit': 'Save Changes',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Course updated successfully.' in response.data
    with app.app_context():
        course = db.session.get(Course, course_id)
        assert course.course_code == 'BSIT'
        assert course.course_name == 'Bachelor of Science in Information Technology'
        assert course.description == 'Updated description'
        activity = ActivityLog.query.filter_by(entity_type='Course', action='Updated').one()
        assert activity.entity_label == 'BSIT - Bachelor of Science in Information Technology'


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

    response = client.get('/students?q=Lina+Martinez')
    assert response.status_code == 200
    assert b'Lina Martinez' in response.data
    assert b'Kai Santos' not in response.data

    response = client.get('/students?status=Inactive')
    assert response.status_code == 200
    assert b'Kai' in response.data
    assert b'Lina' not in response.data


def test_student_removal_requires_a_reason(app, client):
    with app.app_context():
        user = User(username='remover', email='remover@example.com', password_hash=generate_password_hash('secret123'))
        course = Course(course_code='REMOVE101', course_name='Removal Test Course')
        db.session.add_all([user, course])
        db.session.commit()
        student = Student(
            student_id='STU-DEL-001',
            first_name='Taylor',
            last_name='Jordan',
            email='taylor.jordan@example.com',
            phone='09111111111',
            date_of_birth=date(2003, 11, 20),
            course_id=course.id,
            year_level='2nd Year',
            enrollment_status='Active',
        )
        db.session.add(student)
        db.session.commit()
        student_id = student.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    page = client.get('/students')
    assert page.status_code == 200
    assert f'id="delete-student-{student_id}"'.encode() in page.data
    assert f'data-modal-open="delete-student-{student_id}"'.encode() in page.data
    assert b'Are you sure you want to remove this student?' in page.data
    assert b'Please explain why you are removing this record.' in page.data
    assert b'name="reason"' in page.data
    assert b'required' in page.data

    response = client.post(f'/students/{student_id}/delete', data={'reason': '  '}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Enter a reason of 5 to 500 characters' in response.data
    with app.app_context():
        assert db.session.get(Student, student_id) is not None

    response = client.post(
        f'/students/{student_id}/delete',
        data={'reason': 'Duplicate student record'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Student deleted successfully.' in response.data
    with app.app_context():
        assert db.session.get(Student, student_id) is None
        activity = ActivityLog.query.filter_by(entity_type='Student', action='Removed').one()
        assert activity.entity_label == 'Taylor Jordan (STU-DEL-001)'
        assert activity.details == 'Reason: Duplicate student record'

    activity_page = client.get('/activity-logs')
    assert activity_page.status_code == 200
    assert b'Duplicate student record' in activity_page.data


def test_course_removal_requires_a_reason_and_preserves_enrolled_students(app, client):
    with app.app_context():
        user = User(username='course_remover', email='course-remover@example.com', password_hash=generate_password_hash('secret123'))
        course = Course(course_code='COURSE-DEL', course_name='Course Removal Test')
        db.session.add_all([user, course])
        db.session.commit()
        student = Student(
            student_id='STU-COURSE-DEL',
            first_name='Casey',
            last_name='Taylor',
            email='casey.taylor@example.com',
            phone='09111111111',
            date_of_birth=date(2003, 11, 20),
            course_id=course.id,
            year_level='2nd Year',
            enrollment_status='Active',
        )
        db.session.add(student)
        db.session.commit()
        course_id = course.id
        student_id = student.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    page = client.get('/courses')
    assert page.status_code == 200
    assert f'data-modal-open="delete-course-{course_id}"'.encode() in page.data
    assert f'id="delete-course-{course_id}"'.encode() in page.data
    assert b'Are you sure you want to remove this course?' in page.data
    assert b'name="reason"' in page.data
    assert b'Reassign those students before removing the course' in page.data
    assert b'<button type="submit" class="btn-primary delete-confirm-button" disabled>' in page.data

    response = client.post(
        f'/courses/{course_id}/delete',
        data={'reason': 'No longer offered'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Cannot delete a course with assigned students.' in response.data
    with app.app_context():
        assert db.session.get(Course, course_id) is not None
        assert db.session.get(Student, student_id) is not None


def test_course_without_students_requires_removal_reason(app, client):
    with app.app_context():
        user = User(username='course_admin', email='course-admin@example.com', password_hash=generate_password_hash('secret123'))
        course = Course(course_code='EMPTY-COURSE', course_name='Empty Course')
        db.session.add_all([user, course])
        db.session.commit()
        course_id = course.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True

    response = client.post(f'/courses/{course_id}/delete', data={'reason': '  '}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Enter a reason of 5 to 500 characters before removing this course.' in response.data
    with app.app_context():
        assert db.session.get(Course, course_id) is not None

    response = client.post(
        f'/courses/{course_id}/delete',
        data={'reason': 'Course no longer offered'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Course deleted successfully.' in response.data
    with app.app_context():
        assert db.session.get(Course, course_id) is None
