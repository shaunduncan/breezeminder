import os

from flask import (flash,
                   redirect,
                   render_template,
                   request,
                   send_from_directory,
                   url_for)

from breezeminder.app import app
from breezeminder.forms.contact import ContactForm
from breezeminder.models.messaging import Messaging


def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.png', mimetype='image/png')


def index():
    context = {
        'show_footer_ad': True
    }
    return render_template('pages/index.html', **context)


def privacy():
    context = {
        'title': 'Privacy Policy',
        'description': 'The BreezeMinder Privacy Policy',
        'show_footer_ad': True
    }
    return render_template('pages/privacy.html', **context)


def terms():
    context = {
        'title': 'Terms and Conditions',
        'description': 'Terms and Conditions for using BreezeMinder.com',
        'show_footer_ad': True
    }
    return render_template('pages/terms.html', **context)


def contact():
    form = ContactForm(request.form)

    if request.method == 'POST' and form.validate():
        try:
            Messaging.objects.create(recipients=['help@breezeminder.com'],
                                     sender=form.email.data,
                                     subject='[BM Feedback] %s' % form.subject.data,
                                     message=form.message.data)
            flash('Message sent successfully', 'success')
        except:
            flash('Your message could not be sent at this time', 'error')
        return redirect(url_for('contact'))

    context = {
        'form': form,
        'title': 'Contact Us',
        'description': 'A contact form to send feedback or concerns to BreezeMinder.com'
    }

    return render_template('pages/contact.html', **context)


app.add_url_rule('/favicon.ico', 'favicon', favicon)
app.add_url_rule('/', 'index', index)
app.add_url_rule('/privacy/', 'privacy', privacy)
app.add_url_rule('/terms/', 'terms', terms)
app.add_url_rule('/contact/', 'contact', contact, methods=['GET', 'POST'])
