import tornado.web
import logging
import logging.config
import os
from arteria.configuration import ConfigurationService
from arteria.web.routes import RouteService
from arteria.web.handlers import LogLevelHandler, ApiHelpHandler


class AppService:
    """
    Core functionality for the application.

    Automatically sets up logging, given a config_svc that serves a logging config

    Usage example:
        # Set up using the factory method, which provides default location of
        # config files:
        app_svc = AppService.create("product_name", debug=True)

        # This sets up the service reading config files from:
        #  - /opt/product_name/etc/app.config
        #  - /opt/product_name/etc/logger.config

        # Set up Tornado routes
        args = dict(service1=Service1(), service2=Service2())
        routes = [
            (r"/api/1.0/endpoint1", Handler1, args),
            (r"/api/1.0/endpoint2", Handler2, args)
        ]

        app_svc.start(routes)
    """

    def __init__(self, config_svc, debug, port, logger=None):
        """Sets up the admin service and configures logging"""
        self.config_svc = config_svc
        self.route_svc = RouteService(self, debug)
        self._debug = debug

        if not port or (not type(port) is int):
            raise InvalidPortError("Invalid port: '{port}'".format(port=port))
        self._port = port

        # Initialize the logger configuration:
        self._logger_config = config_svc.get_logger_config()
        logging.config.dictConfig(self._logger_config)

        self._logger = logger or logging.getLogger(__name__)
        self._logger.info("Logger initialized by AppService")
        self._tornado = None

    @staticmethod
    def create(product_name, config_root, debug, port):
        """
        Creates the default app service and related services with defaults
        based on the product_name

        These config files should be accessible:
            - /opt/<product_name>/app.config
            - /opt/<product_name>/logger.config

        You can override this by supplying config_root, in which case they should be
        found at <config_root>/*.config

        :param product_name: The name of the product
        :param config_root: Search for config files under <config_root>
            instead of /opt/<product_name>/etc
        :param debug: Set to true to run the application in debug mode. This affects
            how Tornado runs and how the route help is displayed
        """
        if not config_root:
            config_root = os.path.join("/opt", product_name, "etc")

        logger_config_path = os.path.join(config_root, "logger.config")
        app_config_path = os.path.join(config_root, "app.config")
        config_svc = ConfigurationService(logger_config_path=logger_config_path,
                                          app_config_path=app_config_path)
        app_svc = AppService(config_svc, debug, int(port))
        return app_svc

    def start(self, routes):
        # Add the default routes, such as the API handler
        routes.extend(self._get_default_routes())
        self.route_svc.set_routes(routes)
        self._tornado = tornado.web.Application(self.route_svc.get_routes(), debug=self._debug)
        self._logger.info("Starting the service on {0} (debug={1})"
                          .format(self._port, self._debug))
        self._tornado.listen(self._port)
        tornado.ioloop.IOLoop.current().start()

    def set_log_level(self, log_level):
        # TODO: Directly change via logging module if possible
        self._logger_config["handlers"]["file_handler"]["level"] = log_level
        logging.config.dictConfig(self._logger_config)

    def get_log_level(self):
        return self._logger_config["handlers"]["file_handler"]["level"]

    def _get_default_routes(self):
        """
        Gets the default endpoints for a web service in the Arteria project
        """
        return [
            (r"/api", ApiHelpHandler, dict(route_svc=self.route_svc)),
            (r"/api/1.0/admin/log_level", LogLevelHandler, dict(app_svc=self))
        ]

class InvalidPortError(Exception):
    pass
