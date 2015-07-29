import unittest
import requests
import time
import jsonpickle
import testhelpers

def line_count(path):
    count = 0
    for _ in open(path).xreadlines():
        count += 1
    return count

BASE_URL = "http://testarteria1:10800/api/1.0"
def resource(res):
    return "{0}{1}".format(BASE_URL, res)

class RestApiTestCase(unittest.TestCase):
    # NOTE: Also tests log files, so currently needs to run from the server
    # itself, and the log files being tested against are assumed to be small
    # These tests are intended to be full integration tests, mocking nothing

    BASE_URL = "http://testarteria1:10800/api/1.0"

    def setUp(self):
        self.errors_logged = testhelpers.TestFunctionDelta(
            lambda: line_count('/var/log/runfolder/error.log'), self, 0.1)
        self.infos_logged = testhelpers.TestFunctionDelta(
            lambda: line_count('/var/log/runfolder/info.log'), self, 0.1)

    def test_basic_smoke_test(self):
        resp = requests.get(self.BASE_URL)
        self.assertEqual(resp.status_code, 200)
        self.infos_logged.assert_changed_by_total(1)
        self.errors_logged.assert_changed_by_total(0)

    def test_not_monitored_path_returns_400(self):
        res = resource("/runfolders/path/notmonitored/dir/")
        resp = requests.get(res)
        self.assertEqual(resp.status_code, 400)
        # Tornado currently writes two entries for 400, for tornado.general and tornado.access
        self.infos_logged.assert_changed_by_total(2)
        self.errors_logged.assert_changed_by_total(0)

    def test_can_create_and_update_state(self):
        # First, we want to make sure it's not there now, resulting in 404 warn log:
        file_postfix = int(1000 * time.time())
        # Ensure that we can create a random runfolder at one of the mountpoints
        path = "/data/testarteria1/mon1/runfolder_inttest_{0}".format(file_postfix)

        resp = requests.get(resource("/runfolders/path{0}").format(path))
        self.assertEqual(resp.status_code, 404)

        # Now, create the folder
        resp = requests.put(resource("/runfolders/path{0}".format(path)))
        self.assertEqual(resp.status_code, 200)

        # Create the complete marker
        url = resource("/runfolders/test/markasready/path{0}".format(path))
        resp = requests.put(url)
        self.assertEqual(resp.status_code, 200)

        # The runfolder should show up in /runfolders
        resp = requests.get(resource("/runfolders"))
        self.assertEqual(resp.status_code, 200)
        runfolders = jsonpickle.decode(resp.text)
        matching = [runfolder for runfolder in runfolders if runfolder["path"] == path]
        self.assertEqual(len(matching), 1)

        # TODO: Change state to "processing" and ensure it doesn't show up in /runfolders
        self.infos_logged.assert_changed_by_total(7)
        self.errors_logged.assert_changed_by_total(0)


if __name__ == '__main__':
    unittest.main()
