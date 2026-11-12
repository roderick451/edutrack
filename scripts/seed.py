from datetime import date

from app import create_app, db
from app.models import Course, Student

app = create_app()

with app.app_context():
    if Course.query.count() > 0 or Student.query.count() > 0:
        print('Sample data already exists; skipping seed.')
        raise SystemExit

    courses = [
        Course(course_code='BSIT', course_name='Bachelor of Science in Information Technology', description='Information systems and software development.'),
        Course(course_code='BSE', course_name='Bachelor of Science in Education', description='Teacher education and classroom leadership.'),
        Course(course_code='BSBA', course_name='Bachelor of Science in Business Administration', description='Business, finance, and management disciplines.'),
    ]
    db.session.add_all(courses)
    db.session.commit()

    students = [
        Student(student_id='STU-1001', first_name='Ariana', last_name='Lopez', email='ariana.lopez@example.com', phone='09171234567', date_of_birth=date(2002, 5, 12), gender='Female', course_id=courses[0].id, year_level='1st Year', enrollment_status='Active'),
        Student(student_id='STU-1002', first_name='Marcus', last_name='Brown', email='marcus.brown@example.com', phone='09182345678', date_of_birth=date(2001, 9, 22), gender='Male', course_id=courses[0].id, year_level='2nd Year', enrollment_status='Active'),
        Student(student_id='STU-1003', first_name='Sofia', last_name='Nguyen', email='sofia.nguyen@example.com', phone='09293456789', date_of_birth=date(2000, 11, 7), gender='Female', course_id=courses[1].id, year_level='3rd Year', enrollment_status='Active'),
        Student(student_id='STU-1004', first_name='Daniel', last_name='Kim', email='daniel.kim@example.com', phone='09384567890', date_of_birth=date(1999, 1, 14), gender='Male', course_id=courses[2].id, year_level='4th Year', enrollment_status='Graduated'),
    ]
    db.session.add_all(students)
    db.session.commit()
    print('Seeded 3 courses and 4 sample students.')
