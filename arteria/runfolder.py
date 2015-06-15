import time
import os.path
import requests

class Logger:

    def debug(self, msg):
        print msg 

    def info(self, msg):
        print msg

    def warn(self, msg):
        print msg

    def error(self, msg):
        print msg

class WorkflowService:
    """Represents the workflow service that will do work on the runfolder"""

    def __init__(self, configuration_svc, logger):
        self._configuration_svc = configuration_svc
        self._logger = logger        

    def runfolder_ready(self, host, directory):
        self._logger.info("runfolder_ready called for {0}@{1}".format(host, directory))
        url = self._configuration_svc.runfolder_ready_webhook()
        resp = requests.get(url)
        if resp.status_code == 200:
            self._logger.info("Successfully pushed runfolder_ready signal to workflow service")
        else:
            self._logger.error(
                "Not able to push runfolder_ready signal to workflow service at {0}. Exit code {1}"
                    .format(url, resp.status_code))
        return resp.status_code

class FilesystemService():

    def exists(self, path):
        return os.path.isfile(path)

class ConfigurationService():

    def runfolder_ready_webhook(self):
        return "http://google.com"

    def runfolder_heartbeat(self):
        """The time to wait in seconds between invidual monitor runs"""
        return 10

    def monitored_directories(self, host):
        print "monitored_directories"
        mountpoints = [
            "/home/stanley/arteria/monitored/mon1",
            "/home/stanley/arteria/monitored/mon2" 
        ]
        return mountpoints

# TODO: The filename will be changed to something else
class RunfolderMonitor():
    """Watches a set of directories on the server and reacts when one of them 
       has a runfolder that's ready for processing"""

    def __init__(self, host, workflow_service, configuration_service, 
                 filesystem_service, logger):
        self._logger = logger
        self._workflow_service = workflow_service
        self._configuration_service = configuration_service
        self._host = host
        self._filesystem_service = filesystem_service

    def run_scheduler(self):
        """Starts the runfolder thread, executing the monitor regularly"""
        self._logger.info("Running the runfolder scheduler.")
        sleep_interval = self._configuration_service.runfolder_heartbeat()
        while True:
            self.monitor()
            sleep(sleep_interval)

    def monitor(self):
        """Checks if the runfolder is ready, and if so, pings the workflow service"""
        self._logger.debug("monitor")
        self.get_available_runfolder()

    def is_runfolder_ready(self, directory):
        already_processed_marker = os.path.join(directory, ".arteria/state")
        already_processed = self._filesystem_service.exists(already_processed_marker)
        complete_marker = os.path.join(directory, "RTAComplete.txt")
        completed = self._filesystem_service.exists(complete_marker)
        
        return (not already_processed and completed)

    def _monitored_directories(self):
        return self._configuration_service.monitored_directories(self._host)

    def get_available_runfolder(self):
        """Checks for an available runfolder on the host"""
        self._logger.debug("get_available_runfolder")
        for directory in self._monitored_directories():
            self._logger.debug("Checking {0}".format(directory))
            if self.is_runfolder_ready(directory):
                self._logger.debug("Runfolder is ready, pinging workflow service")
                self._workflow_service.runfolder_ready(self._host, directory)
