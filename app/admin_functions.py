from flask import session
from .db import db, BlacklistIP
from .functions import get_user_ip_address
from .db import AdminUserSession


def blacklist_current_user():
    db.session.add(BlacklistIP(
        ipaddress=get_user_ip_address()
    ))
    db.session.commit()


def get_current_admin_user():
    if 'admin-session-id' in session:
        session_id = session['admin-session-id']
        user_session = AdminUserSession.query.filter(AdminUserSession.session_id == session_id).first()
        if user_session is not None:
            return user_session.user