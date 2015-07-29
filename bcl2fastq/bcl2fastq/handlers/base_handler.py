
import jsonpickle
from tornado.web import RequestHandler

class BaseHandler(RequestHandler):
    def write_object(self, obj):
        resp = jsonpickle.encode(obj, unpicklable=False)
        self.write_json(resp)

    def write_json(self, json):
        self.set_header("Content-Type", "application/json")
        self.write(json)

    def api_link(self, version="1.0"):
        return "%s://%s/api/%s" % (self.request.protocol, self.request.host, version)