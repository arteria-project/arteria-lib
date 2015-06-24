import unittest
import requests
import time
import jsonpickle

class RestApiTestCase(unittest.TestCase):
    BASE_URL = "http://testtank1:10800/api/1.0"

    def test_basic_smoke_test(self):
        resp = requests.get(self.BASE_URL)
        self.assertEqual(resp.status_code, 200)

    def test_can_create_and_update_state(self):
        file_postfix = int(1000 * time.time())
        # Ensure that we can create a random runfolder at one of the mounpoints
        path = "/data/testtank1/mon1/runfolder_inttest_{0}".format(file_postfix)
        print path
        # First, we want to make sure it's not there now:
        url = "{0}/runfolders/path{1}".format(self.BASE_URL, path)
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 500)  # TODO: should be 404

        # Now, create the folder
        url = "{0}/runfolders/path{1}".format(self.BASE_URL, path)
        resp = requests.put(url)
        self.assertEqual(resp.status_code, 200)

        # Create the complete marker
        url = "{0}/runfolders/test/markasready/path{1}".format(self.BASE_URL, path)
        resp = requests.put(url)
        self.assertEqual(resp.status_code, 200)

        # The runfolder should show up in /runfolders
        url = "{0}/runfolders".format(self.BASE_URL)
        resp = requests.get(url)
        self.assertEqual(resp.status_code, 200)
        runfolders = jsonpickle.decode(resp.text)
        matching = [runfolder for runfolder in runfolders if runfolder["path"] == path]
        self.assertEqual(len(matching), 1)

        # TODO: Change state to "processing" and ensure it doesn't show up in /runfolders


if __name__ == '__main__':
    unittest.main()