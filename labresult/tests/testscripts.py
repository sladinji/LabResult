
import testlib
import sys
from labresult.lib import scripts

class TestScripts(testlib.TestBase):

    def test_add_admin(self):
        sys.argv = ['script', 'test', 'dowst', 'dowst']
        scripts.add_admin()

    def test_set_demo_options(self):
        sys.argv = ['script', 'test']
        scripts.set_demo_options(1)

    def test_gen_result(self):
        sys.argv = ['script', 'test', 1]
        scripts.gen_result()
