import os
import tornado.web

import tpa.tpa as tpa

class Handler(tornado.web.RequestHandler):
    def get(self):
        entries = tpa.get_resource_configurations_from_directory()
        self.render('resource_configs.html', configs=entries)

