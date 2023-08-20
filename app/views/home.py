from flask import Blueprint, request, redirect, url_for, session, flash, send_file
from user_agents import parse
from urllib.parse import urlparse

from ..functions import modified_render_template, get_user_ip_address, get_geo_data
from ..forms.home import ShortenLinkForm
from ..db import ShortenLink, db, ShortenLinkTransaction
from ..config import AppConfig
from ..core_functions import generate_shorten_link, check_domain_for_banned, build_shorten_url_for
from ..limiter import limit

import json
import datetime
import qrcode
import io


home = Blueprint("Home", __name__)

@home.route('/')
@limit(datetime.timedelta(minutes=1), limit=30)
def index():
    return modified_render_template(
        "home/index.html"
    )


@home.route("/shorten", methods=["GET", "POST"])
@limit(datetime.timedelta(minutes=1), 20)
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
            
            if check_domain_for_banned(url) is True:
                return redirect(url_for('.shorten_url', error="Entered domain is blocked!", url=url))
            
            response_data = generate_shorten_link(url)
            full_shorten_url = response_data["shorten_url"]
            tracking_id = response_data["tracking_id"]
            
            session.permanent = True
            SESSION_SHORTEN_URLS.insert(0, {
                "to": url,
                "from": full_shorten_url,
                "tracking_id": tracking_id
            })
            session['shorten-urls'] = json.dumps(SESSION_SHORTEN_URLS[:50])
            return redirect(url_for('.shorten_url',id=tracking_id))
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

    if CURRENT_URL is None:
        CURRENT_URL = request.args.get('url')

    form.url.data = CURRENT_URL
    return modified_render_template(
        "home/shorten_url.html",
        page_title="Shorten URL",
        form=form,
        shorten_url=SHORTEN_URL,
        shorten_tracking_id=SHORTEN_TRACKING_ID,
        shorten_urls=SESSION_SHORTEN_URLS
    )


@home.route("/qr-code/<tracking_id>")
@limit(datetime.timedelta(minutes=1), 25)
def qr_code_generator_for_url(tracking_id):
    url = ShortenLink.query.filter(ShortenLink.tracking_id == tracking_id).first_or_404()
    data = qrcode.make(build_shorten_url_for(url.code))
    buffer = io.BytesIO()
    data.save(buffer)
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png", download_name=f'{tracking_id}.png', as_attachment=True)


@home.route('/<shorten_code>')
@limit(datetime.timedelta(minutes=1), 60)
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
    if REQUEST_REFERRER:
        REFERRER = urlparse(REQUEST_REFERRER).netloc

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