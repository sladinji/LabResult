import labresult
from labresult import create_app

app, _ = labresult.app, labresult.celery = create_app('prod')

from labresult.lib.conf import do_post_config

do_post_config(app)
