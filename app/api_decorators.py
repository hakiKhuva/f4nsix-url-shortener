from functools import wraps
from flask import request

from .db import User,APIRequest, db
from .api_functions import generate_secure_string


def api_key_required(f):
    """
    API key must be required in a header if a function wraps using this decorator.
    """
    @wraps(f)
    def fun(*args, **kwargs):
        """
        wraps the function and check the
        """
        if request.headers.get("x-api-key"):
            api_user = User.query.filter(User.api_key == generate_secure_string(request.headers["x-api-key"])).first()

            if api_user is not None:
                kwargs["current_user"] = api_user
                return f(*args, **kwargs)

        return {
            "status": "error",
            "message": "API key could not be found in request or provided key is invalid!"
        }, 401

    return fun



def save_api_requests(f):
    @wraps(f)
    def fun(*args, **kwargs):
        response = f(*args, **kwargs)
        current_user = kwargs['current_user']
        db.session.add(APIRequest(
            request_url=request.url_rule.rule,
            return_code=response[1],
            user_id=current_user.id
        ))
        db.session.commit()
        return response
    return fun