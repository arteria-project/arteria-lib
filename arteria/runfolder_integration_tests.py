import unittest
from runfolder import * 
from mock import MagicMock, call

class RunfolderStackstormIntegrationTest(unittest.TestCase):
    
    def test_can_push_to_webhook(self):
        # TODO: Integrate against the test instance
        logger = Logger()
        configuration_svc = ConfigurationService()
        configuration_svc.runfolder_ready_webhook = lambda: "http://google.com"
        workflow_svc = WorkflowService(configuration_svc, logger)
        ret = workflow_svc.runfolder_ready("localhost", "/home/stanley/arteria/monitored/mon1")
        self.assertEqual(ret, 200)

if __name__ == '__main__':
    unittest.main()
