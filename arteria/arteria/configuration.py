import logging
import yaml
import threading

class ConfigurationService:
    def __init__(self, logger=None, logger_config_path=None, app_config_path=None):
        self._logger = logger or logging.getLogger(__name__)
        self._logger_config_path = logger_config_path
        self._app_config_path = app_config_path
        self._cache_lock = threading.Lock()
        self._cache = {}

    def _load_config_file(self, path, from_cache=True):
        needs_cache = lambda: not from_cache or (path not in self._cache)
        if needs_cache():
            # TODO: Code review threading code
            with self._cache_lock:
                if needs_cache():
                    config_file = ConfigurationService.read_yaml(path)
                    self._cache[path] = config_file
                    self._logger.info("Read config file from {0}, format={1}, from_cache={2}"
                                      .format(path, format, from_cache))
        return self._cache[path]

    def get_app_config(self):
        return self._load_config_file(self._app_config_path)

    def get_logger_config(self):
        return self._load_config_file(self._logger_config_path)

    def __getitem__(self, key):
        """Returns the value for the key from the app config"""
        app_config = self.get_app_config()
        return app_config[key]

    @staticmethod
    def read_yaml(path):
        with open(path, 'r') as f:
            config = yaml.load(f.read())
            return config
