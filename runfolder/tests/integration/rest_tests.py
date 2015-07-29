import unittest
import requests
import time
import jsonpickle
import testhelpers
import re

def line_count(path):
    count = 0
    for _ in open(path).xreadlines():
        count += 1
    return count

class BaseRestTest(unittest.TestCase):
    BASE_URL = "http://testarteria1:10800/api/1.0"

    def _get_full_url(self, url):
        """Replaces a starting . with base url"""
        return re.sub(r'^\.', self.BASE_URL, url)

    def _validate_response(self, resp, expect):
        if expect is not None:
            self.assertEqual(resp.status_code, expect)

    def put(self, url, obj=None, expect=200):
        """
        Sends a PUT to the url, with the obj as the body

        A starting '.' is replaced with the base url
        :param obj: A Python object
        :param expect: The expected status code
        """
        json = jsonpickle.encode(obj)
        full_url = self._get_full_url(url)
        resp = requests.put(full_url, json)
        self._validate_response(resp, expect)
        return resp

    def get(self, url, expect=200):
        """
        Gets the item at url and returns a Python object based on the json body (if any).

        A starting '.' is replaced with the base url

        :param expect: The expected status code
        """
        full_url = self._get_full_url(url)
        resp = requests.get(full_url)
        self._validate_response(resp, expect)
        try:
            resp.body_obj = jsonpickle.decode(resp.text)
        except ValueError:
            resp.body_obj = None
        return resp

class RestApiTestCase(BaseRestTest):
    # NOTE: Also tests log files, so currently needs to run from the server
    # itself, and the log files being tested against are assumed to be small
    # These tests are intended to be full integration tests, mocking nothing
    def setUp(self):
        self.messages_logged = testhelpers.TestFunctionDelta(
            lambda: line_count('/var/log/runfolder/runfolder.log'), self, 0.1)

    def test_can_change_log_level(self):
        resp = self.put("./admin/log_level", {"log_level": "DEBUG"})

        resp = self.get("./admin/log_level")
        self.assertEqual(resp.body_obj["log_level"], "DEBUG")

        # For the rest of the test, and by default, we should have log level WARNING
        resp = self.put("./admin/log_level", {"log_level": "WARNING"})

    def test_basic_smoke_test(self):
        resp = self.get(".")
        self.messages_logged.assert_changed_by_total(0)

    def test_not_monitored_path_returns_400(self):
        resp = self.get("./runfolders/path/notmonitored/dir/", expect=400)
        # Tornado currently writes two entries for 400, for tornado.general and tornado.access
        self.messages_logged.assert_changed_by_total(2)

    def test_can_create_and_update_state(self):
        # First, we want to make sure it's not there now, resulting in 404 warn log:
        file_postfix = int(1000 * time.time())
        # Ensure that we can create a random runfolder at one of the mountpoints
        path = "/data/testarteria1/mon1/runfolder_inttest_{0}".format(file_postfix)

        resp = self.get("./runfolders/path{0}".format(path), expect=404)

        # Now, create the folder
        resp = self.put("./runfolders/path{0}".format(path))

        # Create the complete marker
        resp = self.put("./runfolders/test/markasready/path{0}".format(path))

        # The runfolder should show up in /runfolders
        resp = self.get("./runfolders")
        runfolders = jsonpickle.decode(resp.text)
        matching = [runfolder for runfolder in runfolders if runfolder["path"] == path]
        self.assertEqual(len(matching), 1)

        # TODO: Change state to "processing" and ensure it doesn't show up in /runfolders
        self.messages_logged.assert_changed_by_total(2)


if __name__ == '__main__':
    unittest.main()
