from flask import Blueprint, session, redirect, url_for, request, flash
from sqlalchemy import func, Date

from ..functions import modified_render_template, get_current_loggedin_user, generate_string, get_date
from ..api_functions import generate_secure_string
from ..decorators import account_login_required
from ..forms.account import EditAccountForm, DeleteAccountForm
from ..forms.universal import UniversalCsrfForm
from ..db import db, APIRequest
from ..limiter import limit

import datetime


account = Blueprint("Account", __name__, url_prefix="/account")


@account.route("/", methods=["GET", "POST"])
@limit(datetime.timedelta(minutes=1), 20)
@account_login_required
def index():
    form = EditAccountForm({})
    current_user = get_current_loggedin_user()

    if request.method == "POST":
        form = EditAccountForm(request.form)

        if form.validate_on_submit() is True:
            name = form.name.data
            promotional_emails = form.promotional_emails.data

            current_user.name = name
            current_user.receive_emails = promotional_emails
            db.session.commit()

            flash("Your account was updated successfully.")
        else:
            for errors in form.errors.values():
                for error in errors:
                    flash(error)

        return redirect(url_for(".index"))

    form.name.data = current_user.name
    form.email_address.data = current_user.email_address
    form.username.data = current_user.username
    form.promotional_emails.data = current_user.receive_emails

    return modified_render_template(
        "account/index.html",
        page_title="Your account",
        current_user=current_user,
        form=form
    )


@account.route("/api-dashboard", methods=["GET","POST"])
@limit(datetime.timedelta(minutes=1), 15)
@account_login_required
def api_dashboard():
    form = UniversalCsrfForm({})
    current_user = get_current_loggedin_user()

    if request.method == "POST":
        form = UniversalCsrfForm(request.form)

        if form.validate_on_submit() is True:
            if current_user.api_key_created is not None:
                if current_user.api_key_created == get_date():
                    flash("You've already generated api key today, tryagain tomorrow.")
                    return redirect(url_for(".api_dashboard"))

            USER_API_KEY = generate_string(32)
            current_user.api_key = generate_secure_string(USER_API_KEY)
            current_user.api_key_created = get_date()

            session['current-user-api-key'] = USER_API_KEY
            db.session.commit()
        else:
            flash("Something went wrong, tryagain soon!")
        return redirect(url_for(".api_dashboard"))

    if current_user.api_key_created is None:
        is_api_key_generated = False
    else:
        is_api_key_generated = True

    can_generate_new_api_key = False
    if current_user.api_key_created is not None:
        if current_user.api_key_created < get_date():
            can_generate_new_api_key = True
    else:
        can_generate_new_api_key = True


    # fetching api requests data
    current_time = datetime.datetime.utcnow()
    if current_time.minute < 30:
        current_time = datetime.datetime(current_time.year, current_time.month, current_time.day, current_time.hour, 30)
    else:
        current_time = datetime.datetime(current_time.year, current_time.month, current_time.day, current_time.hour+1, 0)
    
    success_api_requests_data_for_24h = {}
    failed_api_requests_data_for_24h = {}
    for i in range(24):
        timedelta_ = datetime.timedelta(hours=i)
        left = current_time - timedelta_ - datetime.timedelta(hours=1)
        right = current_time - timedelta_

        data = APIRequest.query.with_entities(func.count(APIRequest.id)).filter(APIRequest.created_date.between(left, right), APIRequest.user_id == current_user.id, APIRequest.return_code == 200).first()
        reqs = data[0] if data is not None else 0
        success_api_requests_data_for_24h[left.strftime('%H:%M')+"-"+right.strftime('%H:%M')] = reqs

        data = APIRequest.query.with_entities(func.count(APIRequest.id)).filter(APIRequest.created_date.between(left, right), APIRequest.user_id == current_user.id, APIRequest.return_code != 200).first()
        reqs = data[0] if data is not None else 0
        failed_api_requests_data_for_24h[left.strftime('%H:%M')+"-"+right.strftime('%H:%M')] = reqs
    
    total_requests_count = APIRequest.query.with_entities(func.count(APIRequest.id)).filter(APIRequest.user_id == current_user.id).first()[0]
    successful_requests_count = APIRequest.query.with_entities(func.count(APIRequest.id)).filter(APIRequest.user_id == current_user.id, APIRequest.return_code == 200).first()[0]
    failed_requests_count = APIRequest.query.with_entities(func.count(APIRequest.id)).filter(APIRequest.user_id == current_user.id, APIRequest.return_code != 200).first()[0]

    today_requests_count = APIRequest.query.with_entities(func.count(APIRequest.id)).filter(APIRequest.user_id == current_user.id, APIRequest.created_date.cast(Date) == get_date()).first()[0]

    routes_requests_data = APIRequest.query.with_entities(APIRequest.request_url, func.count(APIRequest.id)).filter(APIRequest.user_id == current_user.id).group_by(APIRequest.request_url).order_by(func.count(APIRequest.id)).all()

    return modified_render_template(
        "account/api_dashboard.html",
        page_title="API Dashboard",
        current_user=current_user,
        is_api_key_generated=is_api_key_generated,
        can_generate_new_api_key=can_generate_new_api_key,
        form=form,
        api_requests_data_for_24h={
            "failed": failed_api_requests_data_for_24h,
            "successful": success_api_requests_data_for_24h,
        },
        total_requests_count=total_requests_count,
        successful_requests_count=successful_requests_count,
        failed_requests_count=failed_requests_count,
        today_requests_count=today_requests_count,
        routes_requests_data=routes_requests_data
    )


@account.route("/delete-account", methods=["GET", "POST"])
@limit(datetime.timedelta(minutes=1), 20)
@account_login_required
def delete_account():
    current_user = get_current_loggedin_user()
    form = DeleteAccountForm({})
    
    if request.method == "POST":
        form = DeleteAccountForm(request.form)
        if form.validate_on_submit() is True:
            username = form.username.data
            agreed = form.agreed.data

            if agreed is not True:
                flash("Checkbox in the form must be checked to delete your account!")
                return redirect(url_for(".delete_account"))
            
            if current_user.username != username:
                flash("Entered username does not matched with your account, tryagain later!")
                return redirect(url_for(".delete_account"))

            db.session.delete(current_user)
            db.session.commit()
            
            flash("Successfully deleted your account.")
            return redirect(url_for("Home.index"))
        else:
            for errors in form.errors.values():
                for error in errors:
                    flash(error)

        return redirect(url_for(".delete_account"))

    return modified_render_template(
        "account/delete_account.html",
        page_title="Delete account",
        current_user=current_user,
        form=form
    )


@account.route("/logout", methods=["POST"])
@limit(datetime.timedelta(minutes=1), 20)
@account_login_required
def logout_user():
    session.pop("github_oauth_token", "")
    return redirect(url_for("Auth.index"))
