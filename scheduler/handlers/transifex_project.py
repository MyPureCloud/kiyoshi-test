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
        platform_type = s.split(':')[0] # not used
        project_slug = s.split(':')[1]

        creds = tpa.get_transifex_creds()
        ret = transifex.query_project(creds, project_slug)
        if ret.succeeded:
            project = ret.output
            resources = []
            for resource in project.resources:
                ret = transifex.query_resource(creds, project_slug, resource.slug)
                if ret.succeeded:
                    resources.append(ret.output)
            project_and_resources = {'project': project, 'resources': resources}
        else:
            logger.error("query_project() failed. Reason: '{}'".format(ret.message))
            project_and_resources = {'project': None, 'resources': None}
        self.render('transifex_project.html', data=project_and_resources)

