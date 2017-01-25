import os
import sys
from pytz import utc
import signal
import json
import datetime
import abc
import uuid
import urllib
from subprocess import call

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
import apih
import core.job as job

class SchedulerJob():
    def __init__(self, job_configuration):
        self._config = job_configuration

    def execute(self):
        global job
        job.execute(self._config)

class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class ScheduleServer():
    def __init__(self):
        tornado.options.parse_command_line()
        application = tornado.web.Application(
                [
                    (r'/', IndexPageHandler),

                    # --- PROJECT ---  #
                    # List of project summary.
                    (r'/api/v0/projects', apih.ListProjectSummaryHandler),
                    # Details of a project. Args: project id
                    (r'/api/v0/project/([^/]+)/details', apih.ProjectDetailsHandler),
                    # List of details of resources. Args: project id
                    (r'/api/v0/project/([^/]+)/resource/details', apih.ProjectResourceDetailsHandler),
                    # List of language status. Args: project id 
                    (r'/api/v0/project/([^/]+)/translation/status', apih.ProjectTranslationStatusHandler),

                    # --- JOB --- #
                    # List of jobs.
                    (r'/api/v0/jobs', apih.ListJobSummaryHandler),
                    # Summary of a job. Args: job id
                    (r'/api/v0/job/([^/]+)', apih.JobSummaryHandler),
                    # Execute a job. Args: job id
                    (r'/api/v0/job/([^/]+)/exec', apih.JobExecutionHandler),
                    # Details of a job. Args: job id
                    (r'/api/v0/job/([^/]+)/details', apih.JobDetailsHandler),
                    # List of resource file path and slug. Args: job id 
                    (r'/api/v0/job/([^/]+)/resource/slugs', apih.JobResourceSlugsHandler),
                    # List of resource name (in translation platform) and slug. Args: job id
                    (r'/api/v0/job/([^/]+)/translation/slugs', apih.JobTranslationSlugsHandler),
                    # Sync status (only for ResourceUploaderJob or TranslationUploaderJob). Args: job id
                    (r'/api/v0/job/([^/]+)/sync/status', apih.JobSyncStatusHandler),
                    # Job execution status. Args: job id
                    (r'/api/v0/job/([^/]+)/exec/status', apih.JobExecStatusHandler),

                    # maybe /job/(^/]+)/log/context/3  (limit = 3) might be useful

                    # --- CONFIGURATION --- #
                    # not using now but keep for a while   
                    # (r'/api/v0/config/([^/]+)/([^/]+)', apih.ConfigurationHandler), # job id, 'key' in config file
                    # Contents of project configuration file. Args: project id
                    # (r'/api/v0/config/project/([^/]+)', apih.ProjectConfigurationHandler),
                    # Contents of job configuration file. Args: job id
                    # (r'/api/v0/config/job/([^/]+)', apih.JobConfigurationHandler),
                    # Contents of resource configuration file. Args: resource configuration file name
                    (r'/api/v0/config/resource/([^/]+)', apih.ResourceConfigurationHandler),
                    # Contents of translation configuration file. Args: translation configuration file name
                    (r'/api/v0/config/translation/([^/]+)', apih.TranslationConfigurationHandler),

                    #--- LOG (JOB EXECUTION LOG) --- #
                    # Log context. Args: log path
                    (r'/api/v0/log/([^/]+)/context', apih.LogContextHandler),

                    # --- LOCAL FILES --- #
                    # List local repositories (git repository).
                    (r'/api/v0/local/repositories', apih.ListLocalRepositoriesHandler),
                    # List branches of specified local git repository. Args: repository name
                    (r'/api/v0/local/repository/([^/]+)/branches', apih.ListLocalRepositoryBranchesHandler),
                    # List local files under specified directory. Args: repository name, relative path in the repository
                    (r'/api/v0/local/repository/([^/]+)/files/([^/]+)', apih.ListLocalRepositoryFilesHandler),

                    # --- RESOURCE REPOSITORY --- #
                    # List of repositories. Args: platform name
                    #(r'/api/v0/resource/([^/]+)/repositories', apih.ListResourceRepositoriessHandler),

                    #--- TRANSLATION REPOSITORY --- #
                    # List of projects. Args: platform name
                    (r'/api/v0/translation/([^/]+)/projects', apih.ListTranslationProjectsHandler),
                    # Project details. Args: platform name, project id
                    (r'/api/v0/translation/([^/]+)/project/([^/]+)/details', apih.TranslationProjectDetailsHandler),
                    # Resource details. Args: platform name, project id, resource id
                    (r'/api/v0/translation/([^/]+)/project/([^/]+)/resource/([^/]+)/details', apih.TranslationResourceDetailsHandler),
                    # All strings for a language. Args: platform name, project id, resource id, language code
                    (r'/api/v0/translation/([^/]+)/project/([^/]+)/resource/([^/]+)/translation/([^/]+)/strings', apih.TranslationTranslationStringsHandler),
                    # Details for a translation string. Args: platform name, project id, resource id, source string id
                    # (r'/api/v0/translation/([^/]+)/project/([^/]+)/resource/([^/]+)/translation/([^/]+)/details', apih.TranslationTranslationStringDetailsHandler),
                    # Details for a source string. Args: platform name, project id, resource id, source string id (key)
                    (r'/api/v0/translation/([^/]+)/project/([^/]+)/resource/([^/]+)/source/([^/]+)/details', apih.TranslationSourceStringDetailsHandler)
                ],
                template_path = os.path.join(os.path.dirname(__file__), 'templates'),
                static_path = os.path.join(os.path.dirname(__file__), 'static')
        )
        self.http_server = tornado.httpserver.HTTPServer(application)

        executors = {
            'default': {'type': 'threadpool', 'max_workers': 20},
            'processpool': ProcessPoolExecutor(max_workers=5)
        }

        logger.info("Initializing scheduler (pid: {}, port: '{}')...".format(os.getpid(), settings.HTTP_PORT))
        self.scheduler = TornadoScheduler()
        self.scheduler.configure(executors = executors)
        self._restore_jobs()
        self.scheduler.start()
        logger.info(self.scheduler.print_jobs())

    def _restore_jobs(self):
        global job
        configs = job.get_configuration(status='active')
        total = 0
        for c in configs:
            o = SchedulerJob(c)
            self.scheduler.add_job(o.execute, 'cron', month=c.month, day=c.day, day_of_week=c.day_of_week, hour=c.hour, minute=c.minute, name=c.name, id=c.id, misfire_grace_time = 600)
            total += 1
        logger.info("Restored '{}' jobs.".format(total))

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
        logger.info('Stopping scheduler...')
        self.scheduler.shutdown()
        tornado.ioloop.IOLoop.current().stop()
        sys.exit(0)

def _setup_dir(path):
    if os.path.isdir(path):
        return True
    else:
        try:
            os.makedirs(path)
        except OSError as e:
            sys.stderr.write("Failed to create directory: '{}'. Reason: {}\n".format(path, e))
            return False
        else:
            if os.path.isdir(path):
                return True
            else:
                sys.stderr.write("Created directory does not exist: '{}'.\n".format(path))
                return False

def _ensure_system_dir(path):
    if os.path.isdir(path):
        return True
    else:
        sys.stderr.write("NOT FOUND: '{}'.\n".format(path))
        return False

def _ensure_system_file(path):
    if os.path.isfile(path):
        return True
    else:
        sys.stderr.write("NOT FOUND: '{}'.\n".format(path))
        return False

def _check_settings():
    sys.stdout.write("Checking settings...\n")
    results = True
    if not _ensure_system_dir(settings.TPA_ROOT_DIR):
        results = False
    if not _ensure_system_dir(settings.CONFIG_RESOURCE_DIR):
        results = False
    if not _ensure_system_dir(settings.CONFIG_TRANSLATION_DIR):
        results = False
    if not _ensure_system_file(settings.PROJECT_FILE):
        results = False
    if not _ensure_system_file(settings.JOB_FILE):
        results = False
    if not _ensure_system_file(settings.SCHEDULER_UPLOADER):
        results = False
    return results

def _initialize():
    if not _check_settings():
        return False
    if not _setup_dir(settings.LOG_DIR):
        return False 
    if not _setup_dir(settings.CACHE_DIR):
       return False
    return True

def main():
    if not _initialize():
        sys.exit(1)
    svr = ScheduleServer()
    svr.start()

if __name__ == "__main__":
    main()

