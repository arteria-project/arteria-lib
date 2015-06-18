import unittest
from runfolder import * 
from mock import MagicMock, call

class RunfolderMonitorTestCase(unittest.TestCase):
    
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
        host_provider = HostProvider()
        runfolder_svc = RunfolderService(configuration_svc,
            host_provider, logger)

        runfolder_svc._file_exists = self._valid_runfolder

        def _subdirectories(path):
            return ["runfolder001"]
        runfolder_svc._subdirectories = _subdirectories

        # Test 
        runfolders = runfolder_svc.list_available_runfolders()
        runfolders = list(runfolders)
        self.assertEqual(len(runfolders), 2)

        runfolders_str = sorted([str(runfolder) for runfolder in runfolders])
        expected = ["ready: /var/local/arteria/mon1/runfolder001@localhost", 
                    "ready: /var/local/arteria/mon2/runfolder001@localhost"]
        self.assertEqual(runfolders_str, expected)

    def test_next_runfolder(self):
        # Setup
        logger = Logger()
        configuration_svc = ConfigurationService()
        host_provider = HostProvider()
        runfolder_svc = RunfolderService(configuration_svc,
            host_provider, logger)

        runfolder_svc._file_exists = self._valid_runfolder

        def _subdirectories(path):
            return ["runfolder001"]
        runfolder_svc._subdirectories = _subdirectories

        # Test 
        runfolder = runfolder_svc.next_runfolder()
        expected = "ready: /var/local/arteria/mon1/runfolder001@localhost"
        self.assertEqual(str(runfolder), expected)

if __name__ == '__main__':
    unittest.main()
