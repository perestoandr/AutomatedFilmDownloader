import base64
import unittest
from environment import environment


class UnitTests(unittest.TestCase):
    def test_environment_login(self):
        self.assertEqual(environment.get('rutracker_login'), 'DumbAssEr')

    def test_environment_pass(self):
        self.assertEqual(base64.b64decode(environment.get('rutracker_password_base64')), 'xbDOB')

    def test_environment_pass64(self):
        self.assertEqual(environment.get('rutracker_password_base64'), base64.b64encode('xbDOB'))
