from celery import Celery
from flask import Flask, request, session, send_from_directory
from flask.ext.babelex import Babel, Domain


app = None
celery = None

conf_short = {
    'test': 'labresult.config.TestConfig',
    'dev': 'labresult.config.DevConfig',
    'prod': 'labresult.config.ProductionConfig',
    't300': 'labresult.config.T300Config',
    't300db': 'labresult.config.T300DB',
}


def make_celery(app):
    """
    flask configurator
    """

    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.config_from_object(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_app(config='prod'):
    app = Flask(__name__)
    app.config.from_object(conf_short[config])

    # i18n
    babel = Babel(app, default_domain=Domain())

    @babel.localeselector
    def get_locale():
        override = request.args.get('lang')
        if override:
            session['lang'] = override
            return session.get('lang', 'fr')

    # param db
    from labresult.model import db
    db.init_app(app)

    # flask-login init
    from labresult.views import login
    login.init_login(app)

    celery = make_celery(app)

    # @app.route('/sitemap.xml')
    @app.route('/robots.txt')
    def static_from_root():
            return send_from_directory(app.static_folder, request.path[1:])

    return app, celery
