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

def _call_post_api(url, payload):
    headers = {'Content-Type': 'application/json'}
    try:
        #r = requests.post(url, auth=(creds['username'], creds['userpasswd']), headers=headers, data=payload)
        r = requests.post(url, headers=headers, data=payload)
        logger.info("payload: '{}'".format(payload))
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


def _get_resource_uploader_configuration(resource_configuration_filename):
    url = '{}/resource/{}'.format(settings.TPA_API_CONFIG, resource_configuration_filename)
    return _call_api(url)

def _get_transltion_uploader_configuration(translation_configuration_filename):
    url = '{}/resource/{}'.format(settings.TPA_API_CONFIG, translation_configuration_filename)
    return _call_api(url)

def _get_repository_branches(resource_repository_name):
    url = '{}/{}/branches'.format(settings.TPA_API_REPOSITORY, resource_repository_name)
    return _call_api(url)

def _change_branch(job_id, resource_configuration_filename, prev_branch, selected_branch):
    j = _get_resource_uploader_configuration(resource_configuration_filename) 
    if j == None:
        logger.error("Failed to change branch. Could not obtain resource configuration file context.")
        return
    if j['repository_branch'] != prev_branch:
        logger.error("Failed to change branch. Branch in configuration file is different. Obtained: '{}', Expected: '{}.".format(j['repository_branch'], prev_branch))
        return

    j['repository_branch'] = selected_branch
    url = '{}/resource/{}'.format(settings.TPA_API_CONFIG, urllib.quote(resource_configuration_filename, safe=''))
    payload = json.dumps(j)
    r = _call_post_api(url, payload)
    if r != None:
        logger.info("Posted branch change. Response: '{}'".format(j))
    else:
        logger.error("Failed to change branch. Post request failed.")

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

class JobConfigurationHandler(tornado.web.RequestHandler):
    def get(self, job_id):
        jid = urllib.unquote(job_id)
        job = _get_job_details(job_id)
        if job == None:
            self.render('fatal_error.html', summary="Failed to get job details. id: '{}'.".format(jid))
        else:
            if job['class_name'] == 'ResourceUploaderJob':
                d = _get_resource_uploader_configuration(job['resource_config_filename'])
                b = _get_repository_branches(d['repository_name'])
                # display branch in configuration file instead of displaying error page.
                if b == None:
                    b = [d['repository_branch']]
                self.render('resource_uploader_configuration.html',
                        job_id=jid,
                        resource_config_filename=job['resource_config_filename'],
                        resource_config_file_context=d,
                        branches=b)
            elif job['class_name'] == 'TranslationUploaderJob':
                d = _get_translation_uploader_configuration_(job['resource_config_filename'])
                self.render('translation_uploader_configuration.html', data=d)
            else:
                logger.error("Unknown job class. id: '{}', class: '{}'.".format(jid, job['class_name']))
                self.render('fatal_error.html', summary="Failed to identify job class. id: '{}', class: '{}'.".format(jid,  job['class_name']))

class ChangeBranchHandler(tornado.web.RequestHandler):
    def post(self):
        jid = self.get_argument('job_id')
        resource_configuration_filename = self.get_argument('resource_configuration_filename')
        prev_branch = self.get_argument('previous_branch_name').strip().rstrip()
        selected_branch = self.get_argument('selected_branch_name').strip().rstrip()
        if prev_branch != selected_branch:
            _change_branch(jid, resource_configuration_filename, prev_branch, selected_branch)

        url = "/job/{}/configuration".format(urllib.quote(jid, safe=''))
        self.redirect(url)
        
class ProjectManagerServer():
    def __init__(self):
        self._jobs = []
        tornado.options.parse_command_line()
        application = tornado.web.Application(
                [
                    # --- * PROJECT * ---
                    (r'/', ListProjectsHandler),
                    (r'/project/(.+)', ProjectDetailsHandler), # project id

                    # --- * JOB * ---
                    (r'/exec/([^/]+)/([^/]+)', ExecuteProjectJobHandler), # project id, job id
                    # View job configuration context. Args: job id
                    (r'/job/([^/]+)/configuration', JobConfigurationHandler),

                    # --- * CONFIGURATION * ---
                    # Change branch 
                    (r'/change/branch', ChangeBranchHandler),
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

