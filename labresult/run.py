import sys

import labresult
from labresult import create_app

def usage():
    print("Usage : %s [%s]" % (sys.argv[0],
        "|".join(labresult.conf_short.keys())))


def main(conf):
    labresult.app, labresult.celery  = create_app(conf)
    from labresult.lib.conf import do_post_config
    do_post_config(labresult.app)
    labresult.app.run(host=labresult.app.config['HOST'], threaded=True)

if __name__ == '__main__':
    conf = 'prod'
    if len(sys.argv) == 2 :
        conf = sys.argv[1]
        if conf not in labresult.conf_short.keys():
            usage()
            sys.exit(0)
    elif len(sys.argv) > 2 :
        usage()
        sys.exit(0)
    main(conf)

