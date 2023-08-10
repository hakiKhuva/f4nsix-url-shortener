from flask_dance.contrib.github import github
from functools import wraps
from flask import redirect, url_for

from .functions import is_user_loggedin


def account_login_required(f):
    """
    check for user is logged in or not, it uses `is_user_loggedin` function
    """
    @wraps(f)
    def fun(*args, **kwargs):
        if is_user_loggedin() is True:
            return f(*args, **kwargs)
        return redirect(url_for('Auth.index'))
    
    return fun