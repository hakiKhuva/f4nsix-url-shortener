from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from .db import AdminUser, db

import click
import getpass
import email_validator
from email_validator.exceptions_types import EmailNotValidError


@click.command("createadminuser")
@with_appcontext
def create_admin_user():
    "create new admin user"
    name = input("Enter your name: ").strip()
    email_address = input("Enter email address: ").strip()

    try:
        email_validator.validate_email(email_address)
    except EmailNotValidError:
        print("Enter a valid email address!")
        return

    password = getpass.getpass("Enter password: ").strip()
    if len(password) < 6 or len(password) > 32:
        print("Password length must be between 6 to 32!")
        return

    db.session.add(AdminUser(
        name=name,
        email_address=email_address,
        password=generate_password_hash(password)
    ))
    db.session.commit()
    print("Admin created successfully.")