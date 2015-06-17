class ConfigurationService():

    def __init__(self):
        pass

    # TODO: Have this get from yaml file
    def runfolder_service_port(self):
        return 10800

    def runfolder_ready_webhook(self):
        return "http://google.com"

    def runfolder_heartbeat(self):
        """The time to wait in seconds between invidual monitor runs"""
        return 10

    def monitored_directories(self, host):
        #self._logger.debug("Fetching monitored_directories from config")        
        # TODO: get from yaml
        return ["/var/local/arteria/mon1", "/var/local/arteria/mon2"]

