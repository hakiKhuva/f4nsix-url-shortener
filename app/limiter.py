import datetime
from functools import wraps

from flask import request, abort
from sqlalchemy import func
from .db import db, UserVisit
from .functions import get_user_ip_address

limit_data = []

def limit(timedelta_:datetime.timedelta, limit:int, response_body=None):
    def limit_function_getter(route_function):
        limit_data.append({
            "func": route_function,
            "limit": limit,
            "time": timedelta_
        })
        @wraps(route_function)
        def limit_worker(*args, **kwargs):
            current_datetime = datetime.datetime.utcnow()
            left_time = current_datetime-timedelta_
            user_visits_count = UserVisit.query.with_entities(func.count(UserVisit.id)).filter(UserVisit.created_date >= left_time, UserVisit.created_date <= current_datetime, UserVisit.endpoint == request.endpoint, UserVisit.user_ip_address == get_user_ip_address()).first()

            if user_visits_count[0]+1 > limit:
                if response_body is not None:
                    return response_body, 429
                abort(429)

            db.session.add(UserVisit(
                endpoint = request.endpoint,
            ))
            db.session.commit()
            return route_function(*args, **kwargs)

        return limit_worker
    return limit_function_getter