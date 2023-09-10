from flask_wtf import FlaskForm
from wtforms.fields import URLField
from wtforms.validators import URL, DataRequired, Length
from .functions import strip_value
from ..config import BaseConfig


class ShortenLinkForm(FlaskForm):
    url = URLField(
        "Full URL",
        validators=[DataRequired(message="URL is required to shorten!"), Length(max=BaseConfig.LONG_URL_MAX_LIMIT, message="URL length must be less than {} letters!".format(BaseConfig.LONG_URL_MAX_LIMIT)), URL(message="Enter a valid URL!")],
        filters=[strip_value]
    )
