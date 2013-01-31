import mongoengine

from flask_mongoengine import MongoEngine


class PortAwareMongoEngine(MongoEngine):
    def init_app(self, app):
        db = app.config['MONGODB_DB']
        username = app.config.get('MONGODB_USERNAME', None)
        password = app.config.get('MONGODB_PASSWORD', None)
        port = app.config.get('MONGODB_PORT', 27017)

        # more settings e.g. port etc needed

        try:
            self.connection = mongoengine.connect(
                db=db, username=username, password=password, port=port)
        except mongoengine.connection.ConnectionError:
            # Useful for when code is accessed, like say a sphinx docs
            # build and there's no database running.
            self.connection = None
