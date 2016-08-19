import os
import json
import logging
import tornado.web

import settings
import util.transifex_utils as transifex

logger = logging.getLogger(__name__)

class Handler(tornado.web.RequestHandler):
    def _get_crowdin_projects(self):
        # NIY
        return None 

    def _get_transifex_projects(self):
        results = transifex.get_projects()
        if results:
            return results
        else:
            return transifex.create_projects_cache()

    def get(self):
        transifex_projects = self._get_transifex_projects()
        crowdin_projects = self._get_crowdin_projects()
        self.render('transprojects.html', transifex_projects=transifex_projects, crowdin_projects=crowdin_projects)

