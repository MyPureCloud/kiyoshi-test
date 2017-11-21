import os
import sys
import json
import signal
import socket
from urllib.parse import unquote
import json

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from ..common.common import FatalError
from ..common.common import TpaLogger 
from ..common.common import GET, POST
from ..common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR, response_ACCEPTED
from . import settings

# key will be re-generated for a job. 
kafka = {
    'broker_server': settings.kafka['brokers'][0]['server'],
    'broker_port': settings.kafka['brokers'][0]['port'],
    'topic': settings.kafka['topic'],
    'key': 'default'}

class WhoAmI(tornado.web.RequestHandler):
    def get(self):
        d = {'type': settings.identity['type'], 'name': settings.identity['name']}
        self.finish("{}".format(d))

class ExecJob(tornado.web.RequestHandler):
    def post(self, project_id, job_id):
        projid = unquote(project_id)
        jobid = unquote(job_id)

        # TODO --- generate job request id
        request_id = 'NIY'

        # get job details from configurator
        try:
            configurator_id = 'tpa'
            url = "{}/configuration/{}/project/{}/job/{}".format(settings.providers['configurator']['api'], configurator_id, project_id, job_id)
            r = GET(url, request_id)
        except FatalError as e:
            # TEMP --- return all errors as 400.
            res = response_BAD_REQUEST(request_id, str(e), kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return
        
        job = r['results']
        if job['status'] == 'active':
            tasks = job['tasks']
            num_tasks = len(tasks)
            if num_tasks == 0:
                msg = "Job has no tasks. pid: '{}', jid: '{}'".format(projid, jobid)
                res = response_ACCEPTED(request_id, msg, None, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
                return
            elif num_tasks == 1:
                try:
                    task = tasks[0]
                    headers = {'Content-Type': 'application/json'} 
                    payload = {'request_id': request_id, 'config_path': task['config_path']}
                    url = "{}/task/{}/exec".format(settings.providers['task_executor']['api'], task['executor'])
                    r = POST(url, request_id, headers=headers, data=json.dumps(payload))
                    res = response_OK(request_id, r['message'], r['results'], kafka)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
                except FatalError as e:
                    # TEMP --- return all errors as 400.
                    res = response_BAD_REQUEST(request_id, str(e), kafka)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
            else:
                try:
                    tasks = []
                    for x in tasks:
                        if 'aacept_feeds' in x:
                            accept_feeds = x['accept_feeds']
                        else:
                            accept_feeds = 'false'
                        tasks.append({'request_id': request_id, 'executor_id': x['executor'], 'config_path': x['config_path'], 'accept_feeds': accept_feeds})
                    payload = {'tasks': tasks}
                    headers = {'Content-Type': 'application/json'} 
                    url = "{}/tasks/multitasks_executor/exec".format(settings.providers['task_executor']['api'])
                    r = POST(url, request_id, headers=headers, data=json.dumps(payload))
                    res = response_OK(request_id, r['message'], r['results'], kafka)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
                except FatalError as e:
                    # TEMP --- return all errors as 400.
                    res = response_BAD_REQUEST(request_id, str(e), kafka)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
        else:
            msg = "Job is not executable. pid: '{}', jid: '{}', status: '{}".format(projid, jobid, job['status'])
            res = response_ACCEPTED(request_id, msg, r['results'], kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return
        

        # execute tasks for the job


def _signal_handler(signal_type, frame):
    provider_name = settings.identity['name']
    if signal_type == signal.SIGINT:
        msg = "Stopping {} (SIGINT)...".format(provider_name)
    else:
        msg = "Stopping (UNKNOWN SIGNAL)...".format(provider_name)
    with TpaLogger(**kafka) as o:
        o.info(msg)
    tornado.ioloop.IOLoop.current().stop()
    sys.exit(0)

def main():
    provider_name = settings.identity['name']
    with TpaLogger(**kafka) as o:
        o.info("Initializing {}...".format(provider_name))

    signal.signal(signal.SIGINT, _signal_handler)
    tornado.options.parse_command_line()
    application = tornado.web.Application(
        [
            (r'/', WhoAmI),
            (r'/api/v0/whoami', WhoAmI),

            # --- Execute a job --- #
            # Args:
            #   project id          e.g. web-directory
            #   job id              e.g. resource_comparison
            # Payload
            #   None 
            (r'/api/v0/job/([^/]+)/([^/]+)/exec', ExecJob)

        ])

    port = settings.server['http']['port']
    with TpaLogger(**kafka) as o:
        o.info("Starting {}@{}:{} (pid: {})...".format(provider_name, socket.gethostname(), port, os.getpid()))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()

