from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Optional
from wtforms.fields import EmailField, PasswordField, StringField

from .functions import strip_value


class AdminLoginForm(FlaskForm):
    email_address = EmailField(
        "Email address",
        validators=[DataRequired("Email address is required!"), Length(max=200, message="Email address length must be less than 200!")],
        filters=[strip_value]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired('Password is required!'), Length(min=6, max=32, message="Password length must be between 6 to 32!"),],
        filters=[strip_value]
    )


class AdminEditForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[Length(max=64, message="Name value must be less than 64!")],
        filters=[strip_value]
    )

    email_address = EmailField(
        "Email address",
        validators=[DataRequired("Email address is required!"), Length(max=200, message="Email address length must be less than 200!")],
        filters=[strip_value]
    )

    new_password = PasswordField(
        "New Password",
        validators=[Optional(),Length(min=6, max=32, message="Password length must be between 6 to 32!"),],
        filters=[strip_value]
    )