from flask import Blueprint

from ..functions import modified_render_template
from ..limiter import limit

import markdown
import datetime


legal = Blueprint("Legal", __name__, url_prefix='/legal')


@legal.route('/terms-of-service')
@limit(datetime.timedelta(minutes=1), 30)
def terms_of_service():
    terms_of_service_render_data = markdown.markdown(
        modified_render_template(
            "legal/terms_of_service.md"
        )
    )
    return modified_render_template(
        "legal/base.html",
        page_title="Terms of service",
        render_data=terms_of_service_render_data,
    )


@legal.route('/privacy-policy')
@limit(datetime.timedelta(minutes=1), 30)
def privacy_policy():
    privacy_policy_render_data = markdown.markdown(
        modified_render_template(
            "legal/privacy_policy.md"
        )
    )
    return modified_render_template(
        "legal/base.html",
        page_title="Privacy policy",
        render_data=privacy_policy_render_data
    )