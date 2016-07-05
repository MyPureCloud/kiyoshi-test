import os
import urllib
import tornado.web

import scheduler.jobstore.utils as jobstore
import scheduler.logstore.utils as logstore

class Handler(tornado.web.RequestHandler):
    def get(self, job_id):
        job = jobstore.find_job_by_id(job_id)
        if job:
            job.run()
            url = "/job/{}".format(urllib.quote(job.id, safe=''))
            self.redirect(url)

