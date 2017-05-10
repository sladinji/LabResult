import sys

import labresult
from labresult import create_app, conf_short


if __name__ == '__main__':
    #get conf from parameter
    getconf = [ x for x in sys.argv if "conf=" in x]
    if getconf:
        # celery do not like dirty argv
        sys.argv.remove(getconf[0])
    conf = getconf[0][5:] if getconf else 'prod'
    if conf in conf_short:
        print("Start with %s conf" % conf)
    else :
        sys.stderr.write("%s is not a valid conf. Choose between %s" % ( conf,
            conf_short.keys()))
        sys.exit(-1)
    labresult.app, labresult.celery = create_app(conf)
    from labresult.lib.conf import do_post_config
    do_post_config(labresult.app)
    with labresult.app.app_context():
        labresult.celery.start()
