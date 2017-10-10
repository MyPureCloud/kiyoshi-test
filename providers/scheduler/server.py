import os
import sys
import signal
import socket
try:
    from urllib import unquote
except ImportError:
    from urlilb.parse import unquote

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from apscheduler.schedulers.tornado import TornadoScheduler
#from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor

import settings
from common.common import FatalError
from common.common import GET
from common.common import TpaLogger
from common.common import response_OK, response_ACCEPTED, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR

# All configurator shares this provider, however, topic and key are specific to this module.
kafka = {
    'broker_server': settings.kafka['brokers'][0]['server'],
    'broker_port': settings.kafka['brokers'][0]['port'],
    'topic': settings.kafka['topic'],
    'key': settings.kafka['key']}

# @@@@@@@@@@@
# TODO --- 'scheuler' and 'scheduled_jobs' can be put in closure
#
scheduler = None

# Holds jobs, which is added to scheduler.
scheduled_jobs = []
# @@@@@@@@@@@

class WhoAmI(tornado.web.RequestHandler):
    def get(self):
        d = {'type': settings.identity['type'], 'name': settings.identity['name']}
        self.finish("{}".format(d))

def _gen_scheduler_job_id(project_id, job_id):
    ''' Create unique id for scheduler. '''
    return project_id + '_' + job_id

class Job():
    def __init__(self, project_id, job_id, tasks):
        self.project_id = project_id
        self.job_id = job_id
        self.tasks = tasks
        self.scheduler_job_id = _gen_scheduler_job_id(project_id, job_id)

    def execute(self):
        pass

def _add_project(project_id):
    '''
    Add a new project to scheduler.
    The project has to be defined in configuration.
    '''
    request_id = 'NIY'

    global scheduler
    global scheduled_jobs

    for o in scheduled_jobs:
        if o.project_id == project_id:
            msg = "Cannot add a project already in scheduler. '{}'".format(project_id)
            return response_ACCEPTED(request_id, msg, [], kafka)

    try:
        url = "{}/configuration/tpa/project/{}".format(settings.providers['configurator']['api'], project_id)
        r = GET(url, request_id)
    except FatalError as e:
        return response_BAD_REQUEST(request_id, str(e), kafka)

    try:
        config = r['results']
        if config['status'] == 'active':
            msg = "Scheduling project '{}'...".format(project_id)
            with TpaLogger(**kafka) as o:
                o.info(msg)

            jobs = []
            for y in config['jobs']:
                o = Job(config['id'], y['id'], y['tasks'])
                scheduler.add_job(
                    o.execute,
                    'cron',
                    month=y['schedule']['month'],
                    day=y['schedule']['day'],
                    day_of_week=y['schedule']['day_of_week'],
                    hour=y['schedule']['hour'],
                    minute=y['schedule']['minute'],
                    name=y['id'],
                    id=o.scheduler_job_id,
                    misfire_grace_time = 600)
                scheduled_jobs.append(o)
                jobs.append(o.scheduler_job_id)
                msg = "Scheduled: job='{}'".format(y['id'])
            return response_OK(request_id, msg, jobs, kafka)
        else:
            msg = "Project '{}' not scheduled. status='{}'".format(project_id, config['status'])
            return response_Accepted(request_id, msg, [], kafka)
    except KeyError as e:
        msg = "Failed to access key in config for '{}' project. {}".format(project_id, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

def _list_project_jobs(project_id):
    '''
    List jobs for specified 'scheduled' project.
    '''
    request_id = 'NIY'
    global scheduled_jobs

    for o in scheduled_jobs:
        if o.project_id == project_id:
            break
    else:
        msg = "Project not in scheduler. '{}'".format(project_id)
        return response_BAD_REQUEST(request_id, msg, kafka)

    jobs = []
    for o in scheduled_jobs:
        if o.project_id == project_id:
            jobs.append(o.job_id)
    if jobs:
        msg = "{} jobs for '{}'.".format(len(jobs), project_id)
        return response_OK(request_id, msg, jobs, kafka)
    else:
        msg = "No jobs for '{}'.".format(project_id)
        return response_OK(request_id, msg, [], kafka)

def _exec_job(project_id, job_id):
    '''
    The job has to be in scheduler.
    '''
    request_id = 'req_id-NIY'

    global scheduled_jobs
    tasks = None
    scheduler_job_id = _gen_scheduler_job_id(project_id, job_id)
    for o in scheduled_jobs:
        if o.scheduler_job_id == scheduler_job_id:
            tasks = o.tasks
            break
    else:
        msg = "Job '{}' of project '{}' not found in scheduler.".format(job_id, project_id)
        return response_BAD_REQUEST(request_id, msg, kafka)

    results = {'project_id': project_id, 'task_exec_results': []}
    for x in tasks:
        info("Dispacting task '{}'...".format(x))
        # call task executor api w/ request_id, prjoect_id, job_id, x['status'], x['executor'], x['config_path']
        # if r == 200
        # result['task_exec_result'].append({'task_id': x['id'], 'status_code': r['status_code'], 'meessage': r['message'], 'results': r['results']}
    msg = "Executed Job '{}' of project '{}'.".format(job_id, project_id)
    return response_OK(request_id, msg, results, kafka)
    
class AddProject(tornado.web.RequestHandler):
    def post(self, project_id):
        projid = unquote(project_id)
        res = _add_project(projid)
        self.set_status(res['status_code'])
        self.finish(res)

class ListProjectJobs(tornado.web.RequestHandler):
    def get(self, project_id):
        projid = unquote(project_id)
        res = _list_project_jobs(projid)
        self.set_status(res['status_code'])
        self.finish(res)

class ExecJob(tornado.web.RequestHandler):
    def post(self, project_id, job_id):
        projid = unquote(project_id)
        jobid = unquote(job_id)
        res = _exec_job(projid, jobid)
        self.set_status(res['status_code'])
        self.finish(res)

def _signal_handler(signal_type, frame):
    global scheduler
    provider_name = settings.identity['name']
    if signal_type == signal.SIGINT:
        msg = "Stopping {} (SIGINT)...".format(provider_name)
    else:
        msg = "Stopping {} (UNKNOWN SIGNAL)...".format(provider_name)
    with TpaLogger(**kafka) as o:
        o.info(msg)
    scheduler.shutdown()
    tornado.ioloop.IOLoop.current().stop()
    sys.exit(0)

def main():
    global scheduler
    scheduler = TornadoScheduler()
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 20},
        'processpool': ProcessPoolExecutor(max_workers=5)
    }
    scheduler.configure(executors=executors)
    scheduler.start()

    signal.signal(signal.SIGINT, _signal_handler)
    tornado.options.parse_command_line()
    application = tornado.web.Application(
        [
            (r'/', WhoAmI),
            (r'/api/v0/whoami', WhoAmI),

            # Add a project to scheduler.
            # Args:
            #  Project id
            (r'/api/v0/schedule/project/([^/]+)/add', AddProject),

            # List job(s) for a project.
            # Args:
            #  Project id.
            (r'/api/v0/schedule/project/([^/]+)/jobs', ListProjectJobs),

            # Execute a job.
            # Args:
            #  Project id
            #  Job id
            (r'/api/v0/schedule/project/([^/]+)/job/([^/]+)/exec', ExecJob)
        ])

    provider_name = settings.identity['name']
    port = settings.server['http']['port']
    with TpaLogger(**kafka) as o:
        o.info("Starting {}@{}:{} (pid: {})...".format(provider_name, socket.gethostname(), port, os.getpid()))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()

