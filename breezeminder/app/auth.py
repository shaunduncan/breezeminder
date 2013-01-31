from flask.ext.login import LoginManager

from breezeminder.app import app
from breezeminder.models.user import User


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.session_protection = 'strong'
login_manager.refresh_view = 'auth.login'
login_manager.needs_refresh_message = 'For your security, you have been logged out due to inactivity. Please log in again.'


@app.login_manager.user_loader
def load_user(id):
    try:
        return User.objects.get(id=id)
    except:
        return None
