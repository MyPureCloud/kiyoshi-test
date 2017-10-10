"""
TPA Configurator


"""
import os
import json

from common.common import FatalError
from common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR
import settings

def _get_configuration_by_path(request_id, kafka, **kwargs):
    try:
        config_path = kwargs['path']
        path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), config_path))
        if not os.path.isfile(path):
            msg = "REQ[{}] Config file not found. '{}'".format(request_id, path)
            return response_BAD_REQUEST(request_id, msg, kafka)

        with open(path, 'r') as fi:
            data = json.load(fi)
        msg = "Context of '{}'.".format(path)
        return response_OK(request_id, msg, data, kafka)
    except IOError as e:
        msg = "REQ[{}] Failed to process config file. '{}' {}".format(request_id, path, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except ValueError as e:
        msg = "REQ[{}] Failed to process config file context. '{}' {}".format(request_id, path, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

def _get_project_configuration(request_id, kafka, **kwargs):
    try:
        project_id = kwargs['project_id']
        index_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config/projects/index.json'))
        if not os.path.isfile(index_path):
            msg = "REQ[{}] Index file not found. '{}'".format(request_id, index_path)
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

        with open(index_path, 'r') as fi:
            index = json.load(fi)
    except IOError as e:
        msg = "REQ[{}] Failed to process index file. {}".format(request_id, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except ValueError as e:
        msg = "REQ[{}] Failed to process index file. {}".format(request_id, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    try:
        for x in index['projects']:
            if x['id'] == project_id:
                config_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), x['config_path']))
                with open(config_path, 'r') as fi:
                    context = json.load(fi)
                    msg = "Context of {} project config.".format(project_id)
                    return response_OK(request_id, msg, context, kafka)
        else:
            msg = "Project not found. '{}'".format(project_id)
            return response_BAD_REQUEST(request_id, msg, kafka)
    except IOError as e:
        msg = "REQ[{}] Failed to process project file. '{}' {}".format(request_id, config_path, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except ValueError as e:
        msg = "REQ[{}] Failed to process project file. '{}' {}".format(request_id, config_path, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except KeyError as e:
        msg = "REQ[{}] Failed to access key in  project file. '{}' {}".format(request_id, x['config_path'], str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

def _list_project_ids(request_id, kafka):
    try:
        index_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config/projects/index.json'))
        if not os.path.isfile(index_path):
            msg = "REQ[{}] Index file not found. '{}'".format(request_id, index_path)
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

        with open(index_path, 'r') as fi:
            index = json.load(fi)

        lst = []
        for x in index['projects']:
            lst.append(x['id'])
        msg = "Listed {} project(s).".format(len(lst))
        return response_OK(request_id, msg, lst, kafka)
    except IOError as e:
        msg = "REQ[{}] Failed to process index file. {}".format(request_id, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except ValueError as e:
        msg = "REQ[{}] Failed to process index file. {}".format(request_id, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

commands = {
        'get_configuration_by_path': _get_configuration_by_path,
        'get_project_configuration': _get_project_configuration,
        'list_project_ids': _list_project_ids
        }

def get_configurator(request_id, **kwargs):
    kafka = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port'],
        'topic': settings.kafka['topic'],
        'key': 'default'}

    # nothing special for now
    initialized = True

    def _dispatcher(request_id, command, **kwargs):
        if not initialized:
            msg = "REQ[{}] Configurator is not operational due to initialization error.".format(request_id)
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
        try:
            return commands[command](request_id, kafka, **kwargs)
        except KeyError as e:
            msg = "Command not found in commands list. '{}'.".format(command)
            return response_BAD_REQUEST(request_id, msg, kafka)

    return _dispatcher

