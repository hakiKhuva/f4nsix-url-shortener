from flask import Blueprint, request, session, flash, redirect, url_for, abort
from sqlalchemy import func, Date
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import AdminUser, BlacklistIP, AdminUserSession, ShortenLink, ShortenLinkTransaction, UserVisit, db, User, APIRequest, Notification
from ..functions import modified_render_template, get_user_ip_address, get_geo_data, get_date
from ..admin_functions import blacklist_current_user, get_current_admin_user
from ..admin_decorators import admin_login_required
from ..forms.admin import AdminLoginForm, AdminEditForm, NotificationForm
from ..forms.universal import UniversalCsrfForm
from ..config import AdminConfig, BaseConfig

import datetime
import pygal
import markdown


admin = Blueprint("Admin", __name__, url_prefix="/admin")

@admin.before_request
def before_each_admin_request_blacklist_if_any():
    blacklist_data = BlacklistIP.query.filter(BlacklistIP.ipaddress == get_user_ip_address()).order_by(BlacklistIP.created_date.desc()).first()
    if blacklist_data is not None:
        if datetime.datetime.utcnow()-blacklist_data.created_date <= AdminConfig.IP_BLACKLIST_EXPIRE_TIME:
            abort(403)


@admin.after_request
def after_each_request_of_admin(resp):
    resp.headers['Cache-Control'] = "no-cache"
    return resp


@admin.route('/login', methods=["GET", "POST"])
def login():
    if 'admin-session-id' in session: return redirect(url_for('.index'))

    form = AdminLoginForm({})
    
    if request.method == "POST":
        form = AdminLoginForm(request.form)
        if form.validate_on_submit() is True:
            email_address = form.email_address.data
            password = form.password.data

            user = AdminUser.query.filter(AdminUser.email_address == email_address).first()
            if user is None:
                flash('User not found with entered credentials!')
                blacklist_current_user()
                return redirect(url_for("Home.index"))

            if check_password_hash(user.password, password) is not True:
                flash('User not found with entered credentials!')
                return redirect(url_for(".login"))

            geo_data = get_geo_data()
            u_session = AdminUserSession(
                ipaddress=get_user_ip_address(),
                city=geo_data.get('city'),
                region=geo_data.get('region'),
                country=geo_data.get('country'),
                admin_id = user.id
            )
            db.session.add(u_session)
            db.session.commit()
            session['admin-session-id'] = u_session.session_id

            return redirect(url_for('.index'))
        else:
            for errors in form.errors.values():
                for err in errors:
                    flash(err)
            return redirect(url_for('.login'))

    return modified_render_template(
        "admin/login.html",
        page_title="Admin Login",
        form=form
    )


@admin.route('/')
@admin_login_required
def index():
    data = {}
    data["cards"] = {}
    data["graphs"] = {}
    data["table-data"] = {}

    q = ShortenLink.query.with_entities(func.count(ShortenLink.id)).first()
    data["cards"]["Links count"] = q[0] if q is not None else 0

    q = ShortenLinkTransaction.query.with_entities(func.count(ShortenLinkTransaction.shorten_link_id.distinct())).first()
    data["cards"]["Unique links transactions"] = q[0] if q is not None else 0

    q = ShortenLinkTransaction.query.with_entities(func.count(ShortenLinkTransaction.id)).first()
    data["cards"]["Links transactions"] = q[0] if q is not None else 0

    q = BlacklistIP.query.with_entities(func.count(BlacklistIP.ipaddress.distinct())).first()
    data["cards"]["Blacklist IP"] = q[0] if q is not None else 0

    q = UserVisit.query.with_entities(func.count(UserVisit.id)).filter(UserVisit.endpoint != "Home.redirector").first()
    data["cards"]["User visits (No redirect)"] = q[0] if q is not None else 0
    
    q = UserVisit.query.with_entities(func.count(UserVisit.user_ip_address.distinct())).first()
    data["cards"]["Unique users"] = q[0] if q is not None else 0

    q = User.query.with_entities(func.count(User.id)).first()
    data["cards"]["User Accounts"] = q[0] if q is not None else 0

    q = User.query.with_entities(func.count(User.id)).filter(User.api_key != None).first()
    data["cards"]["API Keys"] = q[0] if q is not None else 0

    q = APIRequest.query.with_entities(func.count(APIRequest.id)).first()
    data["cards"]["API requests"] = q[0] if q is not None else 0


    data["table-data"]["countries"] = []
    for country_item in ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.country, func.count(ShortenLinkTransaction.id)).group_by(ShortenLinkTransaction.country).order_by(func.count(ShortenLinkTransaction.id).desc()).all():
        data["table-data"]["countries"].append([BaseConfig.COUNTRIES_DATA.get(country_item[0], "Other"), country_item[1]])

    date_today = get_date()
    
    GRAPH_DAYS = 21
    data["graphs"]["user-visits-no-redirects-data"] = {}
    for ikh in range(GRAPH_DAYS):
        current = date_today - datetime.timedelta(days=ikh)
        d = UserVisit.query.with_entities(func.count(UserVisit.id)).filter(UserVisit.created_date.cast(Date) == current).filter(UserVisit.endpoint != "Home.redirector").group_by(UserVisit.created_date.cast(Date)).first()
        if d is not None:
            visits = d[0]
        else:
            visits = 0
        data["graphs"]["user-visits-no-redirects-data"][current.strftime('%d-%m')] = visits
    
    data["graphs"]["links-created-data"] = {}
    for ikh in range(GRAPH_DAYS):
        current = date_today - datetime.timedelta(days=ikh)
        d = ShortenLink.query.with_entities(func.count(ShortenLink.id)).filter(ShortenLink.created_date.cast(Date) == current).group_by(ShortenLink.created_date.cast(Date)).first()
        if d is not None:
            links_created_count = d[0]
        else:
            links_created_count = 0
        data["graphs"]["links-created-data"][current.strftime('%d-%m')] = links_created_count
    
    data["graphs"]["link-transactions-data"] = {}
    for ikh in range(GRAPH_DAYS):
        current = date_today - datetime.timedelta(days=ikh)
        d = ShortenLinkTransaction.query.with_entities(func.count(ShortenLinkTransaction.id)).filter(ShortenLinkTransaction.created_date.cast(Date) == current).group_by(ShortenLinkTransaction.created_date.cast(Date)).first()
        if d is not None:
            link_transactions_count = d[0]
        else:
            link_transactions_count = 0
        data["graphs"]["link-transactions-data"][current.strftime('%d-%m')] = link_transactions_count
    
    data["graphs"]["user-accounts-data"] = {}
    for ikh in range(GRAPH_DAYS):
        current = date_today - datetime.timedelta(days=ikh)
        d = User.query.with_entities(func.count(User.id)).filter(User.created_date.cast(Date) == current).group_by(User.created_date.cast(Date)).first()
        user_accounts_count = d[0] if d is not None else 0
        data["graphs"]["user-accounts-data"][current.strftime('%d-%m')] = user_accounts_count
    
    data["graphs"]["api-requests-data"] = {}
    for ikh in range(GRAPH_DAYS):
        current = date_today - datetime.timedelta(days=ikh)
        d = APIRequest.query.with_entities(func.count(APIRequest.id)).filter(APIRequest.created_date.cast(Date) == current).group_by(APIRequest.created_date.cast(Date)).first()
        api_requests_count = d[0] if d is not None else 0
        data["graphs"]["api-requests-data"][current.strftime('%d-%m')] = api_requests_count

    return modified_render_template(
        "admin/index.html",
        page_title="Dashboard",
        admin_login_status=True,
        data=data,
        admin_name=get_current_admin_user().name
    )


@admin.route('/image-map')
@admin_login_required
def worldmap_image():
    tdata = ShortenLinkTransaction.query.with_entities(ShortenLinkTransaction.country, func.count(ShortenLinkTransaction.id)).group_by(ShortenLinkTransaction.country).all()
    data = {}
    for item in tdata:
        if item[0] is not None:
            data[item[0].lower()] = item[1]
    
    worldmap =  pygal.maps.world.World()
    worldmap.add("Country",data)
    worldmap.config.height = 350
    worldmap.config.show_legend = False
    return worldmap.render_data_uri()


@admin.route("/settings", methods=['GET', 'POST'])
@admin_login_required
def settings():
    form = AdminEditForm({})

    current_user = get_current_admin_user()
    if request.method == "POST":
        form = AdminEditForm(request.form)
        if form.validate_on_submit() is True:
            current_user.name = form.name.data
            current_user.email_address = form.email_address.data

            if form.new_password.data:
                current_user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash("Settings updated successfully.")
    
        else:
            for errors in form.errors.values():
                for error in errors:
                    flash(error)
    
        return redirect(url_for('.settings'))

    form.name.data = current_user.name
    form.email_address.data = current_user.email_address

    return modified_render_template(
        "admin/settings.html",
        admin_login_status=True,
        page_title="Admin settings",
        form=form
    )

@admin.route("/new-notification", methods=['GET', 'POST'])
@admin_login_required
def new_notification():
    form = NotificationForm()
    current_user = get_current_admin_user()

    if request.method == "POST":
        form = NotificationForm(request.form)
        if form.validate_on_submit() is True:
            notification_data = form.notification_data.data
            from_ = form.from_.data
            to = form.to.data

            db.session.add(Notification(
                render_data = markdown.markdown(notification_data),
                from_ = from_.astimezone(datetime.timezone.utc).replace(tzinfo=None),
                to = to.astimezone(datetime.timezone.utc).replace(tzinfo=None),
                admin_id = current_user.id
            ))
            db.session.commit()
            flash("Notification posted successfully.")
        else:
            for errors in form.errors.values():
                for error in errors:
                    flash(error)
        return redirect(url_for(".new_notification"))

    return modified_render_template(
        "admin/new_notification.html",
        page_title="New notification",
        admin_login_status=True,
        form=form
    )


@admin.route("/markdown-render", methods=['POST'])
@admin_login_required
def markdown_renderer():
    data = request.get_json().get('data')
    if data is None: abort(400)
    return markdown.markdown(data, extensions=['tables', 'fenced_code'])


@admin.route("/notifications/<int:page>", methods=['GET', 'POST'])
@admin_login_required
def all_notifications(page: int):
    form = UniversalCsrfForm()
    user = get_current_admin_user()

    if request.method == "POST":
        form = UniversalCsrfForm(request.form)
        if form.validate_on_submit() is True:
            public_id = request.form.get('public-id')
            if not public_id: abort(400)
            d = Notification.query.filter(Notification.public_id == public_id).first_or_404()
            db.session.delete(d)
            db.session.commit()
            flash("Notification with Id {} deleted successfully".format(public_id))
        else:
            for errors in form.errors.values():
                for error in errors:
                    flash(error)
        return redirect(url_for("Admin.all_notifications",page=page))

    q_data = Notification.query.filter(Notification.admin_id == user.id).paginate(per_page=10, page=page)

    return modified_render_template(
        "admin/all_notifications.html",
        page_title="All notifications",
        paginate=q_data,
        admin_login_status=True,
        form=form,
        page=page,
        page_range=range(1, q_data.pages+1)
    )


@admin.route('/sessions/<int:page>', methods=['GET', 'POST'])
@admin_login_required
def admin_sessions(page: int):
    user = get_current_admin_user()
    if request.method == "POST":
        session_id = request.form.get('session-id')
        to_value = request.form.get('to')
        if not session_id or not to_value or to_value.lower() not in ("yes", "no"):
            abort(400)
        to_value = True if to_value == "yes" else False
        
        admin_found_session = AdminUserSession.query.filter(AdminUserSession.admin_id == user.id, AdminUserSession.session_id == session_id, AdminUserSession.allowed == (not to_value)).first_or_404()
        admin_found_session.allowed = to_value
        db.session.commit()
        flash('Settings updated successfully')
        return redirect(url_for('.admin_sessions',page=page))

    paginate = AdminUserSession.query.filter(AdminUserSession.admin_id == user.id).order_by(AdminUserSession.created_date.desc()).paginate(page=page, per_page=10)
    return modified_render_template(
        "admin/sessions.html",
        page_title="Admin sessions",
        admin_login_status=True,
        max_admin_session_time=AdminConfig.SESSION_EXPIRE_TIME,
        paginate=paginate,
        country_codes=BaseConfig.COUNTRIES_DATA,
        page_range=range(1, paginate.pages+1)
    )


@admin.route('/links/<int:page>')
@admin_login_required
def links(page: int):
    links_data = ShortenLink.query.order_by(ShortenLink.created_date.desc()).paginate(page=page, per_page=10)
    
    return modified_render_template(
        "admin/links.html",
        page_title="All links",
        admin_login_status=True,
        paginate=links_data,
        page_range=range(1,links_data.pages+1)
    )


@admin.route("/logout")
@admin_login_required
def logout():
    session_id = session.pop('admin-session-id')
    sess = AdminUserSession.query.filter(AdminUserSession.session_id == session_id).first()
    sess.allowed = False
    db.session.commit()
    return redirect(url_for('.login'))