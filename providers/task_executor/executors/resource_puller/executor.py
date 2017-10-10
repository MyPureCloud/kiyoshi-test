import json


from common.common import FatalError
from common.common import POST
from common.common import TpaLogger 
from common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR
import task_executor.settings
import settings

def execute(request_id, config_path, kafka, **kwargs):
    """ This executor consumes no kwargs. """
    try:
        url = "{}/repository/pull".format(task_executor.settings.providers['repository_carrier']['api'])
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({'request_id': request_id, 'config_path': config_path})
        r = POST(url, request_id, headers=headers, data=payload)
        msg = "Executed. Pulled repository for '{}'.".format(config_path)
        return response_OK(request_id, msg, '', kafka)
    except FatalError as e:
        return response_BAD_REQUEST(request_id, str(e), kafka)
    except KeyError as e:
        msg = "Failed to access key in providers list. {}".format(str(e))
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

