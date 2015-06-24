import unittest
from arteria.runfolder import *


class RunfolderServiceTestCase(unittest.TestCase):
    def _valid_runfolder(self, path):
        if path.endswith("RTAComplete.txt"):
            return True
        elif path.endswith(".arteria/state"):
            return False
        else:
            raise Exception("Unexpected path")

    def test_list_available_runfolders(self):
        # Setup
        logger = Logger()
        configuration_svc = ConfigurationService()
        configuration_svc.monitored_directories = lambda s: [
            "/data/testtank1/mon1", "/data/testtank1/mon2"]
        runfolder_svc = RunfolderService(configuration_svc, logger)

        runfolder_svc._file_exists = self._valid_runfolder
        runfolder_svc._subdirectories = lambda path: ["runfolder001"]
        runfolder_svc._host = lambda: "localhost"

        # Test
        runfolders = runfolder_svc.list_available_runfolders()
        runfolders = list(runfolders)
        self.assertEqual(len(runfolders), 2)

        runfolders_str = sorted([str(runfolder) for runfolder in runfolders])
        expected = ["ready: /data/testtank1/mon1/runfolder001@localhost",
                    "ready: /data/testtank1/mon2/runfolder001@localhost"]
        self.assertEqual(runfolders_str, expected)

    def test_next_runfolder(self):
        # Setup
        logger = Logger()
        configuration_svc = ConfigurationService()
        configuration_svc.monitored_directories = lambda s: ["/data/testtank1/mon1"]
        runfolder_svc = RunfolderService(configuration_svc, logger)

        runfolder_svc._file_exists = self._valid_runfolder

        runfolder_svc._subdirectories = lambda path: ["runfolder001"]
        runfolder_svc._host = lambda: "localhost"

        # Test
        runfolder = runfolder_svc.next_runfolder()
        expected = "ready: /data/testtank1/mon1/runfolder001@localhost"
        self.assertEqual(str(runfolder), expected)


if __name__ == '__main__':
    unittest.main()