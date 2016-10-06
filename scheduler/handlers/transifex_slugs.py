import os
import tornado.web
import urllib
import collections

#import logging
#logger = logging.getLogger(__name__)

import tpa.tpa as utils

class Handler(tornado.web.RequestHandler):
    def get(self, param):
        s = urllib.unquote(param)
        resource_config_filename = s.split(':')[0]
        translation_config_filename = s.split(':')[1]
        translation_slugs = {}
        resource_slugs = collections.OrderedDict()
        utils.get_slugs(resource_config_filename, translation_config_filename, translation_slugs, resource_slugs)
        stats = utils.get_translation_project_stats(translation_config_filename)
        if not translation_slugs:
            self.render('error.html', message="Failed to get translation_slugs.")
            return
        if not resource_slugs:
            self.render('error.html', message="Failed to get resource_slugs.")
            return
        if not stats:
            self.render('error.html', message="Failed to get translation project stats.")
            return

        self.render('transifex_slugs.html', resource_config_filename=resource_config_filename, translation_slugs=translation_slugs, resource_slugs=resource_slugs, stats=stats)

