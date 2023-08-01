from flask import Blueprint, request, redirect, url_for, session, flash
from user_agents import parse
from urllib.parse import urlparse

from ..functions import modified_render_template, get_user_ip_address, get_geo_data
from ..forms.home import ShortenLinkForm
from ..db import ShortenLink, db, ShortenLinkTransaction
from ..config import AppConfig

import string
import random
import json


home = Blueprint("Home", __name__)

@home.route('/')
def index():
    return modified_render_template(
        "home/index.html"
    )


@home.route("/shorten", methods=["GET", "POST"])
def shorten_url():
    form = ShortenLinkForm({})
    SESSION_SHORTEN_URLS = json.loads(session.get('shorten-urls',"[]"))

    if request.method == "POST":
        form = ShortenLinkForm(request.form)

        if form.validate_on_submit() is True:
            url = form.url.data

            for item in SESSION_SHORTEN_URLS:
                if item['to'] == url:
                    return redirect(url_for('.shorten_url',id=item['tracking_id']))

            shorten_code = "".join(random.choice(string.ascii_letters+string.digits) for _ in range(random.randint(3, 6)))
            while ShortenLink.query.filter(ShortenLink.code == shorten_code).count() > 0:
                shorten_code = "".join(random.choice(string.ascii_letters+string.digits) for _ in range(random.randint(3, 8)))

            shorten_link = ShortenLink(
                destination=url,
                code=shorten_code
            )
            db.session.add(shorten_link)
            db.session.commit()

            full_shorten_url = url_for("Home.redirector", shorten_code=shorten_code, _external=True, _scheme=AppConfig.HTTP_SCHEME)
            
            session.permanent = True
            SESSION_SHORTEN_URLS.insert(0, {
                "to": url,
                "from": full_shorten_url,
                "tracking_id": shorten_link.tracking_id
            })
            session['shorten-urls'] = json.dumps(SESSION_SHORTEN_URLS)
            return redirect(url_for('.shorten_url',id=shorten_link.tracking_id))
        else:
            return redirect(url_for('.shorten_url', error=list(form.errors.values())[0]))

    if request.args.get('error'):
        for item in request.args.getlist('error'):
            flash(item)
    
    CURRENT_URL = None
    SHORTEN_URL = None
    SHORTEN_TRACKING_ID = None

    if request.args.get('id'):
        for item in SESSION_SHORTEN_URLS:
            if item['tracking_id'] == request.args['id']:
                CURRENT_URL = item['to']
                SHORTEN_URL = item['from']
                SHORTEN_TRACKING_ID = item['tracking_id']

    form.url.data = CURRENT_URL
    return modified_render_template(
        "home/shorten_url.html",
        page_title="Shorten URL",
        form=form,
        shorten_url=SHORTEN_URL,
        shorten_tracking_id=SHORTEN_TRACKING_ID,
        shorten_urls=SESSION_SHORTEN_URLS
    )


@home.route('/<shorten_code>')
def redirector(shorten_code):
    shorten_link = ShortenLink.query.filter(ShortenLink.code == shorten_code).first_or_404("Shorten link could not be found, re-enter or double check the URL and tryagain later.")

    ua = parse(request.user_agent.string)
    BROWSER = ua.browser.family
    OS = ua.os.family
    if ua.is_bot is True:
        DEVICE = "BOT"
    elif ua.is_tablet is True:
        DEVICE = "TABLET"
    elif ua.is_pc is True:
        DEVICE = "PC"
    elif ua.is_mobile:
        DEVICE = "MOBILE"
    else:
        DEVICE = "OTHER"

    geolocation_data = get_geo_data()

    if OS is None:
        OS = "Unknown"
    if BROWSER is None:
        BROWSER = "Unknown"
    
    REQUEST_REFERRER = request.referrer
    REFERRER = None
    if urlparse(REQUEST_REFERRER).netloc != request.host:
        REFERRER = urlparse(REQUEST_REFERRER).hostname

    transaction = ShortenLinkTransaction(
        device=DEVICE[:64],
        os=OS[:64],
        browser=BROWSER[:64],
        city=geolocation_data.get("city"),
        region=geolocation_data.get("region"),
        country=geolocation_data.get("country"),
        timezone=geolocation_data.get("timezone"),
        ipaddress=get_user_ip_address(),
        shorten_link_id=shorten_link.id,
        referrer=REFERRER
    )

    db.session.add(transaction)
    db.session.commit()

    return redirect(shorten_link.destination, code=302)