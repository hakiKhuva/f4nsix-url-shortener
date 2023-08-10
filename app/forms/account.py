from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, Optional
from wtforms.fields import StringField, BooleanField, EmailField

from .functions import strip_value
from ..config import AppConfig


class EditAccountForm(FlaskForm):
    name = StringField(
        "Your name",
        validators=[DataRequired("Your name is required!"), Length(min=2, max=64, message="Your name length must be from 2 to 64!")],
        filters=[strip_value]
    )

    email_address = EmailField(
        "Email address",
        validators=[Optional()],
        render_kw={
            "readonly": ""
        }
    )

    username = StringField(
        "Username",
        validators=[Optional()],
        render_kw={
            "readonly": ""
        }
    )

    promotional_emails = BooleanField(
        "I want to receive promotional emails from {}.".format(AppConfig.APP_NAME),
    )


class DeleteAccountForm(FlaskForm):
    username = StringField(
        "Type your username",
        validators=[DataRequired("Username is required to delete your account"), Length(max=64)],
        filters=[strip_value],
        render_kw={
            "placeholder": "Your username here"
        }
    )

    agreed = BooleanField(
        "I know after deletion of my account, my user data and all shorten urls will be deleted that created using the API and cannot be restored or reversed.",
        validators=[DataRequired("Checkbox in the form must be checked to delete your account")]
    )