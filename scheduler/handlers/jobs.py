import os
import tornado.web

import scheduler.jobstore.jobstore as jobstore

class Handler(tornado.web.RequestHandler):
    def get(self):
        jobs = jobstore.read_jobs()
        self.render('jobs.html', jobs=jobs)

