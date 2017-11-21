"""
How to run configurator
=======================
$ cd translation-process-automation
$ python3 -m providers.configurator.server
"""
import os
import sys
import signal
import socket
from urllib.parse import unquote 
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

from . import settings
from ..common.common import FatalError
from ..common.common import TpaLogger
from ..common.common import response_BAD_REQUEST

# All configurators share this provider, however, topic and key are specific to this module.
kafka = {
    'broker_server': settings.kafka['brokers'][0]['server'],
    'broker_port': settings.kafka['brokers'][0]['port'],
    'topic': settings.kafka['topic'],
    'key': settings.kafka['key']}

class WhoAmI(tornado.web.RequestHandler):
    def get(self):
        with TpaLogger(**kafka) as o:
            o.info(self.request.uri)
        d = {'type': settings.identity['type'], 'name': settings.identity['name']}
        self.finish("{}".format(d))

class ListProjectIds(tornado.web.RequestHandler):
    def initialize(self, configurators):
        self.configurators = configurators

    def get(self, configurator_name):
        request_id = 'NIY'
        name = unquote(configurator_name)
        with TpaLogger(**kafka) as o:
            o.info(self.request.uri)
        for x in self.configurators:
            for k, v in x.items():
                if k == name:
                    res = v(request_id, 'list_project_ids')
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
        else:
            msg = "Configurator not found in configurator list. '{}'".format(name)
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

class ProjectConfigurationFile(tornado.web.RequestHandler):
    def initialize(self, configurators):
        self.configurators = configurators

    def get(self, configurator_name, project_id):
        request_id = 'NIY'
        name = unquote(configurator_name)
        projid = unquote(project_id)
        with TpaLogger(**kafka) as o:
            o.info(self.request.uri)
        for x in self.configurators:
            for k, v in x.items():
                if k == name:
                    res = v(request_id, 'get_project_configuration', project_id=projid)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
        else:
            msg = "Configurator not found in configurator list. '{}'".format(name)
            kp = create_kafka_producer()
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

class ProjectJobConfiguration(tornado.web.RequestHandler):
    def initialize(self, configurators):
        self.configurators = configurators

    def get(self, configurator_name, project_id, job_id):
        request_id = 'NIY'
        name = unquote(configurator_name)
        projid = unquote(project_id)
        jobid = unquote(job_id)
        with TpaLogger(**kafka) as o:
            o.info(self.request.uri)
        for x in self.configurators:
            for k, v in x.items():
                if k == name:
                    res = v(request_id, 'get_project_job_configuration', project_id=projid, job_id=jobid)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
        else:
            msg = "Configurator not found in configurator list. '{}'".format(name)
            kp = create_kafka_producer()
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

class ConfigurationFile(tornado.web.RequestHandler):
    def initialize(self, configurators):
        self.configurators = configurators

    def get(self, configurator_name, config_path):
        request_id = 'NIY'
        name = unquote(configurator_name)
        path = unquote(config_path)
        with TpaLogger(**kafka) as o:
            o.info(self.request.uri)
        for x in self.configurators:
            for k, v in x.items():
                if k == name:
                    res = v(request_id, 'get_configuration_by_path', path=path)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
        else:
            msg = "Configurator not found in configurator list. '{}'".format(name)
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

class UploadableResourceAndTranslationFiles(tornado.web.RequestHandler):
    def initialize(self, configurators):
        self.configurators = configurators

    def get(self, configurator_name, project_id):
        request_id = 'NIY'
        name = unquote(configurator_name)
        projid = unquote(project_id)
        with TpaLogger(**kafka) as o:
            o.info(self.request.uri)
        for x in self.configurators:
            for k, v in x.items():
                if k == name:
                    res = v(request_id, 'get_uploadable_resource_and_translation_files', project_id=projid)
                    self.set_status(res['status_code'])
                    self.finish(res)
                    return
        else:
            msg = "Configurator not found in configurator list. '{}'".format(name)
            kp = create_kafka_producer()
            res = response_BAD_REQUEST(request_id, msg, kafka)
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

def _initialize_configurators(**kwargs):
    p = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port']}
    lst = []
    # FatalError is catched by caller.
    for x, v in settings.configurators.items():
        lst.append({ x: v.get_configurator('reqid_configurators_init', **p)})
    return lst

def main():
    provider_name = settings.identity['name']
    with TpaLogger(**kafka) as o:
        o.info("Initializing {}...".format(provider_name))

    try:
        configurators = _initialize_configurators(**kafka)
    except FatalError as e:
        with TpaLogger(**kafka) as o:
            o.error("Failed to initialize configurator. {}.".format(str(e)))
            o.error("Exiting {}...".format(provider_name))
        sys.exit(1)

    signal.signal(signal.SIGINT, _signal_handler)
    tornado.options.parse_command_line()
    application = tornado.web.Application(
        [
            (r'/', WhoAmI),
            (r'/api/v0/whoami', WhoAmI),

            # --- List project ids --- #
            # Args:
            #   configurator id     e.g. tpa
            (r'/api/v0/configuration/([^/]+)/projects', ListProjectIds, dict(configurators=configurators)),

            # --- Project configuraton file context --- #
            # Args:
            #   configurator id     e.g. tpa
            #   Project id          e.g. sandbag
            (r'/api/v0/configuration/([^/]+)/project/([^/]+)', ProjectConfigurationFile, dict(configurators=configurators)),

            # --- Project job configuraton context --- #
            # Args:
            #   configurator id     e.g. tpa
            #   Project id          e.g. sandbag
            #   Job id              e.g. resource_upload
            (r'/api/v0/configuration/([^/]+)/project/([^/]+)/job/([^/]+)', ProjectJobConfiguration, dict(configurators=configurators)),

            # --- Supportive project configuration file context --- #
            # Args:
            #   configurator id     e.g. tpa
            #   Path            path of configuraton file.              
            (r'/api/v0/configuration/([^/]+)/path=([^/]+)', ConfigurationFile, dict(configurators=configurators)),



            # --- List of uploadable resource and translation files in project --- #
            # Args:
            #   configurator id     e.g. tpa
            #   Project id          e.g. sandbag
            (r'/api/v0/configuration/([^/]+)/project/([^/]+)/uploadablefiles', UploadableResourceAndTranslationFiles, dict(configurators=configurators)),

        ])

    port = settings.server['http']['port']
    with TpaLogger(**kafka) as o:
        o.info("Starting {}@{}:{} (pid: {})...".format(provider_name, socket.gethostname(), port, os.getpid()))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()

