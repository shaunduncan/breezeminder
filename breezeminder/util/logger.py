import logging
import os
import stat

from logging.handlers import TimedRotatingFileHandler


LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}


def _make_writable(file):
    try:
        curMode = os.stat(file).st_mode
        os.chmod(file, curMode | stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    except (OSError, IOError):
        pass


class WritableTimedRotatingFileHandler(TimedRotatingFileHandler):

    def doRollover(self):
        # Just chmod the file
        TimedRotatingFileHandler.doRollover(self)
        _make_writable(self.baseFilename)

def configure_logging(app):
    if app.config.get('LOG_FILE'):
        log_file = app.config['LOG_FILE']
        log_file = os.path.abspath(os.path.expanduser(log_file))

        # Chmod the log file to be safe
        _make_writable(log_file)

        new_handler = WritableTimedRotatingFileHandler(log_file,
                                                       when='W6',
                                                       backupCount=5)

        if app.config.get('LOGGING_LEVEL'):
            new_level = app.config['LOGGING_LEVEL'].lower()
            new_level = LEVELS.get(new_level, logging.error)
            new_handler.setLevel(new_level)

        log_format = '%(asctime)-15s [%(levelname)s] [%(pathname)s:%(lineno)d]: %(message)s'
        new_handler.setFormatter(logging.Formatter(log_format))
        for handler in app.logger.handlers:
            handler.setFormatter(logging.Formatter(log_format))

        app.logger.addHandler(new_handler)
