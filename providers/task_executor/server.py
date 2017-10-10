import os
import sys
import json
import signal
import socket
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote
import json

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

import settings
from common.common import FatalError
from common.common import TpaLogger 
from common.common import response_OK, response_BAD_REQUEST

# All task executors share this provider, however, topic and key are specific to this module.
kafka = {
    'broker_server': settings.kafka['brokers'][0]['server'],
    'broker_port': settings.kafka['brokers'][0]['port'],
    'topic': settings.kafka['topic'],
    'key': settings.kafka['key']}

class WhoAmI(tornado.web.RequestHandler):
    def get(self):
        d = {'type': settings.identity['type'], 'name': settings.identity['name']}
        self.finish("{}".format(d))

class ExecTask(tornado.web.RequestHandler):
    def initialize(self, executors):
        self.executors = executors

    def post(self, executor_id):
        eid = unquote(executor_id)
        request_id = 'NIY'       # for exception case
        try:
            data = json.loads(self.request.body)
            request_id = data['request_id']
            config_path = data['config_path']

            # TODO --- since not all executros require 'format' option,
            #           this kind of option should be handled another way.
            if 'format' in data:
                style = data['format']
            else:
                style = None
        except ValueError as e:
            msg = "Failed to process payload of task '{}', {}".format(eid, str(e))
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return
        except KeyError as e:
            msg = "Failed to access key in payload of task '{}', {}".format(eid, str(e))
            res =  response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return

        if style:
            kwargs = {'format': style}
        else:
            kwargs = {} 

        for x in self.executors:
            for k, v in x.items():
                if k == eid:
                    res = v.execute(request_id, config_path, kafka, **kwargs)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
        else:
            msg = "Executor not found in executor list. '{}'".format(eid)
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

def _execute_multi_tasks(request_id, tasks, executors, force_execute):
    feeds = []
    summary = []
    n = len(tasks) 
    for i in range(0, n):
        request_id = None       # for exception case.
        executor_id = None
        try:
            request_id = tasks[i]['request_id']
            executor_id = tasks[i]['executor_id']
            config_path = tasks[i]['config_path']
          
            if 'accept_feeds' in tasks[i]:
                if tasks[i]['accept_feeds'] == 'true':
                    accept_feeds = True
                else:
                    with TpaLogger(**kafka) as o:
                        o.error("REQ[{}] Unknown accept_feeds value '{}'. Defaults to False.".format(request_id, tasks[i]['accept_feeds']))
                    accept_feeds = False
            else:
                accept_feeds = False

        except KeyError as e:
            with TpaLogger(**kafka) as o:
                o.error("REQ[{}] Failed to access key in payload of multi tasks({}/{}) for task '{}'. {}".format(request_id, i, n, executor_id, str(e)))
            d = {'total': n, 'seq': i, 'executor_id': executor_id, 'status': 'failure'}
            summary.append(d)
            if force_execute:
                continue
            else:
                return summary 

        try:
            if accept_feeds:
                kwargs = {'feeds': feeds}
            else:
                kwargs = {}

            res =  settings.executors[executor_id].execute(request_id, config_path, kafka, **kwargs)

            executed = False
            for x in executors:
                for k, v in x.items():
                    if k == executor_id:
                        res = v(request_id, config_path, **kwargs)
                        executed = True
                        break
                if executed:
                    break
            else:
                msg = "Executor not found in executor list. '{}'".format(executor_id)
                res = response_BAD_REQUEST(request_id, msg, kafka)

            if res['status_code'] == 200 or res['status_code'] == 202:
                d = {'total': n, 'seq': i, 'executor_id': executor_id, 'status': 'success'}
                summary.append(d)
                d['output'] = res
                feeds.append(d)
            else:
                with TpaLogger(**kafka) as o:
                    o.error("REQ[{}] Failed to execute multi tasks({}/{}) for task '{}'. {}".format(request_id, i, n, executor_id, res['message']))
                d = {'total': n, 'seq': i, 'executor_id': executor_id, 'status': 'failure'}
                summary.append(d)
                if force_execute:
                    d['output'] = res
                    feeds.append(d)
                else:
                    return summary 
        except KeyError as e:
            with TpaLogger(**kafka) as o:
                o.error("REQ[{}] Failed to access key in response of multi tasks({}/{}) for task '{}'. {}".format(request_id, i, n, executor_id, str(e)))
            d = {'total': n, 'seq': i, 'executor_id': executor_id, 'status': 'failure'}
            summary.append(d)
            if force_execute:
                d['output'] =  message
                feeds.append(d)
            else:
                return summary
    return summary

class ExecMultiTasks(tornado.web.RequestHandler):
    def initialize(self, executors):
        self.executors = executors

    def post(self):
        request_id = 'NIY'       # for exceptin case.
        try:
            data = json.loads(self.request.body)
            tasks = data['tasks']
        except ValueError as e:
            msg = "REQ[{}] Failed to process payload of multi tasks. {}".format(request_id, str(e))
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return

        summary = _execute_multi_tasks(request_id, tasks, self.executors, force_execute=False)
        results = json.dumps(summary)
        res = response_OK(request_id, "Completed.", results, kafka)
        self.set_status(res['status_code'])
        self.finish(res)

class ExecMultiTasksForceExecute(tornado.web.RequestHandler):
    def initialize(self, executors):
        self.executors = executors

    def post(self):
        request_id = 'NIY'       # for exceptin case.
        try:
            data = json.loads(self.request.body)
            tasks = data['tasks']
        except ValueError as e:
            msg = "REQ[{}] Failed to process payload of multi tasks. {}".format(request_id, str(e))
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
            return

        summary = _execute_multi_tasks(request_id, tasks, force_execute=True)
        results = json.dumps(summry)
        res = response_OK(request_id, "Completed", results, kafka)
        self.set_status(res['status_code'])
        self.finish(res)

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

def _initialize_task_executors(**kwargs):
    p = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port']}
    lst = []
    # FatalError is catched by caller.
    request_id = 'NIY'
    for x, v in settings.executors.items():
        lst.append({ x: v.get_executor(request_id, **p)})
    return lst

def main():
    provider_name = settings.identity['name']
    with TpaLogger(**kafka) as o:
        o.info("Initializing {}...".format(provider_name))

    try:
        executors = _initialize_task_executors(**kafka)
    except FatalError as e:
        with TpaLogger(**kafka) as o:
            o.error("Failed to initialize task executor. {}.".format(str(e)))
            o.error("Exiting {}...".format(provider_name))
        sys.exit(1)

    signal.signal(signal.SIGINT, _signal_handler)
    tornado.options.parse_command_line()
    application = tornado.web.Application(
        [
            (r'/', WhoAmI),
            (r'/api/v0/whoami', WhoAmI),

            # --- Execute a task --- #
            # Args:
            #   Executer id        e.g. resource_puller
            # Payload
            #   'request_id': request id 
            #   'config_path': configuration file path obtained via configurator
            #   'format': (optional)
            (r'/api/v0/task/([^/]+)/exec', ExecTask, dict(executors=executors)),

            # --- Execute tasks (terminates on any task execution failure) --- #
            # Args:
            #   None 
            # Payload
            #   [
            #       {
            #           'request_id': request id 
            #           'executor_id': executor id
            #           'config_path': configuration file path obtained via configurator
            #           'accept_feeds': 'ture' when the executor needs feeds from prev executors
            #       },
            #       ...
            #   ]
            (r'/api/v0/tasks/multitasks_executor/exec', ExecMultiTasks, dict(executors=executors)),

            # --- Execute tasks (force executing all tasks)--- #
            # Args:
            #   None 
            # Payload
            #   [
            #       {
            #           'request_id': request id 
            #           'executor_id': executor id
            #           'config_path': configuration file path obtained via configurator
            #           'accept_feeds': 'ture' when the executor needs feeds from prev executors
            #       },
            #       ...
            #   ]
            (r'/api/v0/tasks/multitasks_executor/exec/force_execute', ExecMultiTasksForceExecute, dict(executors=executors))

        ])

    port = settings.server['http']['port']
    with TpaLogger(**kafka) as o:
        o.info("Starting {}@{}:{} (pid: {})...".format(provider_name, socket.gethostname(), port, os.getpid()))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()

