import time
import os.path
import requests

class HostProvider:
    def host(self):
        return "localhost"

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

class ConfigurationService():
    # TODO: Have this get from yaml file
    def runfolder_service_port(self):
        return 10800

    def runfolder_ready_webhook(self):
        return "http://google.com"

    def runfolder_heartbeat(self):
        """The time to wait in seconds between invidual monitor runs"""
        return 10

    def monitored_directories(self, host):
        # TODO: get from yaml
        return ["/var/local/arteria/mon1", "/var/local/arteria/mon2"]

class RunfolderInfo():
    """Information about a runfolder. Status can be:
            none: Not ready for processing or invalid
            ready: Ready for processing by Arteria
            started: Arteria started processing the runfolder
            done: Arteria is done processing the runfolder
            error: Arteria started processing the runfolder but there was an error
    """

    STATE_NONE    = "none"
    STATE_READY   = "ready"
    STATE_STARTED = "started"
    STATE_DONE    = "done"
    STATE_ERROR   = "error"

    def __init__(self, host, path, state):
        self.host = host
        self.path = path
        self.state = state 

    def __str__(self):
        return "{0}: {1}@{2}".format(self.state, self.path, self.host)

class RunfolderService():
    """Watches a set of directories on the server and reacts when one of them 
       has a runfolder that's ready for processing"""

    def __init__(self, 
                 configuration_svc=ConfigurationService(), 
                 host_provider=HostProvider(),
                 logger=Logger()):
        self._configuration_svc = configuration_svc
        self._host_provider = host_provider
        self._logger = logger

    def _file_exists(self, path):
        return os.path.isfile(path)

    def _dir_exists(self, path):
        return os.path.isdir(path)

    def _subdirectories(self, path):
        return os.listdir(path)

    def get_by_path(self, path):
        self._logger.debug("get_by_path")
        # TODO: Validate that the path is actually being monitored
        if not self._dir_exists(path):
            raise Exception("Directory does not exist: '{0}'".format(path)) 
        info = RunfolderInfo("host", path, self.get_runfolder_state(path)) 
        return info
        
    def _get_runfolder_state_from_state_file(self, runfolder):
        state_file = os.path.join(runfolder, ".arteria/state")
        if self._file_exists(state_file):
            with open(state_file, 'r') as f:
                state = f.read()
                return state
        else:
            return RunfolderInfo.STATE_NONE

    def get_runfolder_state(self, runfolder):
        # If there exists a state file, it defines the state, otherwise
        # it's the existence of a marker from a sequencer
        state = self._get_runfolder_state_from_state_file(runfolder)  
        if state == RunfolderInfo.STATE_NONE:
            completed_marker = os.path.join(runfolder, "RTAComplete.txt")
            ready = self._file_exists(completed_marker)
            if ready:
                state = RunfolderInfo.STATE_READY 

        return state

    def set_runfolder_state(self, runfolder, state):
        arteria_dir = os.path.join(runfolder, ".arteria")
        state_file = os.path.join(arteria_dir, "state")
        if not os.path.exists(arteria_dir):
            os.makedirs(arteria_dir)
        with open(state_file, 'w') as f:
            f.write(state)
        
    def is_runfolder_ready(self, directory):
        state = self.get_runfolder_state(directory)
        self._logger.debug("Checking {0}. state={1}".format(directory, state))
        return state == RunfolderInfo.STATE_READY

    def _monitored_directories(self):
        return self._configuration_svc.monitored_directories(self._host_provider.host())

    def next_runfolder(self):
        """Pulls for available run folders"""
        self._logger.info("Searching for next available runfolder")
        available = self.list_available_runfolders()
        try:
            return available.next()
        except StopIteration:
            return None

    def list_available_runfolders(self):
        """Lists all the available runfolders on the host"""
        self._logger.debug("get_available_runfolder")
        for monitored_root in self._monitored_directories():
            self._logger.debug("Checking subdirectories of {0}".format(monitored_root))
            for subdir in self._subdirectories(monitored_root):
                directory = os.path.join(monitored_root, subdir)
                self._logger.debug("Found potential runfolder {0}".format(directory))
                if self.is_runfolder_ready(directory):
                    info = RunfolderInfo(self._host_provider.host(),
                                         directory, RunfolderInfo.STATE_READY)
                    yield info

        self._logger.debug("Done walking {0}".format(monitored_root))
