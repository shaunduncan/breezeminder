from flask import (flash,
                   render_template,
                   redirect,
                   request,
                   url_for)
from flask.ext.login import (current_user,
                             fresh_login_required)

from breezeminder.app import app
from breezeminder.forms.user import (ProfileForm,
                                     PasswordChangeForm,
                                     VerifyCellForm)


@fresh_login_required
def profile():
    user = current_user._get_current_object()

    if request.method == 'POST':
        if user.needs_to_verify_phone:
            form = VerifyCellForm(request.form)
            if form.validate():
                if user.cell_verify_code == form.verify_code.data:
                    user.cell_verified = True
                    user.save()
                    flash('Your mobile phone was activated successfully', 'success')
                else:
                    flash('That code does not match the code we sent you. Try again', 'error')

                return redirect(url_for('user.profile'))
        else:
            form = ProfileForm(request.form)
            if form.validate():
                form.populate_user(user)
                user.save()

                flash('Profile updated successfully', 'success')

                if user.cell_phone and not user.cell_verified:
                    # Send out a notice
                    flash('We sent you a verification code to your mobile phone. Please enter that code below', 'warning')
                    user.send_cell_verification()

                return redirect(url_for('user.profile'))
    else:
        if user.needs_to_verify_phone:
            form = VerifyCellForm(request.form)
        else:
            form = ProfileForm.from_user(current_user)

    context = {
        'title': 'Your Profile',
        'description': 'Manage your BreezeMinder.com profile and account',
        'form': form
    }

    return render_template('user/profile.html', **context)


@fresh_login_required
def resend_cell_code():
    current_user.send_cell_verification()

    flash('We resent the verification code to your mobile phone', 'success')
    return redirect(url_for('user.profile'))


@fresh_login_required
def cancel_cell_verify():
    user = current_user._get_current_object()
    user.cell_phone = None
    user.cell_verify_code = None
    user.cell_verified = False
    user.save()

    flash('You have successfully cancelled verifying your mobile number', 'success')
    return redirect(url_for('user.profile'))


@fresh_login_required
def change_password():
    form = PasswordChangeForm(request.form)
    if request.method == 'POST' and form.validate():
        # Check current pasword
        if current_user.hash_password(form.current_password.data) != current_user.password:
            flash('Your current password is incorrect', 'error')
        else:
            current_user.set_password(form.password.data)
            current_user.save()
            flash('Password changed successfully', 'success')
        return redirect(url_for('user.password'))

    context = {
        'title': 'Change Password',
        'description': 'Change your BreezeMinder.com account password',
        'form': form
    }

    return render_template('user/password.html', **context)


app.add_url_rule('/me/', 'user.profile', profile, methods=['GET', 'POST'])
app.add_url_rule('/me/mobile/resend', 'user.mobile.resend', resend_cell_code)
app.add_url_rule('/me/mobile/cancel', 'user.mobile.cancel', cancel_cell_verify)
app.add_url_rule('/me/password/', 'user.password', change_password, methods=['GET', 'POST'])
