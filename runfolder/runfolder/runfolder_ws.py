from .runfolder import *
from .admin import AdminService
from .configuration import ConfigurationService
import os
import click
import logging
from arteria.web import BaseRestHandler
import tornado.web
import arteria.web

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
    """List all available runfolders"""
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



class TestFakeSequencerReadyHandler(BaseRunfolderHandler):
    def put(self, path):
        self.runfolder_svc.add_sequencing_finished_marker(path)

def create_app(debug, args):
    # Define the endpoints as tuples expected by Tornado, but adding the help information:
    # If there is no help string (undocumented feature) it will not be shown in the help
    # A third entry in the tuple overrides the route in the help listing if provided

    endpoints = [
        (
            (r"/api/1.0/runfolders", ListAvailableRunfoldersHandler, args),
            "List all runfolders"
        ),
        (
            (r"/api/1.0/runfolders/next", NextAvailableRunfolderHandler, args),
            "Return the next runfolder to process"),
        (
            (r"/api/1.0/runfolders/path(/.*)", RunfolderHandler, args),
            "Returns information about the runfolder at the path. The path must be monitored",
            "/api/1.0/runfolders/path/root/monitored/directory"
        ),
        (
            (r"/api/1.0/runfolders/test/markasready/path(/.*)", TestFakeSequencerReadyHandler, args),
            None
        ),
    ]

    app = arteria.web.TornadoAppFactory.create_app(debug, endpoints)
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
