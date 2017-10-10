import os
import sys
import signal
import json
import socket
#import urllib
try:
    from urllib import quote, unquote  # py2
except ImportError:
    from urllib.parse import quote, unquote  # py3

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.options

import settings
from common.common import FatalError
from common.common import GET
from common.common import TpaLogger
from common.common import response_OK, response_BAD_REQUEST

# All configurators share this provider, however, topic and key are specific to this module.
kafka = {
    'broker_server': settings.kafka['brokers'][0]['server'],
    'broker_port': settings.kafka['brokers'][0]['port'],
    'topic': settings.kafka['topic'],
    'key': settings.kafka['key']}

class WhoAmI(tornado.web.RequestHandler):
    def get(self):
        d = {'type': settings.identity['type'], 'name': settings.identity['name']}
        self.finish("{}".format(d))

class FileContextByPath(tornado.web.RequestHandler):
    def initialize(self, carriers):
        self.carriers = carriers

    def get(self, platform_name, repository_name, file_path):
        request_id = 'NYI'
        try:
            carrier_name = unquote(platform_name)
            repo = unquote(repository_name)
            path = unquote(file_path)
            for x in self.carriers:
                for k, v in x.items():
                    if k == carrier_name:
                        res = v(request_id, 'get_file_context', repo_name=repo, file_path=path)
                        self.set_status(res['status_code'])
                        self.finish(res)
                        return
            else:
                msg = "Carrier not found in carrier list. '{}'".format(carrier_name)
                res = response_BAD_REQUEST(request_id, msg, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
        except FatalError as e:
            msg = "Failed to check file existence. '{}/{}' {}".format(repo, path, str(e))
            res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

class FileContextByLanguageId(tornado.web.RequestHandler):
    def initialize(self, carriers):
        self.carriers = carriers

    def get(self, platform_name, project_slug, resource_slug, language_code):
        request_id = 'NYI'
        try:
            carrier_name = unquote(platform_name)
            pslug = unquote(project_slug)
            rslug = unquote(resource_slug)
            lang = unquote(language_code)
            for x in self.carriers:
                for k, v in x.items():
                    if k == carrier_name:
                        res = v(request_id, 'get_file_context', pslug=pslug, rslug=rslug, lang=lang)
                        self.set_status(res['status_code'])
                        self.finish(res)
                        return
            else:
                msg = "Carrier not found in carrier list. '{}'".format(carrier_name)
                res = response_BAD_REQUEST(request_id, msg, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
        except FatalError as e:
            msg = "Failed to get file context. '{}/{}' {}".format(repo, path, str(e))
            res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

def _get_configuration_context(request_id, configurator_id, config_path):
    url = "{}/configuration/{}/path={}".format(settings.providers['configurator']['api'], configurator_id, quote(config_path, safe=''))
    r = GET(url, request_id)
    return r['results']

class FileExists(tornado.web.RequestHandler):
    def initialize(self, carriers):
        self.carriers = carriers

    def get(self, platform_name, repository_name, file_path):
        request_id = 'NYI'
        try:
            carrier_name = unquote(platform_name)
            repo = unquote(repository_name)
            path = unquote(file_path)
            for x in self.carriers:
                for k, v in x.items():
                    if k == carrier_name:
                        res = v(request_id, 'file_exists', repo_name=repo, file_path=path)
                        self.set_status(res['status_code'])
                        self.finish(res)
                        return
            else:
                msg = "Carrier not found in carrier list. '{}'".format(carrier_name)
                res = response_BAD_REQUEST(request_id, msg, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
        except FatalError as e:
            msg = "Failed to check file existence. '{}/{}' {}".format(repo, path, str(e))
            res = response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)

class Pull(tornado.web.RequestHandler):
    def initialize(self, carriers):
        self.carriers = carriers

    def post(self):
        request_id = 'NYI'
        try:
            data = json.loads(self.request.body)
            request_id = data['request_id']
            config_path = data['config_path']
            # FIXME --- since we have only tpa configurator, assume configurator is
            #           always tpa configurator. But it should be explicitly be specified
            #           via API param or payload.
            configurator_id = 'tpa'
            config = _get_configuration_context(request_id, configurator_id, config_path)
            carrier_name = config['repository']['platform']
            for x in self.carriers:
                for k, v in x.items():
                    if k == carrier_name:
                        res = v(request_id, 'pull', config=config)
                        self.set_status(res['status_code'])
                        self.finish(res)
                        return
            else:
                msg = "Carrier not found in carrier list. '{}'".format(carrier_name)
                res = response_BAD_REQUEST(request_id, msg, kafka)
                self.set_status(res['status_code'])
                self.finish(res)
        except FatalError as e:
            msg = "Failed to get configuration context for {}. {}".format(config_path, str(e))
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
        except ValueError as e:
            msg = "Failed to process payload for pull. {}".format(str(e))
            res = response_BAD_REQUEST(request_id, msg, kafka)
            self.set_status(res['status_code'])
            self.finish(res)
        except KeyError as e:
            msg = "Failed to access key in payload for pull. {}".format(str(e))
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

def _initialize_carriers(**kwargs):
    p = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port']}
    lst = []
    try:
        for x, v in settings.repository_carriers.items():
            lst.append({ x: v.get_carrier('reqid_repository_carrier_init', **p)})
        return lst
    except FatalError as e:
        with TpaLogger(**kafka) as o:
            o.error("Exiting due to repository carrier initialization failure. {}.".format(str(e)))
        sys.exit(1)

def main():
    provider_name = settings.identity['name']
    with TpaLogger(**kafka) as o:
        o.info("Initializing {}...".format(provider_name))

    carriers = _initialize_carriers(**kafka)
    signal.signal(signal.SIGINT, _signal_handler)
    tornado.options.parse_command_line()
    application = tornado.web.Application(
        [
            (r'/', WhoAmI),
            (r'/api/v0/whoami', WhoAmI),
            
            # NOTE:
            # APIs does not handle 'organization' name, such as MyPureCloud.
            #

            # ---  File context --- #
            # 
            # This is for platforms such as Github, Bitbucket, where files can be located by file paths.
            # Args:
            #   platform name           eg. bitbucket
            #   repository name         e.g. web-directory
            #   file path               e.g. translations/en-us.json
            (r'/api/v0/repository/platform/([^/]+)/repo/([^/]+)/file/path=([^/]+)', FileContextByPath, dict(carriers=carriers)),
            # 
            # This is for platforms such as Transifex, where files are identified by ids/slugs and language.
            # Args:
            #   platform name           eg. transifex
            #   project id/slag 
            #   resource id/slag 
            #   language code           eg. es
            (r'/api/v0/repository/platform/([^/]+)/project/([^/]+)/resource/([^/]+)/lang/([^/]+)', FileContextByLanguageId, dict(carriers=carriers)),

            # ---  File existence --- #
            # 
            # This is for platforms such as Github, Bitbucket, where files can be located by file paths.
            # Args:
            #   platform name           eg. bitbucket
            #   repository name         e.g. web-directory
            #   file path               e.g. translations/en-us.json
            (r'/api/v0/repository/platform/([^/]+)/repo/([^/]+)/file/path=([^/]+)/exists', FileExists, dict(carriers=carriers)),

            # --- Pull repository --- #
            # 
            # This is for platforms such as Github, Bitbucket.
            # Args:
            #   None
            # POST Payload
            #   'request_id': request ID.
            #   'config_path': configuration file path, which is obtained via configurator.
            (r'/api/v0/repository/pull', Pull, dict(carriers=carriers))
            # OR
            #(r'/api/v0/repository/platform/{}/repo/{}/pull', PullRepository, dict(carriers=carriers))
        ])

    port = settings.server['http']['port']
    with TpaLogger(**kafka) as o:
        o.info("Starting {}@{}:{} (pid: {})...".format(provider_name, socket.gethostname(), port, os.getpid()))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()

