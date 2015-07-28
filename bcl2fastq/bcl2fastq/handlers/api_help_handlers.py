
from handlers.base_handler import BaseHandler

class ApiHelpEntry():
    def __init__(self, link, description):
        self.link = self.prefix + link
        self.description = description

class ApiHelpHandler(BaseHandler):
    def get(self):
        ApiHelpEntry.prefix = self.api_link()
        doc = [
            # TODO Use as template
            ApiHelpEntry("/runfolders", "Lists all runfolders"),
        ]
        self.write_object(doc)
