from datetime import timedelta
from flask import (flash,
                   render_template,
                   redirect,
                   request,
                   session,
                   url_for)
from flask.ext.login import (current_user,
                             logout_user,
                             login_fresh)

from breezeminder.app import app
from breezeminder.forms.user import (LoginForm,
                                     RegisterForm,
                                     ResetPasswordForm,
                                     PasswordChangeForm)
from breezeminder.models.user import User
from breezeminder.models.messaging import Messaging
from breezeminder.util.views import redirect_next, nocache
from breezeminder.util.auth import authenticate


@nocache
def register():
    if current_user is not None and current_user.is_authenticated():
        return redirect_next()
    else:
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate():
            fields = form.data
            del fields['confirm']

            user = User.objects.create(**fields)
            user.is_verified = False
            user.set_password(fields['password'])
            user.save()

            # Schedule a welcome letter
            Messaging.objects.create(recipients=[user.email],
                                     sender=app.config['DEFAULT_MAIL_SENDER'],
                                     subject='Welcome to BreezeMinder - Please Verify Email Address',
                                     message=render_template('messages/email/welcome.html', current_user=user),
                                     is_immediate=True)

            context = {
                'title': 'Registration Complete',
                'description': 'Registration Complete'
            }

            return render_template('auth/register_complete.html', **context)

    context = {
        'title': 'Register',
        'description': 'Create a BreezeMinder account to manage Breeze cards and MARTA reminders',
        'form': form
    }

    return render_template('auth/register.html', **context)


@nocache
def reset_password():
    if current_user is not None and current_user.is_authenticated():
        return redirect_next()
    else:
        form = ResetPasswordForm(request.form)
        if request.method == 'POST' and form.validate():
            try:
                user = User.objects.get(email=form.data['email'])

                # Send out the message
                Messaging.objects.create(recipients=[user.email],
                                         sender=app.config['DEFAULT_MAIL_SENDER'],
                                         subject='BreezeMinder - Password Reset',
                                         message=render_template('messages/email/reset_password.html', current_user=user),
                                         is_immediate=True)

                flash('We have sent an email to you with further instructions to reset your password.', 'success')
                return redirect(url_for('auth.login'))
            except User.DoesNotExist:
                flash('We cannot locate the email address you have entered. Please make sure it is correct.', 'error')

    context = {
        'title': 'Reset Password',
        'description': 'Reset BreezeMinder.com password',
        'form': form
    }

    return render_template('auth/reset_password.html', **context)


@nocache
def new_password(auth_code):
    user = User.objects.get_or_404(pk_hash=auth_code)
    form = PasswordChangeForm(request.form)

    if request.method == 'POST' and form.validate():
        user.set_password(form.password.data)
        user.save()
        flash('Password changed successfully', 'success')
        return redirect(url_for('auth.login'))

    context = {
        'title': 'Choose New Password',
        'description': 'Choose new BreezeMinder.com password',
        'form': form
    }

    return render_template('user/password.html', **context)


@nocache
def verify(pk_hash):
    user = User.objects.get_or_404(pk_hash=pk_hash)
    user.verify()

    flash('You have successfully verified your email address. You can now log in', 'success')
    return redirect(url_for('auth.login'))


@nocache
def login():
    if current_user is not None and current_user.is_authenticated() and login_fresh():
        return redirect_next()
    else:
        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():
            try:
                authenticate(username=form.email.data,
                             password=form.password.data)

                # Set session timeout
                session.permanent = True
                app.permanent_session_lifetime = app.config.get('SESSION_TIMEOUT', timedelta(minutes=30))

                flash('Welcome Back!', 'info')

                # Because shit can break
                session['_fresh'] = True
                session.update()
                if request.args.get('next'):
                    return redirect_next()
                else:
                    return redirect(url_for('user.profile'))
            except:
                app.logger.info('Invalid login attempt for username %s' % form.email.data)
                flash('Invalid username/password', 'error')
                return redirect(url_for('auth.login', next=request.args.get('next', '/')))

    context = {
        'title': 'Login',
        'description': 'Login form for BreezeMinder.com to access Breeze cards and MARTA reminders',
        'form': form
    }

    return render_template('auth/login.html', **context)


def logout():
    logout_user()
    return redirect_next()


app.add_url_rule('/register/', 'auth.register', register, methods=['GET', 'POST'])
app.add_url_rule('/reset-password/', 'auth.reset_password', reset_password, methods=['GET', 'POST'])
app.add_url_rule('/reset-password/<auth_code>', 'auth.new_password', new_password, methods=['GET', 'POST'])
app.add_url_rule('/verify/<pk_hash>', 'auth.verify', verify)
app.add_url_rule('/login/', 'auth.login', login, methods=['GET', 'POST'])
app.add_url_rule('/logout/', 'auth.logout', logout)
