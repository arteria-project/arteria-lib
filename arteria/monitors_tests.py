import unittest
from arteria_services import RunfolderMonitor

class DummyLogger:
    def debug(self, msg):
        print msg

    def info(self, msg):
        print msg

class DummyWorkflowService:
    def runfolder_ready(self, host, directory):
        print "runfolder_ready called for {0}@{1}".format(host, directory)
        if self.calls == None: self.calls = 0
        self.calls += 1

class DummyConfigurationService():
    def monitored_directories(self, host):
        print "monitored_directories"
        mountpoints = [
            "/home/stanley/arteria/monitored/mon1",
            "/home/stanley/arteria/monitored/mon2" 
        ] 
        return mountpoints

class RunfolderMonitorTestCase(unittest.TestCase):
    
    def test_runfolderavailable_valid_response(self):
        print "test..."
        workflow_service = DummyWorkflowService()
        configuration_service = DummyConfigurationService()
        runfolder_monitor = RunfolderMonitor("localhost", workflow_service,
            configuration_service, DummyLogger())
        runfolder_monitor.monitor()
        #print workflow_service.calls

if __name__ == '__main__':
    unittest.main()
