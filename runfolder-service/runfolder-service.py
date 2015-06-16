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
        return "%s://%s/api/1.0/runfolders/path%s" % (
               self.request.protocol, self.request.host, path)

class ListAvailableRunfoldersHandler(BaseHandler):
    def get(self):
        monitor = runfolder.RunfolderMonitor()
        runfolder_infos = list(monitor.list_runfolders(self.request.remote_ip))
        for runfolder_info in runfolder_infos:
            self.append_runfolder_link(runfolder_info)

        self.write_object(runfolder_infos)

class NextAvailableRunfolderHandler(BaseHandler):
    def get(self):
        monitor = runfolder.RunfolderMonitor()
        runfolder_info = monitor.next_runfolder(self.request.remote_ip)
        self.append_runfolder_link(runfolder_info)
        self.write_object(runfolder_info)

class RunfolderHandler(BaseHandler):
    """Handles a particular runfolder"""
    def get(self, path):
        logger = runfolder.Logger()
        logger.debug("get " + path)
        # TODO: Rename the monitor class to something more general 
        monitor = runfolder.RunfolderMonitor()
        ret = monitor.get_by_path(path)
        self.write_object(ret)

    def post(self, path):
        logger = runfolder.Logger()
        logger.debug("post " + path)
        monitor = runfolder.RunfolderMonitor()
        monitor.set_runfolder_state(path, "TODO")

def create_app(debug):
    app = tornado.web.Application([
            (r"/api/1.0/runfolders/list", ListAvailableRunfoldersHandler),
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
    host_provider = runfolder.HostProvider()
    port = configuration_svc.runfolder_service_port() 
    logger.info("Starting the runfolder micro service on {0}:{1} (debug={2})"
                .format(host_provider.host(), port, debug))
    app = create_app(debug)
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
