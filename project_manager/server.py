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

def _get_project_details(project_id):
    url = '{}/{}/{}'.format(settings.TPA_API_PROJECT, project_id, 'details')
    return _call_api(url)

def _collect_project_data(project_id):
    project = _get_project_details(project_id)
    results = {}
    if project:
        results['project_name'] = project['name']
        results['project_description'] = project['description']
        results['project_status'] = project['status']
    return results

def _get_project_resource_details(project_id):
    url = '{}/{}/{}'.format(settings.TPA_API_PROJECT, project_id, 'resource/details')
    return _call_api(url)

def _get_job_details(job_id):
    url = '{}/{}/{}'.format(settings.TPA_API_JOB, job_id, 'details')
    return _call_api(url)

def _get_resource_uploader_job_details(jobs):
    # As, there, currently, is only one ResourceUploaderJob in a project's job list.
    for job in jobs:
        if job['class_name'] == 'ResourceUploaderJob':
            logger.info("ResourceUploaderJob Details: '{}'".format(job))
            return job

    logger.error("ResourceUploaderJob not found in given jobs (below).")
    for job in jobs:
        logger.error("job_id: {} ({})".format(job['id'], job['job_class']))
    return {}

def _get_translation_uploader_job_details(jobs):
    # As, there, currently, is only one TranslationUploaderJob in a project's job list.
    for job in jobs:
        if job['class_name'] == 'TranslationUploaderJob':
            logger.info("TranslationUploaderJob Details: '{}'".format(job))
            return job

    logger.error("TranslationUploaderJob not found in given jobs (below).")
    for job in jobs:
        logger.error("job_id: {} ({})".format(job['id'], job['job_class']))
    return {}

def _get_job_sync_status(job_id):
    url = '{}/{}/{}'.format(settings.TPA_API_JOB, job_id, 'sync/status')
    return _call_api(url)

def _collect_job_sync_data(project_id):
    results = []
    project = _get_project_details(project_id)
    if project:
        for job_id in project['jobs']:
            job = _get_job_details(job_id)
            if job['class_name'] == 'ResourceUploaderJob':
                sync_status = _get_job_sync_status(job['id'])
                if sync_status:
                    results.append(
                        {
                        'job_id': job['id'],
                        'job_status': job['status'],
                        'job_cron_string': job['job_cron_string'],
                        'job_class_name': job['class_name'],
                        'sync_date': sync_status['date']
                        })
            elif job['class_name'] == 'TranslationUploaderJob':
                sync_status = _get_job_sync_status(job['id'])
                if sync_status:
                    results.append(
                        {
                        'job_id': job['id'],
                        'job_status': job['status'],
                        'job_cron_string': job['job_cron_string'],
                        'job_class_name': job['class_name'],
                        'sync_date': sync_status['date'],
                        'sync_id': sync_status['sync_id'],
                        'sync_url': sync_status['sync_url'],
                        'sync_state': sync_status['sync_state']
                        })
            else:
                logger.error("Unknown job. id: '{}', class: '{}'.".format(job_id, job['class_name']))
    return results

def _get_translation_status(project_id):
    url = '{}/{}/{}'.format(settings.TPA_API_PROJECT, project_id, 'translation/status')
    return _call_api(url)

def _collect_resource_data(project_id):
    d = _get_project_resource_details(project_id)
    results = {}
    if d:
        results['resource_repository_url'] = d['url']
        results['resource_repository_platform'] = d['platform']
        results['resource_repository_owner'] = d['owner']
        results['resource_repository_name'] = d['name']
        results['resource_repository_branch'] = d['branch']

        resources = []
        for r in d['resources']:
            languages = []
            for t in r['translations']:
                languages.append(t['language_code'])
            resources.append({'path': r['path'], 'languages': languages}) 
        results['resources'] = resources
    return results

def _merge_translation_status_data(project_id, resources):
    translations = _get_translation_status(project_id)
    if translations:
        resources['translation_platform'] = translations[0]['platform']
        resources['translation_project'] = 'NIY'
        for r in resources['resources']:
            done = []
            wip = []
            for t in translations:
                if r['path'] == t['path']:
                    for l in t['languages']:
                        # FIXME --- assuming resource's language is en-US and
                        #           removing it.
                        if l['language_code'] == 'en_US':
                            continue
                        if l['completed']:
                            done.append(l['language_code'])
                        else:
                            wip.append(l['language_code'])
                r['completed_languages'] = done
                r['in_progress_languages'] = wip

    return resources

def _collect_resource_translation_status_data(project_id):
    resources = _collect_resource_data(project_id)
    if resources:
        return _merge_translation_status_data(project_id, resources)
    else:
        return {} 

class ProjectDetailsHandler(tornado.web.RequestHandler):
    def get(self, param):
        project_id = urllib.unquote(param)
        results = _collect_project_data(project_id)
        results['project_id'] = project_id
        if results:
            results['resources'] = _collect_resource_translation_status_data(project_id)
            results['job_syncs'] = _collect_job_sync_data(project_id)
            self.render("project.html", data=results)
        else:
            self.render('fatal_error.html', summary="Failed to obtain project data. id: '{}'.".format(project_id))

class ListProjectsHandler(tornado.web.RequestHandler):
    def get(self):
        url = settings.TPA_API_PROJECTS
        _call_api_and_render(self, url, 'projects.html', "Failed to obtain project listings.")

class ExecuteProjectJobHandler(tornado.web.RequestHandler):
    def post(self, project_id, job_id):
        pid = urllib.unquote(project_id)
        jid = urllib.unquote(job_id)
        url = '{}/{}/exec'.format(settings.TPA_API_JOB, jid)
        try:
            r = requests.post(url)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            logger.error("Failed API call: '{}', Reason: '{}'.".format(url, e))
            self.render('fatal_error.html', summary="Failed to execute a job. id: '{}'.".format(jid), details=str(e))
        else:
            url = "/project/{}".format(urllib.quote(pid, safe=''))
            self.redirect(url)

class ProjectManagerServer():
    def __init__(self):
        self._jobs = []
        tornado.options.parse_command_line()
        application = tornado.web.Application(
                [
                    (r'/', ListProjectsHandler),
                    (r'/project/(.+)', ProjectDetailsHandler), # project id
                    (r'/exec/([^/]+)/([^/]+)', ExecuteProjectJobHandler) # project id, job id
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
    svr = ProjectManagerServer()
    svr.start()

if __name__ == "__main__":
    main()

