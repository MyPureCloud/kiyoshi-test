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


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

def _call_api(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        j = json.loads(r.text)
    except (RequestException, HTTPError) as e:
        logger.error("Failed API call: '{}', Reason: '{}'.".format(url, e))
        return None 
    except ValueError as e:
        logger.error("Failed to parse API response. Reason: '{}', Response:'{}'.".format(e, r.text))
        return None 
    else:
        logger.info(r.text)
        return j 

def _call_api_and_render(handler, url, html_template, error_message):
    j = _call_api(url)
    if j != None:
        handler.render(html_template, data=j)
    else:
        handler.render('fatal_error.html', summary=error_message, details="")

class ProjectDetailsHandler(tornado.web.RequestHandler):
    def get(self, param):
        project_id = urllib.unquote(param)
        url = '{}/{}/details'.format(settings.TPA_API_PROJECT, project_id)
        _call_api_and_render(self, url, 'project.html', "Failed to obtain project details.")

class ListProjectsHandler(tornado.web.RequestHandler):
    def get(self):
        url = settings.TPA_API_PROJECTS
        _call_api_and_render(self, url, 'projects.html', "Failed to obtain project listings.")

class JobDetailsHandler(tornado.web.RequestHandler):
    def get(self, param):
        job_id = urllib.unquote(param)
        url = '{}/{}/details'.format(settings.TPA_API_JOB, job_id)
        _call_api_and_render(self, url, 'job.html', "Failed to obtain job details.")

def _get_all_jobs():
    url = settings.TPA_API_JOBS
    return  _call_api(url)

class ListJobsHandler(tornado.web.RequestHandler):
    def get(self):
        j = _get_all_jobs()
        if j != None:
            self.render("jobs.html", data=j)
        else:
            self.render('fatal_error.html', summary="Failed to obtain job listings.", details="")

class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        jobs = _get_all_jobs()
        if jobs == None:
            self.render('fatal_error.html', summary="Failed to obtain job listings.", details="")
        else:
            lists = [] 
            for x in jobs:
                url = "{}/{}/exec/status".format(settings.TPA_API_JOB, x['id'])
                j = _call_api(url)
                if j:
                    lists.append(j[0]) # only one exec stata is the retured array. 
            self.render("dashboard.html", data=lists)

class ResourceConfigHandler(tornado.web.RequestHandler):
    def get(self, param):
        filename = urllib.quote(param, safe='')
        url = '{}/resource/{}'.format(settings.TPA_API_CONFIG, filename)
        _call_api_and_render(self, url, 'resource_config.html', "Failed to obtain resource configuration context.")

class TranslationConfigHandler(tornado.web.RequestHandler):
    def get(self, param):
        filename = urllib.quote(param, safe='')
        url = '{}/translation/{}'.format(settings.TPA_API_CONFIG, filename)
        _call_api_and_render(self, url, 'translation_config.html', "Failed to obtain translation configuration context.")

class LogContextHandler(tornado.web.RequestHandler):
    def get(self, param):
        log_path = urllib.quote(param, safe='')
        url = '{}/{}/context'.format(settings.TPA_API_LOG, log_path)
        j = _call_api(url)
        if j:
            self.render('log.html', path=param, data=j)
        else:
            self.render('fatal_error.html', summary="Failed to obtain log context.", details="")

def _get_resource_slugs(job_id):
    url = '{}/{}/resource/slugs'.format(settings.TPA_API_JOB, job_id)
    return _call_api(url)

def _get_translation_slugs(job_id):
    url = '{}/{}/translation/slugs'.format(settings.TPA_API_JOB, job_id)
    return _call_api(url)

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

class ListTranslationProjects(tornado.web.RequestHandler):
    def get(self, arg):
        platform = urllib.unquote(arg)
        url = '{}/{}/projects'.format(settings.TPA_API_TRANSLATION, platform)
        j = _call_api(url)
        if j != None:
            self.render("translation_projects.html", platform=platform, projects=j)
        else:
            self.render('fatal_error.html', summary="Failed to obtain translation project listings.", details="")

def _get_translation_project_resource_details(base_url, resources):
    l = []
    for x in resources:
        url = '{}/resource/{}/details'.format(base_url, x['slug'])
        j = _call_api(url)
        if j != None:
            l.append(j)
    return l

def _get_translation_platform_project_details(platform, pslug):
    url = '{}/{}/project/{}/details'.format(settings.TPA_API_TRANSLATION, platform, pslug)
    return _call_api(url)

class TranslationProjectDetails(tornado.web.RequestHandler):
    """ Returns project details and details for each resource in the project. """
    def get(self, arg1, arg2):
        platform = urllib.unquote(arg1)
        pslug = urllib.unquote(arg2)
        j = _get_translation_platform_project_details(platform, pslug)
        if j != None:
            base_url = '{}/{}/project/{}'.format(settings.TPA_API_TRANSLATION, platform, pslug)
            l = _get_translation_project_resource_details(base_url, j['resources'])
            self.render("translation_project_details.html", platform=platform, details=j, resources=l)
        else:
            self.render('fatal_error.html', summary="Failed to obtain translation project details.", details="")

def _get_translation_platform_translation_strings(platform, pslug, rslug, lang):
    url = '{}/{}/project/{}/resource/{}/translation/{}/strings'.format(settings.TPA_API_TRANSLATION, platform, pslug, rslug, lang)
    return _call_api(url)

class TranslationProjectTranslationStrings(tornado.web.RequestHandler):
    """ Returns summary of translated strings for specified language of resource in the project. """
    def get(self, arg1, arg2, arg3, arg4):
        platform = urllib.unquote(arg1)
        pslug = urllib.unquote(arg2)
        rslug = urllib.unquote(arg3)
        lang = urllib.unquote(arg4)
        j = _get_translation_platform_translation_strings(platform, pslug, rslug, lang)
        if j != None:
            self.render("translation_project_translation_strings.html", data=j)
        else:
            self.render('fatal_error.html', summary="Failed to obtain translation project translation strings.", details="")

def _get_translation_platform_source_details(platform, pslug, rslug, source_key):
    url = '{}/{}/project/{}/resource/{}/source/{}/details'.format(settings.TPA_API_TRANSLATION, platform, pslug, rslug, source_key)
    return _call_api(url)

class TranslationProjectSourceStringDetails(tornado.web.RequestHandler):
    """ Returns list of details of source string for specified resource in the project. """
    def get(self, arg1, arg2, arg3):
        platform = urllib.unquote(arg1)
        pslug = urllib.unquote(arg2)
        rslug = urllib.unquote(arg3)
        p = _get_translation_platform_project_details(platform, pslug)
        if p:
            l = _get_translation_platform_translation_strings(platform, pslug, rslug, p['source_language_code'])
            if l:
                r = []
                for x in l:
                    j = _get_translation_platform_source_details(platform, pslug, rslug, x['key'])
                    if j:
                        if platform == 'transifex':
                            j['source'] = x['source']
                        else:
                            pass
                        r.append(j)
                    else:
                        pass
                self.render("translation_project_source_strings.html", data=r)
            else:
                self.render('fatal_error.html', summary="Failed to obtain translation project source string details.", details="")
        else:
            self.render('fatal_error.html', summary="Failed to obtain translation project source string details.", details="")

class SystemManagerServer():
    def __init__(self):
        self._jobs = []
        tornado.options.parse_command_line()
        application = tornado.web.Application(
                [
                    (r'/', IndexHandler),
                    # --- * CONFIGURATION * ---
                    # Context of resource configuration file. Args: resource configuration filename
                    (r'/config/resource/([^/]+)', ResourceConfigHandler),
                    # Context of translation configuration file. Args: translation configuration filename
                    (r'/config/translation/([^/]+)', TranslationConfigHandler),

                    # --- * DASHBOARD * ---
                    # Dashboard.
                    (r'/dashboard', DashboardHandler),

                    # --- * JOB * ---
                    # List of jobs.
                    (r'/jobs', ListJobsHandler),
                    # List resource slugs for resources in a project. Args: job id
                    (r'/job/([^/]+)/check/slugs', CheckSlugsHandler),
                    # Details of a job. Args: job id
                    (r'/job/([^/]+)/details', JobDetailsHandler),
                    # Context of most recent log for a job. Args: job id

                    # --- * LOG * ---
                    (r'/log/([^/]+)/context', LogContextHandler),
                    # List of projects.

                    # --- * PROJECT * ---
                    (r'/projects', ListProjectsHandler),
                    # Details of a project. Args: project id
                    (r'/project/([^/]+)/details', ProjectDetailsHandler),
                    # List of projects in translation platform (e.g. Transifex projects) Args: translation platform name
  
                    # --- * TRANSLATION PLATFORM * ---
                    (r'/translation/([^/]+)/projects', ListTranslationProjects),
                    # Details of a project in translation platform. Args: translation platform name, project slag
                    (r'/translation/([^/]+)/project/([^/]+)/details', TranslationProjectDetails),
                    # List of all translation strings for a resource of a language. Args: translation platform name, project slug, resource slug, langauge code
                    (r'/translation/([^/]+)/project/([^/]+)/resource/([^/]+)/translation/([^/]+)/strings', TranslationProjectTranslationStrings),
                    # Details of a source string. Args: translation platform name, project slug, resource slug
                    (r'/translation/([^/]+)/project/([^/]+)/resource/([^/]+)/source/strings', TranslationProjectSourceStringDetails)
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

