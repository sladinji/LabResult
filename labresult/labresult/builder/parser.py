

class BaseParser():
    """
    Base class for labresult parser.
    """

    def __init__(self, marker=None, dbload = True):
        """
        :param marker: marker before tags, if marker = None, try to find
        it (should be something like "&a200C" or "&a350C").
        :param dbload: true means db object will be load from db according to
        their external_id, false means no interaction with db, usefull for
        tests.
        """
        self.marker = marker
        self.dbload = dbload
