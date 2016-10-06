import os
import tornado.web

import logging
logger = logging.getLogger(__name__)

class Handler(tornado.web.RequestHandler):
    def _read_file(self, file_path):
        if os.path.isfile(file_path):
            with open(file_path) as fi:
                context = fi.readlines()
            return context
        else:
            logger.error("Log file '{}' not found.".format(file_path))
            return []

    def get(self, logdir):
        info_lines = self._read_file(os.path.join(logdir, 'tpa.log'))
        err_lines = self._read_file(os.path.join(logdir, 'tpa.err'))
        self.render('log.html', infolines=info_lines, errlines=err_lines)

