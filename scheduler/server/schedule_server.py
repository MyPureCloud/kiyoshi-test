import os, sys
from pytz import utc
import logging
import signal
import json

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor

import settings
import scheduler.jobstore.utils as jobstore
from scheduler.handlers import main as main_handler
from scheduler.handlers import job as job_handler 
from scheduler.handlers import jobs as jobs_handler 
from scheduler.handlers import run as run_handler 
from scheduler.handlers import logs as logs_handler 
from scheduler.handlers import log as log_handler 
from scheduler.jobs import test as test_job, resource_uploader as resource_uploader_job, translation_uploader as translation_uploader_job

logger = logging.getLogger(__name__)

class ScheduleServer():
    def __init__(self):
        self._jobs = []
        tornado.options.parse_command_line()
        application = tornado.web.Application(
                [
                    (r'/', main_handler.Handler),
                    (r'/job/(.+)', job_handler.Handler),
                    (r'/jobs', jobs_handler.Handler),
                    (r'/run/(.+)', run_handler.Handler),
                    (r'/logs', logs_handler.Handler),
                    (r'/log/(.+)', log_handler.Handler)
                ],
                template_path = os.path.join(os.path.dirname(__file__), '..', 'templates'),
                static_path = os.path.join(os.path.dirname(__file__), '..', 'static')
        )
        self.http_server = tornado.httpserver.HTTPServer(application)

        executors = {
            'default': {'type': 'threadpool', 'max_workers': 20},
            'processpool': ProcessPoolExecutor(max_workers=5)
        }

        self.scheduler = TornadoScheduler()
        self.scheduler.configure(executors = executors)
        self._restore_jobs()
        
        logger.info("pid: {}".format(os.getpid()))
        logger.info('Starting scheduler...')
        self.scheduler.start()
        logger.info(self.scheduler.print_jobs())


    def _restore_jobs(self):
        self._jobs = jobstore.read_jobs()
        for job in self._jobs:
            if not job.status == 'active':
                continue

            self.scheduler.add_job(job.run, 'cron', month = job.month, day = job.day, day_of_week = job.day_of_week, hour = job.hour, minute = job.minute, name = job.name, id = job.id, misfire_grace_time = 600)
            logger.info("Restored: {} {} {} {} {} {}".format(job.class_name, job.status, job.name, job.resource_config_filename, job.translation_config_filename, job.id))

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


