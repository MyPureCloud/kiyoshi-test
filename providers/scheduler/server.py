"""
How to run scheduler
====================
$ cd translation-process-automation
$ python3 -m providers.scheduler.server
"""
import os
import sys
import signal
import socket
import json

from urllib.parse import unquote
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.executors.pool import ProcessPoolExecutor

from . import settings
from ..common.common import FatalError
from ..common.common import GET
from ..common.common import TpaLogger
from ..common.common import response_OK, response_ACCEPTED, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR

# All configurator shares this provider, however, topic and key are specific to this module.
kafka = {
    'broker_server': settings.kafka['brokers'][0]['server'],
    'broker_port': settings.kafka['brokers'][0]['port'],
    'topic': settings.kafka['topic'],
    'key': settings.kafka['key']}

providers = {
    'configurator': {
        'api': 'http://localhost:65000/api/v0'
    },
    'job_executor': {
        'api': 'http://localhost:64600/api/v0'
    }
}


def _execute(pid, jid):
    request_id = "NIY"
    with TpaLogger(**kafka) as o:
        o.info("Executing... Project: '{}', Job: '{}'".format(config['project']['id'], x['id']))
    url = "{}/job/{}/{}/exec".format(providers['job_executor']['api'], pid, jid)
    r = POST(url, request_id)
    with TpaLogger(**kafka) as o:
        o.info("Executed. Project: '{}', Job: '{}', Status: '{}'".format(pid, jid, r['status_code']))

class WhoAmI(tornado.web.RequestHandler):
    def get(self):
        d = {'type': settings.identity['type'], 'name': settings.identity['name']}
        self.finish("{}".format(d))

class ManageProject(tornado.web.RequestHandler):
    """
    GET - List project jobs.
    POST - Add project jobs to scheduler.
    PUT - Update project jobs in scheduelr.
    DELETE - Remove project jobs from scheduler.

    To PUT/POST a project, the project jobs will be obtained via configurator.
    """
    def initialize(self, scheduler):
        self.scheduler = scheduler

    def delete(self, project_id):
        pass

    def put(self, project_id):
        pass

    def post(self, project_id):
        """
        Schedule new jobs for a project.
        If the project is known to the scheduler, NOP (use PUT to update the project).
        """
        pid = unquote(project_id)
        request_id = 'NIY'

        # Ensure the project is new to scheduler. Otherwise NOP.
        jobs = self.scheduler.get_jobs()
        for x in jobs:
            if x.project_id == pid:
                msg = "Project already exists. '{}'".format(pid)
                res = response_ACCEPTED(request_id, msg, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
                return

        # Obtain project configuration.
        try:
            configurator_id = 'tpa' # only tpa configurator for now
            url = "{}/configuration/{}/project/{}".format(providers['configurator']['api'], configurator_id, project_id)
            r = GET(url, request_id)
            if r['status_code'] == 200:
                config = r['results']
                expected_file_category = 'project_configuration'
                if config['meta']['category'] == expected_file_category:
                    pass
                else:
                    msg = "Unexpected config file category. Project: '{}', '{}' Expected: '{}', Actual: '{}'".format(project_id, expected_file_category, config['meta']['category'])
                    res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
            elif r['status_code'] == 400:
                msg = "Failed to get project configuration. Project: '{}' {}".format(project_id, r['message'])
                res = response_BAD_REQUEST(request_id, msg, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
                return
            else:
                msg = "Failed to get project configuration. Project: '{}' {}".format(project_id, r['message'])
                res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
                return
        except FatalError as e:
            msg = "Failed to get project configuration. Project: '{}' {}".format(project_id, str(e))
            res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return
        except KeyError as e:
            msg = "Failed to access key in config response. Project: '{}' '{}'".format(project_id, str(e))
            res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return


        # Schedule active project jobs.
        try:
            if config['status'] == 'active':
                num_scheduled = 0
                for x in config['jobs']:
                    if x['status'] == 'active':
                        self.scheduler.add_job(
                            lambda: _execute(config['id'], x['id']),
                            'cron',
                            month=x['schedule']['month'],
                            day=x['schedule']['day'],
                            day_of_week=x['schedule']['day_of_week'],
                            hour=x['schedule']['hour'],
                            minute=x['schedule']['minute'],
                            name=config['id'], # use name as project id
                            id="{}_{}".format(config['id'], x['id']), # make it unique id
                            misfire_grace_time=600)
                        with TpaLogger(**kafka) as o:
                            o.info("Scheduled. Project: '{}', Job: '{}'".format(config['id'], x['id']))
                        num_scheduled += 1
                    else:
                        with TpaLogger(**kafka) as o:
                            o.info("Not scheduled. Project: '{}', Job: '{}', Status: '{}'".format(config['id'], x['id'], x['status']))
                with TpaLogger(**kafka) as o:
                    o.info("Scheduled jobs: {}.".format(num_scheduled))
            else:
                with TpaLogger(**kafka) as o:
                    o.info("Not scheduled. Project: '{}', Status: '{}'".format(config['id'], x['status']))
        except KeyError as e:
            msg = "Failed to access key in project config. Project: '{}' '{}'".format(project_id, str(e))
            res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return

    def get(self, project_id):
        pid = unquote(project_id)
        request_id = 'NIY'
        jobs = self.scheduler.get_jobs()
        lst = []
        found = False
        for x in jobs:
            if x.name == pid: # name attribute holds project id.
                lst.append(x.id)
                found = True
        if found:    
            try:
                j = json.dumps({'project': pid, 'jobs': lst})
                msg = "{}".format(pid)
                res = response_OK(request_id, msg, j, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
            except ValueError as e:
                msg = "Failed to dump project to json. {}".format(str(e))
                res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
        else:
            msg = "Unscheulded project. '{}'".format(pid)
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

class ListProjects(tornado.web.RequestHandler):
    """
    List scheduled projects.
    """
    def initialize(self, scheduler):
        self.scheduler = scheduler

    def get(self):
        request_id = 'NIY'
        names = set()
        jobs = self.scheduler.get_jobs()
        for x in jobs:
            names.add(x.name) # name attribute holds project id.
        lst = list(names)
        d = {'projects': lst}
        try:
            j = json.dumps(d)
            msg = "{} projects.".format(len(lst))
            res = response_OK(request_id, msg, j, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
        except ValueError as e:
            msg = "Failed to dump project lists to json. {}".format(str(e))
            res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

def main():
    provider_name = settings.identity['name']
    with TpaLogger(**kafka) as o:
        o.info("Initializing {}...".format(provider_name))

    scheduler = TornadoScheduler()
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 20},
        'processpool': ProcessPoolExecutor(max_workers=5)
    }
    scheduler.configure(executors=executors)
    scheduler.start()

    def signal_handler(signal_type, frame):
        if signal_type == signal.SIGINT:
            msg = "Stopping {} (SIGINT)...".format(provider_name)
        else:
            msg = "Stopping {} (UNKNOWN SIGNAL)...".format(provider_name)
        with TpaLogger(**kafka) as o:
            o.info(msg)
        scheduler.shutdown()
        tornado.ioloop.IOLoop.current().stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    tornado.options.parse_command_line()
    application = tornado.web.Application(
        [
            (r'/', WhoAmI),
            (r'/api/v0/whoami', WhoAmI),

            # List scheduled projects.
            # Args:
            #  None
            (r'/api/v0/schedule/projects', ListProjects, dict(scheduler=scheduler)),

            # List (GET), add (POST), update (PUT) or delete (DELETE) a project in scheduler.
            # The project has to be known by configurator.
            # Args:
            #  Project id
            # Payload:
            #  None
            (r'/api/v0/schedule/project/([^/]+)', ManageProject, dict(scheduler=scheduler))
        ])

    port = settings.server['http']['port']
    with TpaLogger(**kafka) as o:
        o.info("Starting {}@{}:{} (pid: {})...".format(provider_name, socket.gethostname(), port, os.getpid()))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()

