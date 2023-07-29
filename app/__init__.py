from flask import Flask
from flask_migrate import Migrate
from flask_minify import Minify

import datetime


def create_app():
    """Returns Flask app"""
    app = Flask(__name__)

    # -------------------------
    # configuration
    # -------------------------
    from .config import AppConfig
    app.config.from_object(AppConfig)


    # -------------------------
    # init Flask app
    # -------------------------
    from .db import db
    db.init_app(app)
    
    Migrate(app, db)
    Minify(app)
    
    # -------------------------
    # Requests rate limiting
    # -------------------------
    from .limiter import Limiter
    limiter = Limiter(app, db)
    limiter.set_limit("Home.index", datetime.timedelta(seconds=60), 20)
    limiter.set_limit("Home.redirector", datetime.timedelta(seconds=60), 60)
    limiter.set_limit("Track.index", datetime.timedelta(seconds=60), 20)
    limiter.set_limit("Track.image_for_shorten", datetime.timedelta(seconds=60), 25)

    
    # -------------------------
    # add flask cli commands
    # -------------------------
    from .commands import create_admin_user
    app.cli.add_command(create_admin_user)

    # -------------------------
    # register Flask Blueprints
    # -------------------------
    from .views.home import home
    app.register_blueprint(home)

    from .views.track import track
    app.register_blueprint(track)

    from .views.legal import legal
    app.register_blueprint(legal)

    from .views.admin import admin
    app.register_blueprint(admin)


    # -------------------------
    # add error handlers
    # -------------------------
    from .functions import modified_render_template
    
    @app.errorhandler(429)
    def rate_limit_handler(e):
        return modified_render_template(
            "errors/rate_limit.html",
            title="Too many requests"
        ), 429


    @app.errorhandler(404)
    def not_found_handler(e):
        return modified_render_template(
            "errors/not_found.html",
            title="Not found"
        ), 404
    

    # -------------------------
    # return final app
    # -------------------------
    return app