import time
import os.path

# TODO: The filename will be changed to something else
class RunfolderMonitor():
    """Watches a set of directories on the server and reacts when one of them 
       has a runfolder that's ready for processing
    """

    def __init__(self, host, workflow_service, configuration_service, logger):
        """..."""
        self._logger = logger
        self._workflow_service = workflow_service
        self._configuration_service = configuration_service
        self._host = host

    def _file_exists(self, fullpath):
        return True

    def run(self):
        """Starts the runfolder thread, executing the monitor regularly"""
        # TODO
        pass

    def monitor(self):
        """Checks if the runfolder is ready, and if so, pings the workflow service"""
        self._logger.debug("monitor")
        self.get_available_runfolder()

    def is_runfolder_ready(self, directory):
        already_processed_marker = os.path.join(directory, ".arteria/state")
        already_processed = self._file_exists(already_processed_marker)

        complete_marker = os.path.join(directory, "RTAComplete.txt")
        completed = self._file_exists(_host, complete_marker)
        
        if (not already_processed and completed):
            pass

    def _monitored_directories(self):
        return self._configuration_service.monitored_directories(self._host)

    def get_available_runfolder(self):
        """Checks for an available runfolder on the host"""
        self._logger.debug("get_available_runfolder")
        for directory in self._monitored_directories():
            if self.is_runfolder_ready(directory):
                self._workflow_service.runfolder_ready(self._host, directory)
