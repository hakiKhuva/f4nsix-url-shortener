from flask_wtf import FlaskForm
from wtforms.fields import URLField
from wtforms.validators import URL, DataRequired, Length
from .functions import strip_value


class ShortenLinkForm(FlaskForm):
    url = URLField(
        "Full URL",
        validators=[DataRequired(message="URL is required to shorten!"), Length(max=2048, message="URL length must be less than 2048 letters!"), URL(message="Enter a valid URL!")],
        filters=[strip_value]
    )
