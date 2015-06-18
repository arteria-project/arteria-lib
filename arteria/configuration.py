import sys
import os
import jsonpickle

class ConfigurationService():

    def __init__(self):
        self._config_loaded = False

    def _load_config_file(self, from_cache=True):
        # TODO: Read everything from config file
        if not self._config_loaded or not from_cache:
            path = "/etc/opt/arteria-lib/runfolder-ws/runfolder.config"
            self._config_file = ConfigurationFile.read(path)
            print "Read config file from {0}".format(path)
        self._config_loaded = True

    def runfolder_service_port(self):
        return 10800

    def runfolder_ready_webhook(self):
        return "http://google.com"

    def runfolder_heartbeat(self):
        """The time to wait in seconds between invidual monitor runs"""
        return 10

    def monitored_directories(self, host):
        self._load_config_file()
        return self._config_file.monitored_directories


class ConfigurationFile():
    def __init__(self, monitored_directories):
        self.monitored_directories = monitored_directories

    @staticmethod
    def read(path):
        with open(path, 'r') as f:
            json = f.read()
            return jsonpickle.decode(json)

    @staticmethod
    def write(path, obj):
        jsonpickle.set_encoder_options('simplejson', sort_keys=True, indent=4)
        with open(path, 'w') as f:
            json = jsonpickle.encode(obj)
            f.write(json)
