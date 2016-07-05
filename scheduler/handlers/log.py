import os
import tornado.web

class Handler(tornado.web.RequestHandler):
    def get(self, logdir):
        info_lines = self._read_file(os.path.join(logdir, 'tpa.log'))
        err_lines = self._read_file(os.path.join(logdir, 'tpa.err'))
        self.render('log.html', infolines=info_lines, errlines=err_lines)

    def _read_file(self, file_path):
        with open(file_path) as fi:
            context = fi.readlines()
        return context

