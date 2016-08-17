import os
import tornado.web

import scheduler.jobstore.jobstore as jobstore
import scheduler.logstore.logstore as logstore

class Handler(tornado.web.RequestHandler):
    def get(self, job_id):
        fetch_limit = 7
        job = jobstore.find_job_by_id(job_id)
        if job:
            recent_runs = jobstore.collect_jobs_latest_7(job)
            self.render('job.html', job=job, runjobs=recent_runs)
        else:
            # NIY
            pass
