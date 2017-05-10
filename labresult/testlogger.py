import labresult
labresult.app, labresult.celery = labresult.create_app("prod")
from labresult.lib.conf import do_post_config
do_post_config(labresult.app)
labresult.app.logger.error("allez google arrête de bloquer....")
