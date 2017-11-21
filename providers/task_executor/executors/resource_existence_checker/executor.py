import json
from urllib.parse import quote

from ....common.common import FatalError
from ....common.common import GET
from ....common.common import TpaLogger 
from ....common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR
from ..helper import get_config_context, repository_file_exists
from . import settings

def execute(request_id, config_path, kafka, **kwargs):
    """ This executor consumes no kwargs. """
    try:
        configurator_id = 'tpa'
        resource_config = get_config_context(request_id, configurator_id, config_path, 'resource_configuration')
    except FatalError as e:
        msg = "Failed to get config context. {}".format(str(e))
        return response_BAD_REQUEST(request_id, msg, kafka)

    results =[]
    try:
        platform = resource_config['repository']['platform']
        repo_name = resource_config['repository']['name']
        for x in resource_config['repository']['resources']:
            if repository_file_exists(request_id, platform, repo_name, x['path']):
                results.append({'file_path': x['path'], 'exists': "ture"})
            else:
                results.append({'file_path': x['path'], 'exists': "false"})
        return response_OK(request_id, "Executed.", results, kafka)
    except FatalError as e:
        return response_BAD_REQUEST(request_id, str(e), kafka)
    except KeyError as e:
        msg = "Failed to access key in resource config. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

def get_executor(request_id, **kwargs):
    kafka = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port'],
        'topic': settings.kafka['topic'],
        'key': 'default'}

    # nothing special for now
    initialized = True

    def _executor(request_id, config_path, **kwargs):
        if initialized:
            return execute(request_id, config_path, kafka, **kwargs)
        else:
            msg = "REQ[{}] {} is not operational due to initialization error.".format(request_id, settings.identity['name'])
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    return _executor


