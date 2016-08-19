import os
import json
import urllib
import tornado.web

import util.transifex_utils as transifex

class Handler(tornado.web.RequestHandler):
    def _get_transifex_project_details(self, project_slug):
        results = transifex.get_project_details(project_slug)
        if results:
            return results
        else:
            return transifex.create_project_details_cache(project_slug)

    def _get_transifex_resources_details(self, project_slug):
        results = transifex.get_resources_details(project_slug)
        if results:
            return results
        else:
            return transifex.create_resources_details_cache(project_slug)

    def get(self, param):
        s = urllib.unquote(param)
        platform_type = s.split(':')[0]
        project_slug = s.split(':')[1]

        if platform_type == 'transifex':
            project = self._get_transifex_project_details(project_slug)
            resources = self._get_transifex_resources_details(project_slug)
            self.render('transifexproject.html', project=project, resources=resources)
        else:
            #NIY
            self.render('crowdinproject.html', project=None)

