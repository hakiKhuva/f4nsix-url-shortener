from flask import session, redirect, url_for
from functools import wraps

from .db import AdminUserSession
from .config import AdminConfig

import datetime


def admin_login_required(f):
    @wraps(f)
    def fun(*args, **kwargs):
        if 'admin-session-id' in session and session['admin-session-id'] is not None:
            session_id = session['admin-session-id']
            session_data = AdminUserSession.query.filter(AdminUserSession.session_id == session_id).first()
            if session_data is not None:
                if session_data.allowed is True:
                    if datetime.datetime.utcnow()-session_data.created_date <= AdminConfig.SESSION_EXPIRE_TIME:
                        return f(*args, **kwargs)
            session.pop('admin-session-id','')
        return redirect(url_for("Admin.login"))
    return fun