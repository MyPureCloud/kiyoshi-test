import os
import json
import tornado.web

import logging
logger = logging.getLogger(__name__)

import tpa.tpa as tpa
import plugins.translation_repository.transifex.utils as transifex

class Handler(tornado.web.RequestHandler):
    def get(self):
        creds = tpa.get_transifex_creds()
        ret = transifex.query_projects(creds)
        if ret.succeeded:
            projects = ret.output
        else:
            logger.error("query_projects() failed. Reason: '{}'".format(ret.message))
            projects = []
        self.render('transifex_projects.html', projects=projects)

