from flask import Blueprint, request, jsonify
from sqlalchemy import func, Date
from flask_cors import cross_origin

from ..config import AppConfig, BaseConfig
from ..api_decorators import api_key_required, save_api_requests
from ..functions import modified_render_template, get_date, url_for_external
from ..core_functions import generate_shorten_link, build_shorten_url_for, check_domain_for_banned
from ..db import ShortenLink, ShortenLinkTransaction, db
from ..limiter import limit

import markdown
import math
import validators
import datetime


api = Blueprint("API", __name__, url_prefix="/api")


@api.route("/docs")
@limit(datetime.timedelta(seconds=60), 30)
def api_docs():
    rendered_md = markdown.markdown(
        modified_render_template(
            "api/docs.md",
            url_for=url_for_external,
        ),
        extensions=['tables', 'fenced_code']
    )
    return modified_render_template(
        "api/index.html",
        page_title=f"{AppConfig.APP_NAME} URL shortener API docs",
        page_description=f"Create and manage shorten URLs using the {AppConfig.APP_NAME} URL shortener API. Shorten the URL and track the clicks, referrers, devices and countries info of shorten URL using the API.",
        rendered_data=rendered_md
    )


@api.route('/shorten', methods=["POST"])
@limit(datetime.timedelta(seconds=60), 30, response_body={ "status": "error", "message": "Too many requests!" })
@cross_origin()
@api_key_required
@save_api_requests
def shorten_url(current_user):
    url = request.args.get("url", request.form.get("url"))
    if request.is_json is True and url is None:
        url = request.json.get('url')
    
    try:
        is_valid = validators.url(url,)
    except validators.ValidationFailure:
        is_valid = False
    except ValueError:
        is_valid = False
    except TypeError:
        is_valid = False

    if is_valid is True:
        if len(url) > BaseConfig.LONG_URL_MAX_LIMIT:
            return jsonify({
                "status": "error",
                "message": "URL length must be less than {} letters!".format(BaseConfig.LONG_URL_MAX_LIMIT)
            }), 400

        if check_domain_for_banned(url) is True:
            return jsonify({
                "status": "error",
                "message": "The entered domain is blocked!"
            }), 400

        _shorten_url_in_db = ShortenLink.query.filter(ShortenLink.destination == url, ShortenLink.user_id == current_user.id).first()
        
        if _shorten_url_in_db is None:
            total_links_by_user = ShortenLink.query.with_entities(func.count(ShortenLink.id)).filter(ShortenLink.user_id == current_user.id).first()
            if total_links_by_user is not None and total_links_by_user[0] >= BaseConfig.USER_LIMIT_FOR_SHORTEN_LINKS:
                return jsonify({
                    "status": "error",
                    "message": "User is reached to limit for creating the shorten url!"
                }), 400

            function_response = generate_shorten_link(url, current_user=current_user)
            return jsonify({
                "status": "ok",
                "data": {
                    "code": function_response["shorten_code"],
                    "shorten_url": function_response["shorten_url"],
                    "tracking_id": function_response["tracking_id"],
                }
            }), 200

        else:
            return jsonify({
                "status": "ok",
                "data": {
                    "code": _shorten_url_in_db.code,
                    "shorten_url": build_shorten_url_for(_shorten_url_in_db.code),
                    "tracking_id": _shorten_url_in_db.tracking_id,
                }
            }), 200

    return jsonify({
            "status": "error",
            "message": "URL to be shorten is missing or invalid!"
        }), 400


@api.route("/urls")
@limit(datetime.timedelta(seconds=60), 30, response_body={ "status": "error", "message": "Too many requests!" })
@cross_origin()
@api_key_required
@save_api_requests
def all_urls(current_user):
    current_page = request.args.get("page", "1")
    if current_page.isnumeric() is True:
        current_page = int(current_page)
        if current_page > math.ceil(BaseConfig.USER_LIMIT_FOR_SHORTEN_LINKS/10):
            return jsonify({
                "status": "error",
                "message": "The page number is more than {}!".format(math.ceil(BaseConfig.USER_LIMIT_FOR_SHORTEN_LINKS/10))
            }), 400
    else:
        return jsonify({
            "status": "error",
            "message": "Page parameter must be an Integer value!"
        }), 400

    count_of_urls = ShortenLink.query.with_entities(func.count(ShortenLink.id)).filter(ShortenLink.user_id == current_user.id).first()
    count_of_urls = 0 if count_of_urls is None else count_of_urls[0]
    total_pages = math.ceil(count_of_urls/10)
    if count_of_urls > 0 and current_page <= total_pages:
        paginate = ShortenLink.query.filter(ShortenLink.user_id == current_user.id).paginate(page=current_page, per_page=10)
    else:
        paginate = []
     
    data = []
    for link in paginate:
        data.append({
            "tracking_id": link.tracking_id,
            "shorten_url": build_shorten_url_for(link.code),
            "destination": link.destination
        })

    return jsonify({
        "status" : "ok",
        "total_links": count_of_urls,
        "pages": total_pages,
        "current_page": current_page,
        "data": data
    }), 200


@api.route("/track/<tracking_id>", methods=["GET", "DELETE"])
@limit(datetime.timedelta(seconds=60), 10, response_body={ "status": "error", "message": "Too many requests!" })
@cross_origin()
@api_key_required
@save_api_requests
def track_or_delete_the_url(current_user, tracking_id):
    if len(tracking_id) > BaseConfig.TRACKING_ID_MAX_LIMIT:
        return jsonify({
            "status": "error",
            "message": "Tracking id length must be less than or equal to {}!".format(BaseConfig.TRACKING_ID_MAX_LIMIT)
        }), 400

    shorten_link_in_db = ShortenLink.query.filter(ShortenLink.tracking_id == tracking_id, ShortenLink.user_id == current_user.id).first()
    if shorten_link_in_db is None:
        return jsonify({
            "status": "error",
            "message": "Tracking id could not be found!"
        }), 404

    if request.method == "GET":
        clicks = ShortenLinkTransaction.query.with_entities(func.count(ShortenLinkTransaction.id)).filter(
            ShortenLinkTransaction.shorten_link_id == shorten_link_in_db.id,
        ).first()[0]

        countries = {x[0]: x[1] for x in ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.country, func.count(ShortenLinkTransaction.country)).filter(
            ShortenLinkTransaction.shorten_link_id == shorten_link_in_db.id
        ).group_by(ShortenLinkTransaction.country).all()}
        if None in countries.keys():
            countries.pop(None, "")

        referrers = {x[0] : x[1] for x in ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.referrer, func.count(ShortenLinkTransaction.referrer)).filter(
            ShortenLinkTransaction.shorten_link_id == shorten_link_in_db.id
        ).group_by(ShortenLinkTransaction.referrer).limit(10).all()}
        if None in referrers.keys():
            referrers.pop(None,"")

        last_seven_days_clicking_data = []
        today = get_date()
        for ikh in range(7):
            date_curr = today - datetime.timedelta(days=ikh)
            
            counts = ShortenLinkTransaction.query.with_entities(
                func.count(ShortenLinkTransaction.id)
            ).filter(
                ShortenLinkTransaction.shorten_link_id == shorten_link_in_db.id,
                ShortenLinkTransaction.created_date.cast(Date) == date_curr,
            ).group_by(ShortenLinkTransaction.created_date.cast(Date)).first()
            counts = counts[0] if counts is not None else 0

            last_seven_days_clicking_data.append({
                "date": date_curr.isoformat(),
                "clicks": counts,
            })
        
        return jsonify({
            "status": "ok",
            "shorten_link": build_shorten_url_for(shorten_link_in_db.code),
            "destination": shorten_link_in_db.destination,
            "date": shorten_link_in_db.created_date.isoformat(),
            "data": {
                "clicks": clicks,
                "countries": countries,
                "referrers": referrers,
                "seven_days_clicks": last_seven_days_clicking_data,
            }
        }), 200
    else:
        shorten_url = build_shorten_url_for(shorten_link_in_db.code)
        destination = shorten_link_in_db.destination
        db.session.delete(shorten_link_in_db)
        db.session.commit()

        return jsonify({
            "status": "ok",
            "shorten_url": shorten_url,
            "destination": destination
        }), 200