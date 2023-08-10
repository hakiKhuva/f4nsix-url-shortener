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



@click.command("rate-limits")
@with_appcontext
def rate_limit_show():
    """show rate limits"""
    from flask import current_app
    from .limiter import limit_data
    import datetime

    def format_time_for_limit(timedelta:datetime.timedelta):
        explain = ""
        if timedelta.days > 0:
            explain += f"{timedelta.days} days "
        if timedelta.seconds > 0:
            seconds = timedelta.seconds
            minutes = 0
            hours = 0
            while seconds > 60:
                seconds -= 60
                minutes += 1
                if minutes > 60:
                    minutes -= 60
                    hours += 1
                
            if hours > 0:
                explain += f"{hours} hours "
            if minutes > 0:
                explain += f"{minutes} minutes "
            if seconds > 0:
                explain += f"{seconds} seconds "
        return explain.strip()

    printable_data = []
    largest_ljust = 0

    for item in limit_data:
        found = False
        for rule in current_app.url_map.iter_rules():
            rule_function_wrapped = current_app.view_functions[rule.endpoint]
            while 1:
                if rule_function_wrapped.__dict__.get('__wrapped__') is None:
                    break
                rule_function_wrapped = rule_function_wrapped.__dict__.get('__wrapped__')
            item_function_wrapped = item['func']
            while 1:
                if item_function_wrapped.__dict__.get('__wrapped__') is None:
                    break
                item_function_wrapped = item_function_wrapped.__dict__.get('__wrapped__')

            if item_function_wrapped == rule_function_wrapped:
                current_just = len(f'{str(rule.endpoint).replace("."," -> ")}({rule.rule})')+20
                if current_just > largest_ljust:
                    largest_ljust = current_just
                
                printable_data.append([
                    f'{str(rule.endpoint).replace("."," -> ")}({rule.rule})',
                    f"{item['limit']} per {format_time_for_limit(item['time'])}"
                ])
                found = True
                break
        
        if found is False:
            printable_data.append([
                f'function name: {item["func"].__name__}',
                f"{item['limit']} per {format_time_for_limit(item['time'])}"
            ])
    
    print("="*(largest_ljust+30))
    print("Rate limits for current app")
    print("="*(largest_ljust+30))
    printable_data.sort()
    index = 1
    for printable_item in printable_data:
        print(f"[{index}] {printable_item[0]}".ljust(largest_ljust), printable_item[1])
        print("-"*(largest_ljust+30))
        index += 1