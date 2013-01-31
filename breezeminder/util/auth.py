import functools

from datetime import datetime, timedelta
from flask import session, flash, redirect
from flask.ext.login import current_user, login_user

from breezeminder.app import app
from breezeminder.models.user import User


def authenticate(username, password):
    user = current_user

    if user is None or not user.is_authenticated():
        # Expectation is to bubble the exception
        pass_hash = hash_password(password)
        user = User.objects.get(email__iexact=username,
                                password__exact=pass_hash,
                                is_verified=True)
    
    if user is not None:
        login_user(user, remember=True)
    return user


@app.cache.memoize(timeout=3600)
def hash_password(value):
    return User.hash_password(value)


def admin_only(fn):
    @functools.wraps(fn)
    def check_admin(*args, **kwargs):
        user = current_user
        if user is not None and user.is_authenticated() and user.is_admin:
            return fn(*args, **kwargs)
        else:
            return unauthorized()
    return check_admin
