import tornado.web
import jsonpickle
import re
import threading
import logging
import logging.config
import os
from .configuration import ConfigurationService
import itertools

def undocumented(f):
    """
    Apply the undocumented decorator to handler methods if they should not turn up in the API help
    """
    f.undocumented = True
    return f


class RouteProvider:
    def __init__(self, routes, app_svc, debug):
        """
        Initialize with routes

        :param routes: A list of tuples with tornado routing definitions
        :param debug: True if debugging
        """
        self._app_svc = app_svc
        self._debug = debug
        self._routes = routes
        self._routes.extend(self._get_default_routes(self))
        self._help_generated_lock = threading.Lock()
        self._help_generated = False

    def _doc_string_from_class_attribute(self, cls, attr_name):
        """
        Returns the doc string for the attribute

        Ignores the documentation if it has the undocumented attribute
        and is not running in debug mode
        """
        attr = getattr(cls, attr_name)
        doc = attr.__doc__
        is_undocumented = hasattr(attr, "undocumented")
        if doc is not None and (not is_undocumented or self._debug):
            doc = doc.strip()
            doc = re.sub(r'\s+', ' ', doc)
            if is_undocumented:
                doc = "(UNDOCUMENTED): {0}".format(doc)
            return doc

    def _get_route_infos_grouped(self, tornado_routes, base_url):
        """Returns the route infos grouped by route"""
        route_infos = list(self._get_route_infos(tornado_routes, base_url))
        grouped = itertools.groupby(route_infos, lambda entry: entry.route)
        routes = []
        for key, groups in grouped:
            route_info = {"route": key}
            methods = []
            for group in groups:
                method = dict()
                method[group.method] = group.description
                methods.append(method)
            route_info["methods"] = methods
            routes.append(route_info)
        return routes

    def _get_route_infos(self, tornado_routes, base_url):
        for tornado_route in tornado_routes:
            route = tornado_route[0]
            cls = tornado_route[1]
            for method_name in "get", "post", "put", "delete":
                doc = self._doc_string_from_class_attribute(cls, method_name)
                if doc is not None:
                    yield RouteInfo("{0}{1}".format(base_url, route), method_name, doc)

    def get_routes(self):
        return self._routes

    def _map_to_help_entry(self, raw_entry, base_url):
        route = raw_entry[2] if len(raw_entry) > 2 else raw_entry[0][0]
        route = "{0}{1}".format(base_url, route)
        return {"route": route, "description": raw_entry[1]}

    def _generate_help(self, force, base_url):
        """Generates help from self._routes"""
        if not self._help_generated or force:
            with self._help_generated_lock:
                if not self._help_generated:
                    self._route_infos = self._get_route_infos_grouped(self._routes, base_url)
                    self._help_generated = True
        return self._route_infos

    def get_help(self, base_url):
        return self._generate_help(True, base_url)

    def _get_default_routes(self, route_provider):
        """
        Gets the default endpoints for a web service in the Arteria project
        """
        return [
            (r"/api", ApiHelpHandler, dict(route_provider=route_provider)),
            (r"/api/1.0/admin/log_level", LogLevelHandler, dict(app_svc=self._app_svc))
        ]


class AppService:
    """Core functionality for the application, such as logging support"""

    def __init__(self, config_svc, debug, logger=None):
        """Sets up the admin service and configures logging"""
        self.config_svc = config_svc
        self._debug = debug

        # Initialize the logger configuration:
        self._logger_config = config_svc.get_logger_config()
        logging.config.dictConfig(self._logger_config)

        self._logger = logger or logging.getLogger(__name__)
        self._logger.info("Logger initialized by AppService")
        self._tornado = None

    @staticmethod
    def create(product_name, config_root, debug):
        """
        Creates the default app service and related services with defaults
        based on the product_name

        Log files will be available under /opt/<product_name>/etc by default

        :param product_name: The name of the product
        """
        if not config_root:
            config_root = os.path.join("/opt", product_name, "etc")

        logger_config_path = os.path.join(config_root, "logger.config")
        app_config_path = os.path.join(config_root, "app.config")
        config_svc = ConfigurationService(logger_config_path=logger_config_path,
                                          app_config_path=app_config_path)
        app_svc = AppService(config_svc, debug)
        return app_svc

    def start(self, routes):
        route_provider = RouteProvider(routes, self, self._debug)
        self._tornado = tornado.web.Application(route_provider.get_routes(), debug=self._debug)
        self._logger.info("Starting the service on {0} (debug={1})"
                          .format(self.config_svc["port"], self._debug))
        self._tornado.listen(self.config_svc["port"])
        tornado.ioloop.IOLoop.current().start()

    def set_log_level(self, log_level):
        # TODO: Directly change via logging module if possible
        self._logger_config["handlers"]["file_handler"]["level"] = log_level
        logging.config.dictConfig(self._logger_config)

    def get_log_level(self):
        return self._logger_config["handlers"]["file_handler"]["level"]

class RouteInfo:
    def __init__(self, route, method, description):
        self.route = route
        self.method = method
        self.description = description

    def __repr__(self):
        return "[{0} method={1}: {2}]".format(self.route, self.method, self.description)

class BaseRestHandler(tornado.web.RequestHandler):
    """
    A request handler for a REST web interface, taking care of
    writing and reading JSON request/responses
    """

    def data_received(self, chunk):
        pass

    def write_object(self, obj):
        resp = jsonpickle.encode(obj, unpicklable=False)
        self.write_json(resp)

    def write_json(self, json):
        self.set_header("Content-Type", "application/json")
        self.write(json)

    def body_as_object(self, required_members=[]):
        """Returns the JSON encoded body as a Python object"""
        obj = jsonpickle.decode(self.request.body)
        for member in required_members:
            if member not in obj:
                raise tornado.web.HTTPError("400", "Expecting '{0}' in the JSON body".format(member))
        return obj

    def api_link(self, version="1.0"):
        return "%s://%s/api/%s" % (self.request.protocol, self.request.host, version)

class LogLevelHandler(BaseRestHandler):
    """
    Handles getting/setting the log_level of the running application
    """
    def initialize(self, app_svc):
        self.app_svc = app_svc

    def get(self):
        """
        Get the current log_level of the running server
        """
        log_level = self.app_svc.get_log_level()
        self.write_object({"log_level": log_level})

    def put(self):
        """
        Set the current log_level of the running server. Call with e.g. {'log_level': 'DEBUG'}
        """
        json_body = self.body_as_object(["log_level"])
        log_level = json_body["log_level"]
        self.app_svc.set_log_level(log_level)
        self.write_object({"log_level": log_level})

class ApiHelpHandler(BaseRestHandler):
    """
    Handles requests for the api help, available at the root of the application
    """
    def initialize(self, route_provider):
        self.route_provider = route_provider

    def get(self):
        """Returns the help for the API"""
        base_url = "{0}://{1}".format(self.request.protocol, self.request.host)
        help_doc = self.route_provider.get_help(base_url)
        self.write_object(help_doc)
