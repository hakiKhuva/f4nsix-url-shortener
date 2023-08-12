from flask import Flask, render_template, request, send_from_directory
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
    # add flask cli commands
    # -------------------------
    from .commands import create_admin_user, rate_limit_show
    app.cli.add_command(create_admin_user)
    app.cli.add_command(rate_limit_show)


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
    
    from .views.auth import auth
    app.register_blueprint(auth)

    from .views.api import api
    app.register_blueprint(api)

    from .views.account import account
    app.register_blueprint(account)


    # -------------------------
    # add error handlers
    # -------------------------
    from .functions import modified_render_template
    
    @app.errorhandler(429)
    def rate_limit_handler(e):
        return modified_render_template(
            "errors/rate_limit.html",
            page_title="Too many requests"
        ), 429


    @app.errorhandler(404)
    def not_found_handler(e):
        return modified_render_template(
            "errors/not_found.html",
            page_title="Not found"
        ), 404
    

    # --------------------------------------------------
    # misc routes for sending files
    # --------------------------------------------------

    @app.route('/googled75d43e26e15ddd9.html')
    @app.route('/sitemap.xml')
    @app.route('/robots.txt')
    def files_from_static_path():
        if request.url_rule.rule == "/sitemap.xml":
            return send_from_directory(app.static_folder, "sitemap.xml")
        if request.url_rule.rule == "/robots.txt":
            return send_from_directory(app.static_folder, "robots.txt")
        else:
            return render_template('misc/googled75d43e26e15ddd9.html')

    # -------------------------
    # return final app
    # -------------------------
    return app