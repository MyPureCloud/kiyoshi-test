import os
import urllib
import tornado.web

import tpa.scheduler.jobstore.utils as jobstore
import tpa.scheduler.logstore.utils as logstore

class Handler(tornado.web.RequestHandler):
    def get(self, job_id):
        fetch_limit = 7
        job = jobstore.find_job_by_id(job_id)
        if job:
            job.run()
            url = "http://localhost:8080/job/{}".format(urllib.quote(job.id, safe=''))
            self.redirect(url)

