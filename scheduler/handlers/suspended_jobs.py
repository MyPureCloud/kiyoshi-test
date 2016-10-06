import os
import tornado.web

import scheduler.jobstore.jobstore as jobstore

class Handler(tornado.web.RequestHandler):
    def get(self):
        jobs = jobstore.read_suspended_jobs()
        self.render('suspended_jobs.html', jobs=jobs)

