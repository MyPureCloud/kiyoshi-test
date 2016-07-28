import os, sys
import urllib
import tornado.web

import scheduler.jobstore.utils as jobstore
import scheduler.logstore.utils as logstore

class Handler(tornado.web.RequestHandler):
    def post(self, arg):
        job_id = self.get_argument('job_id', '')
        job = jobstore.find_job_by_id(job_id)
        if job:
            if job.class_name == 'TranslationUploaderJob':
                options = {}
                if self.get_argument('language_completion', '') == 'all':
                    options['all_lang_per_resource'] = True
                else:
                    options['all_lang_per_resource'] = False
                job.run(**options)
            else:
                job.run()

            url = "/job/{}".format(urllib.quote(job.id, safe=''))
            self.redirect(url)

