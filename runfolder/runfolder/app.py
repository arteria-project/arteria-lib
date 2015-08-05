import click
from arteria.web.app import AppService
from runfolder.handlers import *

@click.command()
@click.option('--product', default=__package__)
@click.option('--configroot')
@click.option('--debug/--no-debug', default=False)
def start(product, configroot, debug):
    app_svc = AppService.create(product, configroot, debug)
    runfolder_svc = RunfolderService(app_svc.config_svc)

    # Setup the routing. Help will be automatically available at /api, and will be based on
    # the doc strings of the get/post/put/delete methods
    args = dict(runfolder_svc=runfolder_svc, config_svc=app_svc.config_svc)
    routes = [
        (r"/api/1.0/runfolders", ListAvailableRunfoldersHandler, args),
        (r"/api/1.0/runfolders/next", NextAvailableRunfolderHandler, args),
        (r"/api/1.0/runfolders/path(/.*)", RunfolderHandler, args),
        (r"/api/1.0/runfolders/test/markasready/path(/.*)", TestFakeSequencerReadyHandler, args)
    ]
    app_svc.start(routes)

