from flask import Blueprint, request, url_for, flash, abort
from sqlalchemy import func, Date

from ..db import ShortenLink, ShortenLinkTransaction
from ..config import BaseConfig, AppConfig
from ..functions import modified_render_template
from ..limiter import limit

import datetime
import pygal
import urllib.parse


track = Blueprint("Track", __name__, url_prefix='/track')

@track.route('/')
@limit(datetime.timedelta(minutes=1), 20)
def index():
    tracking_id = request.args.get('id')
    
    tracking_data = {}
    if tracking_id is not None:
        tracking_id = tracking_id.strip().upper()
        shorten_link = ShortenLink.query.filter(ShortenLink.tracking_id == tracking_id).first()

        if shorten_link is not None:
            tracking_data['shorten-link'] = url_for('Home.redirector', shorten_code=shorten_link.code, _external=True, _scheme=AppConfig.HTTP_SCHEME)
            tracking_data['link-destination'] = shorten_link.destination
            tracking_data['link-created-date'] = shorten_link.created_date
            tracking_data['clicks'] = ShortenLinkTransaction.query.with_entities(func.count(ShortenLinkTransaction.id)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id).first()
            if tracking_data['clicks'] is not None:
                tracking_data['clicks'] = tracking_data['clicks'][0]
            else:
                tracking_data['clicks'] = 0
            tracking_data['devices'] = list([c[0], c[1]] for c in ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.device, func.count(ShortenLinkTransaction.id)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id).group_by(ShortenLinkTransaction.device).order_by(func.count(ShortenLinkTransaction.device).desc()).limit(10).all())
            tracking_data['browsers'] = list([c[0], c[1]] for c in ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.browser, func.count(ShortenLinkTransaction.id)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id).group_by(ShortenLinkTransaction.browser).order_by(func.count(ShortenLinkTransaction.browser).desc()).limit(10).all())
            tracking_data['operating-systems'] = list([c[0], c[1]] for c in ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.os, func.count(ShortenLinkTransaction.id)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id).group_by(ShortenLinkTransaction.os).order_by(func.count(ShortenLinkTransaction.os).desc()).limit(10).all())
            tracking_data['top-referrers'] = list([c[0], c[1]] for c in ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.referrer, func.count(ShortenLinkTransaction.id)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id, ShortenLinkTransaction.referrer != None).group_by(ShortenLinkTransaction.referrer).order_by(func.count(ShortenLinkTransaction.referrer).desc()).limit(10).all())
            tracking_data['countries'] = list(
                [BaseConfig.COUNTRIES_DATA.get(c[0], "Other"), c[1]] \
                for c in ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.country, func.count(ShortenLinkTransaction.country)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id).group_by(ShortenLinkTransaction.country).order_by(func.count(ShortenLinkTransaction.country).desc()).all()
            )

            tracking_data['last-seven-days-clicks'] = {}    
            today_utc_date = datetime.datetime.utcnow().date()
            for ikh in range(7):
                current_date_running = today_utc_date - datetime.timedelta(days=ikh)
                data = ShortenLinkTransaction.query.with_entities(func.count(ShortenLinkTransaction.id)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id, ShortenLinkTransaction.created_date.cast(Date) == current_date_running).group_by(ShortenLinkTransaction.created_date).first()
                if data is None:
                    data = 0
                else:
                    data = data[0]
                tracking_data['last-seven-days-clicks'][current_date_running.strftime('%Y-%m-%d')] = data
            
            tracking_data['datetime-clicks'] = {}
            temp_t = datetime.datetime.utcnow()
            if temp_t.minute < 30:
                time_now = datetime.datetime(temp_t.year, temp_t.month, temp_t.day, temp_t.hour, 30, 0)
            else:
                time_now = datetime.datetime(temp_t.year, temp_t.month, temp_t.day, temp_t.hour+1, 0, 0)

            for ikh in range(24):
                time_delta = datetime.timedelta(hours=ikh)
                from_ = time_now-time_delta-datetime.timedelta(hours=1)
                to_ = time_now-time_delta
                data = ShortenLinkTransaction.query.with_entities(func.count(ShortenLinkTransaction.id)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id, ShortenLinkTransaction.created_date.between(from_, to_)).group_by(ShortenLinkTransaction.created_date).first()
                if data is None:
                    data = 0
                else:
                    data = data[0]
                tracking_data["datetime-clicks"][f"{from_.strftime('%H:%M')} - {to_.strftime('%H:%M')}"] = data

        else:
            flash("Entered tracking id could not be found!")

    return modified_render_template(
        "track/index.html",
        page_title="Track ID",
        page_description="Track the clicks of the shorten URL with tracking ID",
        tracking_data=tracking_data,
        tracking_id=tracking_id,
        grid_data_to_display=["browsers", "devices", "operating-systems", "top-referrers"]
    )


@track.route('/<tracking_id>/image')
@limit(datetime.timedelta(minutes=1), 25)
def image_for_shorten(tracking_id):
    if(request.host != urllib.parse.urlparse(request.referrer).netloc):
        abort(400)

    shorten_link = ShortenLink.query.filter(ShortenLink.tracking_id == tracking_id).first_or_404()
    temp_coutries_data = ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.country, func.count(ShortenLinkTransaction.country)).filter(ShortenLinkTransaction.shorten_link_id == shorten_link.id, ShortenLinkTransaction.country != None).group_by(ShortenLinkTransaction.country).all()
    main_countries_data = {}
    for c in temp_coutries_data:
        main_countries_data[c[0].lower()] = c[1]

    worldmap =  pygal.maps.world.World()
    worldmap.add("Country",main_countries_data)
    worldmap.config.height = 350
    worldmap.config.show_legend = False
    return worldmap.render_data_uri()
