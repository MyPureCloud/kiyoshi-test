import os
import sys
import signal
import json
import requests
from requests.exceptions import RequestException, HTTPError
import urllib

import logging
logger = logging.getLogger(__name__)

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor

import settings

def _get_all_jobs():
    url = settings.TPA_API_JOBS
    try:
        r = requests.get(url)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        logger.error("Failed API call: '{}', Reason: '{}'.".format(url, e))
        return None
    else:
        try:
            j = json.loads(r.text)
            logger.info(r.text)
        except ValueError as e:
            logger.error("Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text))
            return None
        else:
            return j 

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class ProjectDetailsHandler(tornado.web.RequestHandler):
    def get(self, param):
        project_id = urllib.unquote(param)
        url = '{}/{}/details'.format(settings.TPA_API_PROJECT, project_id)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            message = "Failed API call: '{}', Reason: '{}'.".format(url, e)
            logger.error(message)
            self.render('fatal_error.html', summary="Failed to obtain project details.", details=message)
        else:
            try:
                j = json.loads(r.text)
                logger.info(r.text)
            except ValueError as e:
                message = "Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text)
                logger.error(message)
                self.render('fatal_error.html', summary="Failed to obtain project details.", details=message)
            else:
                self.render("project.html", project=j)

class ListProjectsHandler(tornado.web.RequestHandler):
    def get(self):
        url = settings.TPA_API_PROJECTS
        try:
            r = requests.get(url)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            message = "Failed API call: '{}', Reason: '{}'.".format(url, e)
            logger.error(message)
            self.render('fatal_error.html', summary="Failed to obtain project listings.", details=message)
        else:
            try:
                j = json.loads(r.text)
                logger.info(r.text)
            except ValueError as e:
                message = "Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text)
                logger.error(message)
                self.render('fatal_error.html', summary="Failed to obtain project listings.", details=message)
            else:
                self.render("projects.html", projects=j)

class JobDetailsHandler(tornado.web.RequestHandler):
    def get(self, param):
        job_id = urllib.unquote(param)
        url = '{}/{}/details'.format(settings.TPA_API_JOB, job_id)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            message = "Failed API call: '{}', Reason: '{}'.".format(url, e)
            logger.error(message)
            self.render('fatal_error.html', summary="Failed to obtain job details.", details=message)
        else:
            try:
                j = json.loads(r.text)
                logger.info(r.text)
            except ValueError as e:
                message = "Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text)
                logger.error(message)
                self.render('fatal_error.html', summary="Failed to obtain job details.", details=message)
            else:
                self.render("job.html", job=j)

class ListJobsHandler(tornado.web.RequestHandler):
    def get(self):
        j = _get_all_jobs()
        if j == None:
            self.render('fatal_error.html', summary="Failed to obtain job listings.", details="")
        else:
            self.render("jobs.html", jobs=j)

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        jobs = _get_all_jobs()
        if jobs == None:
            self.render('fatal_error.html', summary="Failed to obtain job listings.", details="")
        else:
            lists = [] 
            for x in jobs:
                url = "{}/{}/exec/status".format(settings.TPA_API_JOB, x['id'])
                try:
                    r = requests.get(url)
                    r.raise_for_status()
                except (RequestException, HTTPError) as e:
                    logger.error("Failed API call: '{}', Reason: '{}'.".format(url, e))
                else:
                    try:
                        j = json.loads(r.text)
                    except ValueError as e:
                        logger.error("Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text))
                    else:
                        logger.info(r.text)
                        lists.append(j[0]) # only one exec stata is the retured array. 

            self.render("dashboard.html", data=lists)

class XXXXXXXXXXXXLogContextHandler(tornado.web.RequestHandler):
    def get(self, param):
        log_path = urllib.quote(param, safe='')
        url = '{}/{}/context'.format(settings.TPA_API_LOG, log_path)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            message = "Failed API call: '{}', Reason: '{}'.".format(url, e)
            logger.error(message)
            self.render('fatal_error.html', summary="Failed to obtain log context.", details=message)
        else:
            try:
                j = json.loads(r.text)
                logger.info(r.text)
            except ValueError as e:
                message = "Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text)
                logger.error(message)
                self.render('fatal_error.html', summary="Failed to obtain log context.", details=message)
            else:
                self.render("log.html", path=param, data=j)

class ResourceConfigHandler(tornado.web.RequestHandler):
    def get(self, param):
        filename = urllib.quote(param, safe='')
        url = '{}/resource/{}'.format(settings.TPA_API_CONFIG, filename)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            message = "Failed API call: '{}', Reason: '{}'.".format(url, e)
            logger.error(message)
            self.render('fatal_error.html', summary="Failed to obtain resource config file context.", details=message)
        else:
            try:
                j = json.loads(r.text)
                logger.info(r.text)
            except ValueError as e:
                message = "Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text)
                logger.error(message)
                self.render('fatal_error.html', summary="Failed to obtain resource config context.", details=message)
            else:
                self.render("resource_config.html", data=j)

class TranslationConfigHandler(tornado.web.RequestHandler):
    def get(self, param):
        filename = urllib.quote(param, safe='')
        url = '{}/translation/{}'.format(settings.TPA_API_CONFIG, filename)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            message = "Failed API call: '{}', Reason: '{}'.".format(url, e)
            logger.error(message)
            self.render('fatal_error.html', summary="Failed to obtain translation config file context.", details=message)
        else:
            try:
                j = json.loads(r.text)
                logger.info(r.text)
            except ValueError as e:
                message = "Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text)
                logger.error(message)
                self.render('fatal_error.html', summary="Failed to obtain translation config context.", details=message)
            else:
                self.render("translation_config.html", data=j)

class LogContextHandler(tornado.web.RequestHandler):
    def get(self, param):
        log_path = urllib.quote(param, safe='')
        url = '{}/{}/context'.format(settings.TPA_API_LOG, log_path)
        try:
            r = requests.get(url)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            message = "Failed API call: '{}', Reason: '{}'.".format(url, e)
            logger.error(message)
            self.render('fatal_error.html', summary="Failed to obtain log context.", details=message)
        else:
            try:
                j = json.loads(r.text)
                logger.info(r.text)
            except ValueError as e:
                message = "Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text)
                logger.error(message)
                self.render('fatal_error.html', summary="Failed to obtain log context.", details=message)
            else:
                self.render("log.html", path=param, data=j)

def _get_resource_slugs(job_id):
    url = '{}/{}/resource/slugs'.format(settings.TPA_API_JOB, job_id)
    try:
        r = requests.get(url)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        logger.error("Failed API call: '{}', Reason: '{}'.".format(url, str(e)))
        return None
    else:
        try:
            j = json.loads(r.text)
            logger.info(r.text)
        except ValueError as e:
            logger.error("Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text))
            return None 
        else:
            return j

def _get_translation_slugs(job_id):
    url = '{}/{}/translation/slugs'.format(settings.TPA_API_JOB, job_id)
    try:
        r = requests.get(url)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        logger.error("Failed API call: '{}', Reason: '{}'.".format(url, str(e)))
        return None
    else:
        try:
            j = json.loads(r.text)
            logger.info(r.text)
        except ValueError as e:
            logger.error("Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text))
            return None 
        else:
            return j

class CheckSlugsHandler(tornado.web.RequestHandler):
    def get(self, param):
        job_id = urllib.unquote(param)
        r = _get_resource_slugs(job_id)
        if r:
            t = _get_translation_slugs(job_id)
            if t:
                results = []
                for x in r:
                    found = False
                    for k, v in x.items(): # just one dictionary in x
                        r_k = k # path
                        r_v = v # slug
                    for y in t:
                        for k, v in y.items(): # just one dictionary in y
                            t_k = k # slug
                            t_v = v # name
                        if r_v == t_k:
                            results.append({'exists': True, 'path': r_k, 'slug': r_v, 'name': t_v})
                            found = True
                            break
                    if not found:
                        results.append({'exists': False, 'path': r_k, 'slug': r_v, 'name': ''})
                self.render("checkslugs.html", slugs=results)
            else:
                self.render('fatal_error.html', summary="Failed to obtain job translation slugs.", details="")
        else:
            self.render('fatal_error.html', summary="Failed to obtain job resource slugs.", details="")

class SystemManagerServer():
    def __init__(self):
        self._jobs = []
        tornado.options.parse_command_line()
        application = tornado.web.Application(
                [
                    (r'/', IndexHandler),
                    (r'/config/resource/([^/]+)', ResourceConfigHandler), # resource config filename
                    (r'/config/translation/([^/]+)', TranslationConfigHandler), # translation config filename
                    (r'/dashboard', DashboardHandler),
                    (r'/jobs', ListJobsHandler),
                    (r'/job/([^/]+)/check/slugs', CheckSlugsHandler), # job id
                    (r'/job/([^/]+)/details', JobDetailsHandler), # job id
                    (r'/log/([^/]+)/context', LogContextHandler), # job id
                    (r'/projects', ListProjectsHandler),
                    (r'/project/([^/]+)/details', ProjectDetailsHandler) # project id
                ],
                template_path = os.path.join(os.path.dirname(__file__), '.', 'templates'),
                static_path = os.path.join(os.path.dirname(__file__), '.', 'static')
        )
        self.http_server = tornado.httpserver.HTTPServer(application)

        executors = {
            'default': {'type': 'threadpool', 'max_workers': 20},
            'processpool': ProcessPoolExecutor(max_workers=5)
        }

        logger.info("Initializing scheduler (pid: {}, port: '{}')...".format(os.getpid(), settings.HTTP_PORT))
        self.scheduler = TornadoScheduler()
        self.scheduler.configure(executors = executors)
        self.scheduler.start()

    # @classmethod
    def start(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        self.http_server.listen(settings.HTTP_PORT)
        tornado.ioloop.IOLoop.current().start()

    def _signal_handler(self, signal_type, frame):
        if signal_type == signal.SIGINT:
            logger.info('SIGINT')
        else:
            logger.warning('Unknown signal')

        self.terminate()

    # @classmethod
    def terminate(self):
        logger.info('Stopping console...')
        self.scheduler.shutdown()
        tornado.ioloop.IOLoop.current().stop()
        sys.exit(0)

def main():
    svr = SystemManagerServer()
    svr.start()

if __name__ == "__main__":
    main()

