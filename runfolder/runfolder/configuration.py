import jsonpickle
import logging

class ConfigurationService:

    def __init__(self, path, logger=None):
        self._config_loaded = False
        self._path = path
        self._logger = logger or logging.getLogger(__name__)

    def _load_config_file(self, from_cache=True):
        if not self._config_loaded or not from_cache:
            self._config_file = ConfigurationFile.read(self._path)
            self._logger.info("Read config file from {0}".format(self._path))
        self._config_loaded = True

    def port(self):
        self._load_config_file()
        return self._config_file["port"]

    def monitored_directories(self, host):
        self._load_config_file()
        return self._config_file["monitored_directories"]


class ConfigurationFile:
    """Represents a json serialized configuration file with key-value pairs"""
    def __init__(self):
        pass

    @staticmethod
    def read(path):
        with open(path, 'r') as f:
            json = f.read()
            return jsonpickle.decode(json)

    @staticmethod
    def write(path, obj):
        jsonpickle.set_encoder_options(
            'simplejson', sort_keys=True, indent=4)
        with open(path, 'w') as f:
            json = jsonpickle.encode(obj, unpicklable=False)
            f.write(json)
