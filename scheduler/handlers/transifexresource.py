import os
import json
import urllib
import tornado.web

import util.transifex_utils as transifex

class Handler(tornado.web.RequestHandler):
    def _get_source_strings_details(self, project_slug, resource_slug):
        strings = transifex.get_source_strings_details(project_slug, resource_slug)
        if strings:
            return strings
        else:
            return transifex.create_source_strings_details_cache(project_slug, resource_slug)

    def get(self, param):
        s = urllib.unquote(param)
        project_slug = s.split(':')[0]
        resource_slug = s.split(':')[1]
        project_name = s.split(':')[2]
        resource_name = s.split(':')[3]
        strings = self._get_source_strings_details(project_slug, resource_slug)
        self.render('transifexresource.html', project_name=project_name, resource_name=resource_name, strings=strings)

