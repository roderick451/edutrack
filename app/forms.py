from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, PasswordField, SelectField, DateField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from .models import Course, Student


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Login")


class AdminSettingsForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField("Confirm new password", validators=[Optional(), EqualTo("new_password", message="Passwords do not match.")])
    submit = SubmitField("Save Changes")


class CourseForm(FlaskForm):
    course_code = StringField("Course Code", validators=[DataRequired(), Length(min=2, max=50)])
    course_name = StringField("Course Name", validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save Course")

    def validate_course_code(self, field):
        normalized = field.data.strip()
        existing = Course.query.filter_by(course_code=normalized).first()
        if existing and not getattr(self, "course_id", None):
            raise ValidationError("Course code already exists.")
        if existing and getattr(self, "course_id", None) is not None and existing.id != self.course_id:
            raise ValidationError("Course code already exists.")


class StudentForm(FlaskForm):
    student_id = StringField("Student ID", validators=[DataRequired(), Length(min=3, max=50)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(min=2, max=80)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Phone Number", validators=[DataRequired(), Length(min=7, max=30)])
    date_of_birth = DateField("Date of Birth", validators=[DataRequired()])
    gender = SelectField("Gender", choices=[("", "Select gender"), ("Male", "Male"), ("Female", "Female"), ("Other", "Other")], validators=[Optional()])
    course_id = SelectField("Course", coerce=int, validators=[DataRequired()])
    year_level = SelectField(
        "Year Level",
        choices=[("1st Year", "1st Year"), ("2nd Year", "2nd Year"), ("3rd Year", "3rd Year"), ("4th Year", "4th Year")],
        validators=[DataRequired()],
    )
    enrollment_status = SelectField(
        "Enrollment Status",
        choices=[("Active", "Active"), ("Inactive", "Inactive"), ("Graduated", "Graduated")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Student")

    def validate_student_id(self, field):
        normalized = field.data.strip()
        existing = Student.query.filter_by(student_id=normalized).first()
        if existing and not getattr(self, "student_id_value", None):
            raise ValidationError("Student ID already exists.")
        if existing and getattr(self, "student_id_value", None) is not None and existing.id != self.student_id_value:
            raise ValidationError("Student ID already exists.")

    def validate_email(self, field):
        normalized = field.data.strip().lower()
        existing = Student.query.filter_by(email=normalized).first()
        if existing and not getattr(self, "student_email_value", None):
            raise ValidationError("Student email already exists.")
        if existing and getattr(self, "student_email_value", None) is not None and existing.id != self.student_email_value:
            raise ValidationError("Student email already exists.")
