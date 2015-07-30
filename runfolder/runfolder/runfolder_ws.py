import tornado.ioloop
import tornado.web
import jsonpickle
from .runfolder import *
from .admin import AdminService
from .configuration import ConfigurationService
import os
import click
import logging

class BaseRestHandler(tornado.web.RequestHandler):
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
                raise tornado.web.HTTPError("400", "Expecting '{0}' in JSON body".format(member))
        return obj

    def api_link(self, version="1.0"):
        return "%s://%s/api/%s" % (self.request.protocol, self.request.host, version)

class BaseRunfolderHandler(BaseRestHandler):
    def append_runfolder_link(self, runfolder_info):
        runfolder_info.link = self.create_runfolder_link(runfolder_info.path)

    def create_runfolder_link(self, path):
        return "%s/runfolders/path%s" % (
            self.api_link(), path)

    def initialize(self, admin_svc, runfolder_svc, config_svc):
        self.admin_svc = admin_svc
        self.runfolder_svc = runfolder_svc
        self.config_svc = config_svc

class ListAvailableRunfoldersHandler(BaseRunfolderHandler):
    def get(self):
        runfolder_infos = list(self.runfolder_svc.list_available_runfolders())
        for runfolder_info in runfolder_infos:
            self.append_runfolder_link(runfolder_info)

        self.write_object(runfolder_infos)

class NextAvailableRunfolderHandler(BaseRunfolderHandler):
    def get(self):
        runfolder_info = self.runfolder_svc.next_runfolder()
        self.append_runfolder_link(runfolder_info)
        self.write_object(runfolder_info)

class LogLevelHandler(BaseRunfolderHandler):
    def get(self):
        log_level = self.admin_svc.get_log_level()
        self.write_object({"log_level": log_level})

    def put(self):
        json_body = self.body_as_object(["log_level"])
        log_level = json_body["log_level"]
        self.admin_svc.set_log_level(log_level)
        self.write_object({"log_level": log_level})

class RunfolderHandler(BaseRunfolderHandler):
    """Handles a particular runfolder"""

    def get(self, path):
        try:
            runfolder_info = self.runfolder_svc.get_runfolder_by_path(path)
            self.append_runfolder_link(runfolder_info)
            self.write_object(runfolder_info)
        except PathNotMonitored:
            raise tornado.web.HTTPError(400, "Searching an unmonitored path '{0}'".format(path))
        except DirectoryDoesNotExist:
            raise tornado.web.HTTPError(404, "Runfolder '{0}' does not exist".format(path))

    def post(self, path):
        self.runfolder_svc.set_runfolder_state(path, "TODO")

    def put(self, path):
        """NOTE: put is provided for test purposes only. TODO: Discuss if
        it should be disabled in production"""
        try:
            self.runfolder_svc.create_runfolder(path)
        except PathNotMonitored:
            raise tornado.web.HTTPError("400", "Path {0} is not monitored".format(path))


class ApiHelpEntry:
    def __init__(self, link, description):
        self.link = self.prefix + link
        self.description = description


class ApiHelpHandler(BaseRunfolderHandler):
    def get(self):
        ApiHelpEntry.prefix = self.api_link()
        doc = [
            # TODO: Define the help with the route
            ApiHelpEntry("/runfolders", "Lists all runfolders"),
            ApiHelpEntry("/runfolders/next", "Return next runfolder to process"),
            ApiHelpEntry("/runfolders/path/fullpathhere",
                         "Returns information about the runfolder at the path. The path must be monitored"),
            ApiHelpEntry("/admin/log_level",
                         "Put {log_level: new_level} to update the log_level for the lifetime of the process")
        ]
        self.write_object(doc)

class TestFakeSequencerReadyHandler(BaseRunfolderHandler):
    def put(self, path):
        self.runfolder_svc.add_sequencing_finished_marker(path)

class ApiHelpEntry():
    def __init__(self, link, description):
        self.link = self.prefix + link
        self.description = description

def create_app(debug, args):
    app = tornado.web.Application([
        (r"/api/1.0", ApiHelpHandler, args),
        (r"/api/1.0/runfolders", ListAvailableRunfoldersHandler, args),
        (r"/api/1.0/runfolders/next", NextAvailableRunfolderHandler, args),
        (r"/api/1.0/runfolders/path(/.*)", RunfolderHandler, args),
        (r"/api/1.0/runfolders/test/markasready/path(/.*)", TestFakeSequencerReadyHandler, args),
        (r"/api/1.0/admin/log_level", LogLevelHandler, args)
    ],
        debug=debug)
    return app

@click.command()
@click.option('--config', default="./runfolder.config")
@click.option('--loggerconfig', default="./logger.config")
@click.option('--debug/--no-debug', default=False)
@click.option('--create_config', default="")
def start(config, loggerconfig, debug, create_config):
    if create_config:
        _create_config(create_config)
        return

    if not os.path.isfile(config):
        raise Exception("Can't open config file '{0}'".format(config))

    admin_svc = AdminService(loggerconfig)
    config_svc = ConfigurationService(config)
    runfolder_svc = RunfolderService(config_svc)

    logger = logging.getLogger(__name__)
    logger.info("Starting the runfolder micro service on {0} (debug={1})"
                .format(config_svc.port(), debug))
    args = dict(runfolder_svc=runfolder_svc, admin_svc=admin_svc, config_svc=config_svc)
    app = create_app(debug, args)
    app.listen(config_svc.port())
    tornado.ioloop.IOLoop.current().start()

def _create_config(path):
    from configuration import ConfigurationFile
    dirs = ['/data/testarteria1/mon1', '/data/testarteria1/mon2']
    config_file = ConfigurationFile(dirs, 10800)
    ConfigurationFile.write(path, config_file)
    print "Created default config file at {0}".format(path)

if __name__ == "__main__":
    start()
