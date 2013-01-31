import traceback

from flask import render_template, request

from breezeminder.app import app
from breezeminder.util.views import nocache


@app.errorhandler(404)
@nocache
def handle_404(error=None):
    if error:
        # There is actually an error
        app.logger.error('Caught 404 accessing page: %s' % request.path)

    context = {
        'title': 'Page Not Found',
        'description': 'The page you are accessing cannot be found',
        'show_footer_ad': True
    }
    return render_template('errors/404.html', **context), 404


@app.errorhandler(500)
@nocache
def handle_500(error=None):
    if error:
        # There is actually an error
        app.logger.critical('Caught 500 accessing page: %s. Message: %s' % (request.path, error.message))
        app.logger.critical(traceback.format_exc(error))

    context = {
        'title': 'Internal Server Error',
        'description': 'The server is experiencing issues at the moment',
        'show_footer_ad': True
    }
    return render_template('errors/500.html', **context), 500


app.add_url_rule('/404.html', 'error.404', handle_404)
app.add_url_rule('/500.html', 'error.500', handle_500)
