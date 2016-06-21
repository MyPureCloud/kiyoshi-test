import os
import tornado.web

import tpa.settings as settings
import tpa.scheduler.logstore.utils as logstore

class Handler(tornado.web.RequestHandler):
    def get(self):
        ru_entries = logstore.collect_loginfo_all_ru()
        tu_entries = logstore.collect_loginfo_all_tu()
        self.render('logs.html', ru_entries=ru_entries, tu_entries=tu_entries)

