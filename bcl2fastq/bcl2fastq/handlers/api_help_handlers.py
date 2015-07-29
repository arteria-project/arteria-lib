
from handlers.base_handler import BaseHandler

class ApiHelpEntry():
    def __init__(self, link, description):
        self.link = self.prefix + link
        self.description = description

class ApiHelpHandler(BaseHandler):
    def get(self):
        ApiHelpEntry.prefix = self.api_link()
        doc = [
            ApiHelpEntry("/versions", "Lists available version of bcl2fastq"),
            ApiHelpEntry("/start/<runfolder>", "Starts a the specified runfolder. Specify arguments in body."
                                               "Will return job_id and endpoint to query for status."),
            ApiHelpEntry("/stop/<job_id | all>", "Stop the job with id <job_id>, or all jobs if 'all' is specified."),
            ApiHelpEntry("/status/<optional: job_id>", "If no job_id is specified, it will return the status"
                                                       "of all jobs, otherwise the status of the job with id: job_id"),
        ]
        self.write_object(doc)