from flask import request, abort
from sqlalchemy import func
from .db import UserVisit

from .functions import get_user_ip_address
import datetime


class Limiter:
    db = None
    app = None

    def __init__(self, app, db) -> None:
        self.init_app(app=app, db=db)
        self.rate_data = {}

    def init_app(self, app, db):
        self.app = app
        self.db = db

        @app.before_request
        def before_each_request():
            if request.endpoint in self.rate_data.keys():
                dt_right = datetime.datetime.utcnow()
                dt_left = datetime.datetime.utcnow() - self.rate_data[request.endpoint]['timedelta']
                user_visits_count = UserVisit.query.with_entities(func.count(UserVisit.id)).filter(UserVisit.user_ip_address == get_user_ip_address(), UserVisit.endpoint == request.endpoint, UserVisit.created_date.between(dt_left, dt_right)).first()[0]

                if user_visits_count > self.rate_data[request.endpoint]['per_timedelta']:
                    abort(429)

                self.db.session.add(UserVisit(
                    endpoint=request.endpoint
                ))
                self.db.session.commit()


    def set_limit(self, endpoint:str, timedelta_obj:datetime.timedelta, limit: int):
        self.rate_data[endpoint] = {
            "endpoint": endpoint,
            "timedelta": timedelta_obj,
            "per_timedelta": limit
        }
