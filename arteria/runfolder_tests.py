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

    def test_runfolderavailable_valid_response(self):
        logger = Logger()
        configuration_svc = ConfigurationService()
        workflow_svc = WorkflowService(configuration_svc, logger)
        runfolder_ready = MagicMock()
        workflow_svc.runfolder_ready = runfolder_ready 
        filesystem_svc = FilesystemService()
        filesystem_svc.exists = self._valid_runfolder

        runfolder_monitor = RunfolderMonitor("localhost", workflow_svc,
            configuration_svc, filesystem_svc, logger)
        runfolder_monitor.monitor()

        expected_calls = [call('localhost', '/home/stanley/arteria/monitored/mon1'), 
                          call('localhost', '/home/stanley/arteria/monitored/mon2')]

        runfolder_ready.assert_has_calls(expected_calls)

if __name__ == '__main__':
    unittest.main()
