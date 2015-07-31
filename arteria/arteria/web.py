import tornado.web
import jsonpickle

class TornadoAppFactory:
    """
    Helpers for a Tornado app
    """
    @staticmethod
    def create_app(debug, routes_with_help):
        """Creates a web app for serving the REST endpoints, adding defaults for administration"""
        route_provider = RouteProvider(routes_with_help)
        app = tornado.web.Application(route_provider.get_endpoints(), debug=debug)
        return app

class RouteProvider:
    def __init__(self, routes_with_help):
        """
        Initialize with routes and related help

        :param routes_with_help: A list of tuples with tornado routing definitions as first elements
        and a help string as the second
        """
        self._routes_with_help = routes_with_help
        self._routes_with_help.extend(self._get_default_routes(self))

    def get_endpoints(self):
        endpoints = [entry[0] for entry in self._routes_with_help]
        return endpoints

    def _map_to_help_entry(self, raw_entry, base_url):
        route = raw_entry[2] if len(raw_entry) > 2 else raw_entry[0][0]
        route = "{0}{1}".format(base_url, route)
        return {"route": route, "description": raw_entry[1]}

    def get_help(self, base_url):
        mapped = (self._map_to_help_entry(entry, base_url) for entry in self._routes_with_help)
        filtered = (entry for entry in mapped if entry["description"] is not None)
        help_doc = sorted(filtered, key=lambda entry: entry["route"])
        return help_doc

    def _get_default_routes(self, route_provider):
        """
        Gets the default endpoints for a web service in the Arteria project
        """
        return [
            (
                (r"/api", ApiHelpHandler, dict(route_provider=route_provider)),
                "Provides this help listing"
            ),
            (
                (r"/api/1.0/admin/log_level", LogLevelHandler),
                "Put {log_level: new_level} to update the log_level for the lifetime of the process"
            )
        ]

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
    def get(self):
        log_level = self.admin_svc.get_log_level()
        self.write_object({"log_level": log_level})

    def put(self):
        json_body = self.body_as_object(["log_level"])
        log_level = json_body["log_level"]
        self.admin_svc.set_log_level(log_level)
        self.write_object({"log_level": log_level})

class ApiHelpHandler(BaseRestHandler):
    """
    Handles requests for the api help, available at the root of the application
    """
    def initialize(self, route_provider):
        self.route_provider = route_provider

    def get(self):
        base_url = "{0}://{1}".format(self.request.protocol, self.request.host)
        help_doc = self.route_provider.get_help(base_url)
        self.write_object(help_doc)
