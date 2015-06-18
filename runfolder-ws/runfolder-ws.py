import arteria.runfolder as runfolder
import tornado.ioloop
import tornado.web
import sys
import jsonpickle

class BaseHandler(tornado.web.RequestHandler):
    def write_object(self, obj):
        resp = jsonpickle.encode(obj, unpicklable=False)
        self.write_json(resp)

    def write_json(self, json):
        self.set_header("Content-Type", "application/json")
        self.write(json) 

    def append_runfolder_link(self, runfolder_info):
        runfolder_info.link = self.create_runfolder_link(runfolder_info.path) 

    def create_runfolder_link(self, path):
        return "%s/runfolders/path%s" % (
               self.api_link(), path)

    def api_link(self, version="1.0"):
        return "%s://%s/api/%s" % (self.request.protocol, self.request.host, version) 

class ListAvailableRunfoldersHandler(BaseHandler):
    def get(self):
        monitor = runfolder.RunfolderService()
        runfolder_infos = list(monitor.list_available_runfolders())
        for runfolder_info in runfolder_infos:
            self.append_runfolder_link(runfolder_info)

        self.write_object(runfolder_infos)

class NextAvailableRunfolderHandler(BaseHandler):
    def get(self):
        monitor = runfolder.RunfolderService()
        runfolder_info = monitor.next_runfolder()
        self.append_runfolder_link(runfolder_info)
        self.write_object(runfolder_info)

class RunfolderHandler(BaseHandler):
    """Handles a particular runfolder"""
    def get(self, path):
        logger = runfolder.Logger()
        logger.debug("get " + path)
        monitor = runfolder.RunfolderService()
        runfolder_info = monitor.get_by_path(path)
        self.append_runfolder_link(runfolder_info)
        self.write_object(runfolder_info)

    def post(self, path):
        logger = runfolder.Logger()
        logger.debug("post " + path)
        monitor = runfolder.RunfolderService()
        monitor.set_runfolder_state(path, "TODO")

class ApiHelpEntry():
    def __init__(self, link, description):
        self.link = self.prefix + link
        self.description = description 

class ApiHelpHandler(BaseHandler):
    def get(self):
        ApiHelpEntry.prefix = self.api_link() 
        doc = [ 
            ApiHelpEntry("/runfolders", "Lists all runfolders"),
            ApiHelpEntry("/runfolders/next", "Return next runfolder to process"),
            ApiHelpEntry("/runfolders/path/fullpathhere", 
                         "Returns information about the runfolder at the path. The path must be monitored"),
        ]
        self.write_object(doc)

def create_app(debug):
    app = tornado.web.Application([
            (r"/api/1.0", ApiHelpHandler),
            (r"/api/1.0/runfolders", ListAvailableRunfoldersHandler),
            (r"/api/1.0/runfolders/next", NextAvailableRunfolderHandler),
            (r"/api/1.0/runfolders/path(/.*)", RunfolderHandler),
        ],
        debug=debug)
    return app

if __name__ == "__main__":
    if len(sys.argv) > 1:
        debug = sys.argv[1] == "debug"
    else:
        debug = False

    logger = runfolder.Logger()
    configuration_svc = runfolder.ConfigurationService()
    port = configuration_svc.runfolder_service_port() 
    logger.info("Starting the runfolder micro service on {0} (debug={1})"
                .format(port, debug))
    app = create_app(debug)
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
