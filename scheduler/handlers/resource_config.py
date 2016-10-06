import os
import tornado.web
import urllib

import logging
#logger = logging.getLogger(__name__)

import tpa.tpa as tpa
import core.config.resource.parser as parser

class Handler(tornado.web.RequestHandler):
    def get(self, param):
        config_filename = urllib.unquote(param)
        config_path = tpa.get_resource_configuration_path(config_filename)
        if config_path:
            data = parser.parse_resource_configuration_file(config_path)
            if data:
                self.render('resource_config.html', config=data)
            else:
                self.render('error.html', message="Failed to parse resource configuration file '{}'.".format(config_path))
        else:
            self.render('error.html', message="Failed to get resource configuration path for '{}'.".format(config_filename))

