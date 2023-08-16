from flask import render_template as original_render_template, current_app, request, session, url_for
from flask_dance.contrib.github import github
import datetime
import requests
import uuid
import random

from .config import AppConfig, BaseConfig


def modified_render_template(*args,**kwargs):
    """
    Modified version of render template, default arguments are added here.
    """
    from .db import Notification

    kwargs['app_name'] = AppConfig.APP_NAME
    kwargs['app_short_description'] = AppConfig.APP_SHORT_DESCRIPTION
    kwargs['app_debug'] = AppConfig.DEBUG
    kwargs['format_number'] = format_number
    kwargs['auth_status'] = is_user_loggedin()
    kwargs['GITHUB_URL'] = AppConfig.GITHUB_URL
    kwargs['TWITTER_URL'] = AppConfig.TWITTER_URL
    kwargs['LINKEDIN_URL'] = AppConfig.LINKEDIN_URL
    kwargs['GITHUB_TEXT'] = AppConfig.GITHUB_TEXT
    kwargs['TWITTER_TEXT'] = AppConfig.TWITTER_TEXT
    kwargs['TWITTER_USERNAME'] = AppConfig.TWITTER_USERNAME
    kwargs['LINKEDIN_TEXT'] = AppConfig.LINKEDIN_TEXT

    if not kwargs.get('page_title'):
        kwargs['page_title'] = AppConfig.APP_SHORT_DESCRIPTION+" - "+AppConfig.APP_NAME
    if not kwargs.get('page_description'):
        kwargs['page_description'] = AppConfig.APP_DESCRIPTION
    
    kwargs['ALL_NOTIFICATIONS'] = [x.render_data for x in Notification.query.filter(datetime.datetime.utcnow() > Notification.from_ , datetime.datetime.utcnow() < Notification.to).all()]

    return original_render_template(*args,**kwargs)


def get_user_ip_address():
    """returns user ip address"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']
    

def get_date(in_string=False):
    """returns only date in string of date type"""
    if in_string is True:
        return datetime.datetime.utcnow().date().strftime('%Y-%m-%d')
    return datetime.datetime.utcnow().date()


def format_number(num:int):
    """returns formatted number in string"""
    if num >= 1000000:
        n = num/1000000
        m = "M"
    elif num >= 1000:
        n = num/1000
        m = "K"
    else:
        n = num
        m = ""
    
    if type(n) == int:
        return f"{n}{m}"
    return f"{n:.2f}{m}"


def get_geo_data():
    if session.get('user-geo-data') is None or session["user-geo-data"]["date"] != get_date(True):
        if AppConfig.DEBUG is True:
            geolocation_data = BaseConfig.DEBUG_API_DATA
        else:
            req = requests.get(f"https://ipinfo.io/{get_user_ip_address()}?token={BaseConfig.IPINFO_API_TOKEN}")
            if req.status_code == 200:
                geolocation_data = req.json()
            else:
                geolocation_data = {}
        session["user-geo-data"] = {
            "date": get_date(True),
            "data": geolocation_data
        }
    else:
        geolocation_data = session["user-geo-data"]["data"]
    return geolocation_data


def is_user_loggedin():
    from .db import UserSession
    user_session = UserSession.query.filter(UserSession.session_id == session.get("auth-session-id")).first()
    if user_session is not None:
        user = user_session.user
        if user.auth_method == "github":
            return github.authorized
    return False


def get_current_loggedin_user():
    from .db import UserSession
    user_session = UserSession.query.filter(UserSession.session_id == session.get("auth-session-id")).first()
    if user_session is not None:
        user = user_session.user
        return user
    

def generate_string(length=16):
    """
    generate string using uuid, datetime, random numbers
    """
    string_data = ""
    while len(string_data) < length:
        string_data += uuid.uuid4().hex[3:15]+datetime.datetime.utcnow().strftime("%d%H%M%S")+str(random.randint(1111, 99999))
    
    return string_data[:length]


def url_for_external(endpoint, **kwargs):
    """
    returns external url same as url_for, only manages scheme in the url
    """
    return url_for(endpoint, _external=True, _scheme=AppConfig.HTTP_SCHEME, **kwargs)