from flask import Blueprint, session, redirect, url_for, flash
from flask_dance.contrib.github import make_github_blueprint
from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.github import github

from ..config import AuthConfig
from ..functions import modified_render_template, is_user_loggedin
from ..db import User, UserSession, db
from ..limiter import limit

import uuid
import datetime
import random


auth = Blueprint("Auth", __name__, url_prefix="/auth")


@auth.before_request
@limit(datetime.timedelta(seconds=60), 10)
def before_auth_request():
    if is_user_loggedin() is True:
        return redirect(url_for("Account.index"))


@auth.route("/")
def index():
    return modified_render_template(
        "auth/index.html",
        page_title="Log into your account",
    )


github_blueprint = make_github_blueprint(
    client_id=AuthConfig.GitHubConfig.CLIENT_ID,
    client_secret=AuthConfig.GitHubConfig.CLIENT_SECRET,
    scope='read:user,user:email',
)


@oauth_authorized.connect
def create_new_account_if_not_exists(blueprint, token):
    user_json = github.get('/user').json()
    user_emails = github.get('/user/emails').json()    

    if len(user_emails) < 1:
        flash("Something went wrong, tryagain later!")
        return redirect(url_for("Account.logout"))

    if not user_emails[0]["verified"]:
        flash("Account email address is not verified, please verify the email address and tryagain.")
        return redirect(url_for("Account.logout"))

    auth_method = "github"

    user_email_address = user_emails[0]["email"]
    user_name = user_json["name"]
    user_uname = user_json["login"]
    user_profile_image_url = user_json["avatar_url"]

    current_user = User.query.filter(User.email_address == user_emails[0]["email"], User.auth_method == auth_method).first()
    if current_user is None:
        new_user = User(
            name = user_name,
            username = user_uname,
            email_address = user_email_address,
            avatar_url = user_profile_image_url,
            auth_method=auth_method,
        )
        db.session.add(new_user)
        db.session.commit()
        current_user = new_user
    else:
        if current_user.name != user_name:
            current_user.name = user_name
        if current_user.username != user_uname:
            current_user.username = user_uname
        if current_user.avatar_url != user_profile_image_url:
            current_user.avatar_url = user_profile_image_url
        
    new_session = UserSession(
        session_id = uuid.uuid4().hex+datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")+str(random.randint(1111111111,9999999999)),
        user_id=current_user.id
    )
    db.session.add(new_session)
    db.session.commit()

    blueprint.token = token
    session["auth-session-id"] = new_session.session_id
    session["auth-session-method"] = current_user.auth_method
    return redirect(url_for("Account.index"))


auth.register_blueprint(github_blueprint)