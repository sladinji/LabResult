from kombu.common import Broadcast
from kombu import Queue, Exchange
import logging


class Config(object):
    ADMINS_EMAILS = ['julien.almarcha@gmail.com']
    SECRET_KEY = b'`\xae\xde\xa6\xe7\xeb\x14\x0eh\\\xf8\xd55\xfdf\x0c\x95\xb5\x11\x0fbIE\x98'
    MONGODB_SETTINGS = {'DB': 'lrtest', 'HOST': 'lr_mongodb'}
    BABEL_DEFAULT_LOCALE = 'fr'
    CELERY_BROKER_URL = 'amqp://lr_rabbitmq//'
    CELERY_RESULT_BACKEND = 'amqp://lr_rabbitmq//'
    CELERY_TASK_SERIALIZER = 'pickle'
    CELERY_RESULT_SERIALIZER = 'pickle'
    CELERY_ACCEPT_CONTENT = ['pickle']
    CELERY_TIMEZONE = 'Europe/Paris'
    CELERY_ENABLE_UTC = True

    # VERY IMPORTANT SETTING TTL TO NOT BE OVERLOADED BY RESULT QUEUE
    CELERY_TASK_RESULT_EXPIRES = 60 * 10  # SECONDS
    CELERY_STORE_ERRORS_EVEN_IF_IGNORED = False

    CELERY_QUEUES = (
        Broadcast('broadcast_tasks'),
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("for_conversion", Exchange("for_conversion"),
              routing_key="for_conversion"),
        Queue("for_integration", Exchange("for_integration"),
              routing_key="for_integration"))
    CELERY_DEFAULT_QUEUE = 'default'
    CELERY_ROUTES = {
        'default':
        {
            "exchange": "default",
            "binding_key": "default",
        },
        # INTEGRATION
        'labresult.builder.tasks.integrate':
        {'queue': 'for_integration'},
        # CONVERSION
        'labresult.converter.tasks.pcl2pdf':
        {'queue': 'for_conversion'},
        'labresult.converter.tasks.merge':
        {'queue': 'for_conversion'},
        'labresult.converter.tasks.pdf2img':
        {'queue': 'for_conversion'},
        'labresult.converter.tasks.save_img':
        {'queue': 'for_conversion'},
        'labresult.builder.tasks.get_gridfs_data':
        {'queue': 'for_conversion'},
        'labresult.converter.tasks.get_pdf_num_pages':
        {'queue': 'for_conversion'},

    }
    CELERYD_POOL_RESTARTS = True
    DEBUG = False
    TESTING = False
    HOST = '0.0.0.0'
    SEND_FILE_MAX_AGE_DEFAULT = 0
    LOG_PATH = 'labresult.log'
    LOG_LEVEL = logging.ERROR


class ProductionConfig(Config):
    MONGODB_SETTINGS = {'DB': 'lrprod', 'HOST': 'lr_mongodb'}
    CELERY_BROKER_URL = 'amqp://lr_rabbitmq//'
    CELERY_RESULT_BACKEND = 'amqp://lr_rabbitmq//'
    LOG_LEVEL = logging.DEBUG


class DevConfig(Config):
    MONGODB_SETTINGS = {'DB': 'lrprod', 'HOST': 'lr_mongodb'}
    CELERY_BROKER_URL = 'amqp://lr_rabbitmq//'
    CELERY_RESULT_BACKEND = 'amqp://lr_rabbitmq//'
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class TestConfig(Config):
    TESTING = True
    CELERY_ALWAYS_EAGER = True
    DEBUG = True
