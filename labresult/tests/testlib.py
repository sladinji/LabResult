import unittest
import os
import sys
import inspect
import labresult
from labresult import create_app
labresult.app, labresult.celery  = create_app('test')
from labresult.lib.conf import do_post_config
do_post_config(labresult.app)
from labresult.model import Document


class TestBase(unittest.TestCase):
    def setUp(self):
        self.test_folder =  os.path.join(os.path.dirname(__file__), "data")
        self.client = labresult.app.test_client()

    def tearDown(self):
        """
        Iter over all collections and drop them.
        """
        clsmembers = inspect.getmembers(sys.modules[labresult.model.__name__],
        inspect.isclass)
        for name, obj in clsmembers:
            if hasattr(obj, 'drop_collection'):
                obj.drop_collection()

    def get_data(self, filename) :
        return open(os.path.join(self.test_folder, filename), 'rb').read()

    def get_doc(self, filename ):
        if '.pdf' in filename:
            return Document(pdf=self.get_data(filename))
        return Document(data=self.get_data(filename))

