import yaml
import logging
import logging.config

class AdminService:
    """Provides an API for the administration of the application"""

    def __init__(self, logger_config_path):
        """Sets up the admin service and configures logging"""
        self._logger_config_path = logger_config_path
        self._config = self._get_config(self._logger_config_path)
        logging.config.dictConfig(self._config)

    def set_log_level(self, log_level):
        # TODO: Directly change via logging module if possible
        self._config["handlers"]["file_handler"]["level"] = log_level
        logging.config.dictConfig(self._config)

    def get_log_level(self):
        return self._config["handlers"]["file_handler"]["level"]

    @staticmethod
    def _get_config(path):
        with open(path, 'r') as f:
            config = yaml.load(f.read())
            print "Loaded logging config:", config
            return config
