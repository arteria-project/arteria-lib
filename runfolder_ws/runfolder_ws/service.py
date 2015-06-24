import arteria.runfolder as runfolder
import tornado.ioloop
import tornado.web
import jsonpickle
from configuration import ConfigurationService
import os
import click
import sys

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
        global runfolder_svc
        runfolder_infos = list(runfolder_svc.list_available_runfolders())
        for runfolder_info in runfolder_infos:
            self.append_runfolder_link(runfolder_info)

        self.write_object(runfolder_infos)


class NextAvailableRunfolderHandler(BaseHandler):
    def get(self):
        runfolder_info = runfolder_svc.next_runfolder()
        self.append_runfolder_link(runfolder_info)
        self.write_object(runfolder_info)


class RunfolderHandler(BaseHandler):
    """Handles a particular runfolder"""

    def get(self, path):
        logger = runfolder.Logger()
        logger.debug("get " + path)
        global runfolder_svc
        runfolder_info = runfolder_svc.get_runfolder_by_path(path)
        self.append_runfolder_link(runfolder_info)
        self.write_object(runfolder_info)

    def post(self, path):
        logger = runfolder.Logger()
        logger.debug("post " + path)
        global runfolder_svc
        runfolder_svc.set_runfolder_state(path, "TODO")

    def put(self, path):
        """NOTE: put is provided for test purposes only. TODO: Discuss if
        it should be disabled in production"""
        global runfolder_svc
        runfolder_svc.create_runfolder(path)

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

class TestFakeSequencerReadyHandler(BaseHandler):
    def put(self, path):
        global runfolder_svc
        runfolder_svc.add_sequencing_finished_marker(path)

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
            ApiHelpEntry("/runfolders/path/full_path_here",
                         "Returns information about the runfolder at the path. The path must be monitored"),
        ]
        self.write_object(doc)

def create_app(debug):
    app = tornado.web.Application([
        (r"/api/1.0", ApiHelpHandler),
        (r"/api/1.0/runfolders", ListAvailableRunfoldersHandler),
        (r"/api/1.0/runfolders/next", NextAvailableRunfolderHandler),
        (r"/api/1.0/runfolders/path(/.*)", RunfolderHandler),

        (r"/api/1.0/runfolders/test/markasready/path(/.*)", TestFakeSequencerReadyHandler)
    ],
        debug=debug)
    return app

@click.command()
@click.option('--config', default="./runfolder.config")
@click.option('--debug/--no-debug', default=False)
@click.option('--create_config', default="")
def start(config, debug, create_config):
    global runfolder_svc

    if create_config:
        _create_config(create_config)
        return

    if not os.path.isfile(config):
        raise Exception("Can't open config file '{0}'".format(config))

    config_svc = ConfigurationService(config)
    runfolder_svc = runfolder.RunfolderService(config_svc)
    logger = runfolder.Logger()
    logger.info("Starting the runfolder micro service on {0} (debug={1})"
                .format(config_svc.port(), debug))
    app = create_app(debug)
    app.listen(config_svc.port())
    tornado.ioloop.IOLoop.current().start()

def _create_config(path):
    from configuration import ConfigurationFile
    dirs = ['/data/testtank1/mon1', '/data/testtank1/mon2']
    config_file = ConfigurationFile(dirs, 10080)
    ConfigurationFile.write(path, config_file)
    print "Created default config file at {0}".format(path)

if __name__ == "__main__":
    start()
