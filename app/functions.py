from flask import render_template as original_render_template, current_app, request, session
import datetime
import requests

from .config import AppConfig, BaseConfig


def modified_render_template(*args,**kwargs):
    """
    Modified version of render template, default arguments are added here.
    """
    kwargs['app_name'] = current_app.config['APP_NAME']
    kwargs['app_short_description'] = AppConfig.APP_SHORT_DESCRIPTION
    kwargs['app_debug'] = AppConfig.DEBUG
    if not kwargs.get('page_title'):
        kwargs['page_title'] = current_app.config['APP_NAME']+" - "+current_app.config['APP_SHORT_DESCRIPTION']
    if not kwargs.get('page_description'):
        kwargs['page_description'] = current_app.config['APP_DESCRIPTION']
    kwargs['format_number'] = format_number
    kwargs['GITHUB_URL'] = AppConfig.GITHUB_URL
    kwargs['TWITTER_URL'] = AppConfig.TWITTER_URL
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