from flask import url_for
from sqlalchemy import func

from .db import db, ShortenLink
from .config import AppConfig, BaseConfig

import random
import string
import urllib.parse


def build_shorten_url_for(shorten_code: str):
    """
    Build and returns the shorten url using shorten_code
    """
    return url_for("Home.redirector", shorten_code=shorten_code, _external=True, _scheme=AppConfig.HTTP_SCHEME)


def check_domain_for_banned(url:str) -> bool:
    """
    Check the domain is in banned domain or not
    """
    is_banned = False
    f_pointer = open(BaseConfig.BANNED_DOMAIN_FILEPATH, "r")
    current_url_netloc = urllib.parse.urlparse(url).netloc.lower()
    current_url_hostname = urllib.parse.urlparse(url).hostname.lower()
    while True:
        domain = f_pointer.readline().strip()
        if not domain: break
        else: domain = domain.lower()

        if current_url_netloc == domain or current_url_hostname == domain:
            is_banned = True
            break
        elif current_url_netloc.startswith("www.") and current_url_netloc.removeprefix("www.") == domain:
            is_banned = True
            break
        elif current_url_hostname.startswith("www.") and current_url_hostname.removeprefix("www.") == domain:
            is_banned = True
            break
    return is_banned


def generate_shorten_link(url:str, current_user=None) -> dict:
    """
    Generate the shorten code for the link, store it in the Model and returns the data in dictionary.

    args:
        url: url to be shorten
        shortening_method: method that used to shorten("API" or "WEB")
        current_user: if method is API then it is required to pass user

    dictionary object contains shorten code, shorten url and tracking id.
    """
    shorten_code = "".join(random.choice(string.ascii_letters+string.digits) for _ in range(random.randint(3, 6)))

    shorten_code_count = ShortenLink.query.with_entities(func.count(ShortenLink.id)).filter(ShortenLink.code == shorten_code).first()
    if shorten_code_count is not None:
        shorten_code_count = shorten_code_count[0]
    else:
        shorten_code_count = 0

    while shorten_code_count > 0:
        shorten_code = "".join(random.choice(string.ascii_letters+string.digits) for _ in range(random.randint(3, 8)))
        shorten_code_count = ShortenLink.query.with_entities(func.count(ShortenLink.id)).filter(ShortenLink.code == shorten_code).first()
        if shorten_code_count is not None:
            shorten_code_count = shorten_code_count[0]
        else:
            shorten_code_count = 0

    shorten_link = ShortenLink(
        destination = url,
        code = shorten_code,
        user_id = current_user.id if current_user is not None else None
    )
    db.session.add(shorten_link)
    db.session.commit()

    full_shorten_url = build_shorten_url_for(shorten_code)
    return {
        "shorten_code": shorten_code,
        "shorten_url": full_shorten_url,
        "tracking_id": shorten_link.tracking_id
    }