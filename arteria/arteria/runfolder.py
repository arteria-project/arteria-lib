import os.path
from .logging import Logger
import socket


class RunfolderInfo:
    """Information about a runfolder. Status can be:
            none: Not ready for processing or invalid
            ready: Ready for processing by Arteria
            started: Arteria started processing the runfolder
            done: Arteria is done processing the runfolder
            error: Arteria started processing the runfolder but there was an error
    """

    STATE_NONE = "none"
    STATE_READY = "ready"
    STATE_STARTED = "started"
    STATE_DONE = "done"
    STATE_ERROR = "error"

    def __init__(self, host, path, state):
        self.host = host
        self.path = path
        self.state = state

    def __str__(self):
        return "{0}: {1}@{2}".format(self.state, self.path, self.host)

class RunfolderService:
    """Watches a set of directories on the server and reacts when one of them
       has a runfolder that's ready for processing

       configuration_svc must provide monitored_directories(host_name)
       """

    def __init__(self,
                 configuration_svc,
                 logger=Logger()):
        self._configuration_svc = configuration_svc
        self._logger = logger

    # NOTE: These methods were added so that they could be easily mocked out.
    #       It would probably be nicer to move them inline and mock the system calls
    #       or have them in a separate provider class required in the constructor
    @staticmethod
    def _host():
        return socket.gethostname()

    @staticmethod
    def _file_exists(path):
        return os.path.isfile(path)

    @staticmethod
    def _dir_exists(path):
        return os.path.isdir(path)

    @staticmethod
    def _subdirectories(path):
        return os.listdir(path)

    def validate_is_being_monitored(self, path):
        """Validate that this is a subdirectory (potentially non-existing)
         of a monitored path"""
        monitored = any([path.startswith(mon) for mon in self._monitored_directories()])
        if not monitored:
            raise Exception("The path {0} is not being monitored".format(path))

    def create_runfolder(self, path):
        """Provided for integration tests only.
        Creates a runfolder at the path."""
        self.validate_is_being_monitored(path)
        if os.path.exists(path):
            raise Exception("The path {0} already exists and can't be overridden".format(path))
        os.makedirs(path)

    def add_sequencing_finished_marker(self, path):
        """Provided for integration tests only.
        Adds the marker that sets the `ready` state of a runfolder.
        This marker is generally added by the sequencer"""
        if not os.path.isdir(path):
            raise Exception("The path '{0}' is not an existing directory".format(path))

        fullpath = os.path.join(path, "RTAComplete.txt")
        if os.path.isfile(fullpath):
            raise Exception("The complete marker already exists at {0}".format(fullpath))

        open(fullpath, 'a').close()

    def get_runfolder_by_path(self, path):
        """Returns a RunfolderInfo by its Linux file path"""

        self._logger.debug("get_runfolder_by_path")
        self.validate_is_being_monitored(path)

        if not self._dir_exists(path):
            raise Exception("Directory does not exist: '{0}'".format(path))
        info = RunfolderInfo(self._host(), path, self.get_runfolder_state(path))
        return info

    def _get_runfolder_state_from_state_file(self, runfolder):
        """Reads the state in the state file at .arteria/state, returns
        RunfolderInfo.STATE_NONE if nothing is available """
        state_file = os.path.join(runfolder, ".arteria", "state")
        if self._file_exists(state_file):
            with open(state_file, 'r') as f:
                state = f.read()
                state = state.strip()
                return state
        else:
            return RunfolderInfo.STATE_NONE

    def get_runfolder_state(self, runfolder):
        """Returns the state of a runfolder. The possible states are defined in
        RunfolderInfo.STATE_*.

        If the file .arteria/state exists, it will determine the state. If it doesn't
        exist, the existence of the marker file RTAComplete.txt determines the state.
        """

        state = self._get_runfolder_state_from_state_file(runfolder)
        if state == RunfolderInfo.STATE_NONE:
            completed_marker = os.path.join(runfolder, "RTAComplete.txt")
            ready = self._file_exists(completed_marker)
            if ready:
                state = RunfolderInfo.STATE_READY

        return state

    @staticmethod
    def set_runfolder_state(runfolder, state):
        """Sets the state of a runfolder"""

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
        return self._configuration_svc.monitored_directories(self._host())

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
                state = self.get_runfolder_state(directory)
                if state == RunfolderInfo.STATE_READY:
                    info = RunfolderInfo(self._host(),
                                         directory, RunfolderInfo.STATE_READY)
                    yield info

        self._logger.debug("Done walking {0}".format(monitored_root))
