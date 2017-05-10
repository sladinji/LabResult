from datetime import timedelta
from labresult.lib.model import get_option
import labresult

def do_post_config():
    """
    Apply paramters that are in DB. Because of dependancies on labresult.app
    for logging, DB configuration can't be done in create_app.
    """
    time_out = get_option('session_timeout', 120,
            "Durée en minutes d'inactivité avant déconnexion automatique.")
    labresult.app.permanent_session_lifetime = timedelta(time_out)
