import os, sys
import urllib
import tornado.web

import scheduler.jobstore.jobstore as jobstore
import scheduler.logstore.logstore as logstore

class Handler(tornado.web.RequestHandler):
    def post(self, arg):
        job_id = self.get_argument('job_id', '')
        job = jobstore.find_job_by_id(job_id)
        if job:
            job.run()
            url = "/job/{}".format(urllib.quote(job.id, safe=''))
            self.redirect(url)

