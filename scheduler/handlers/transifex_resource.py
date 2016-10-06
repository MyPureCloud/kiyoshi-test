import os
import json
import urllib
import tornado.web

import logging
logger = logging.getLogger(__name__)

import tpa.tpa as tpa
import plugins.translation_repository.transifex.utils as transifex

class Handler(tornado.web.RequestHandler):
    def get(self, param):
        s = urllib.unquote(param)
        project_slug = s.split(':')[0]
        resource_slug = s.split(':')[1]
        project_name = s.split(':')[2]
        resource_name = s.split(':')[3]
        creds = tpa.get_transifex_creds()
        ret = transifex.query_source_strings_details(creds, project_slug, resource_slug)
        if ret.succeeded:
            strings = ret.output
        else:
            logger.error("query_source_strings_detail() failed. Reason: '{}'".format(ret.message))
            strings = []
        self.render('transifex_resource.html', project_name=project_name, resource_name=resource_name, strings=strings)

