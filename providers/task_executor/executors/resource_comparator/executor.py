import os
import json
import hashlib
import difflib

from ....common.common import FatalError
from ....common.common import GET
from ....common.common import TpaLogger 
from ....common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR
from ..helper import get_config_context, get_context_from_translation_platform, get_context_from_resource_repository
from . import settings

def _summary(results):
    ''' Text output such as... 
        
        <platform/owner/repo_name>
            file1_path
            file2_path      DIFFERENT
            file3_path

        Only indicates 'DIFFERENT' on files, whch have diffs.
    '''
    text = "\n{}/{}/{}\n".format(results['platform'], results['owner'], results['name'])
    for x in results['resources']:
        if x['identical'] == 'true':
            text += "\t{}\n".format(x['file_path'])
        else:
            text += "\t{}\t\tDIFFERENT\n".format(x['file_path'])
    text = "{}\n".format(text)
    return text

def _format(style, results):
    default_style = 'raw_results'
    if style == 'raw_results':
        return results
    elif style == 'summary':
        return _summary(results)
    else:
        return results

def execute(request_id, config_path, kafka, **kwargs):
    if 'format' in kwargs:
        style =  kwargs['format']
    else:
        style = 'raw_results'

    # we need resource and translation configuraton files to find out what files to compare. 
    try:
        configurator_id = 'tpa'
        uploader_config = get_config_context(request_id, configurator_id, config_path, 'uploader_configuration')
        resource_config = get_config_context(request_id, configurator_id, uploader_config['resource_config_path'], 'resource_configuration')
        translation_config = get_config_context(request_id, configurator_id, uploader_config['translation_config_path'], 'translation_configuration')
    except FatalError as e:
        msg = "Failed to get config context. {}".format(str(e))
        return response_BAD_REQUEST(request_id, msg, kafka)

    resource_platform = resource_config['repository']['platform']
    repo_owner = resource_config['repository']['owner']
    repo_name = resource_config['repository']['name']
    lst =[]
    for x in resource_config['repository']['resources']:
        resource_file_full_path = os.path.join(repo_owner, repo_name, x['path'])
        try:
            translation_file = get_context_from_translation_platform(request_id, resource_file_full_path, translation_config)
        except FatalError as e:
            msg = "Failded to get translaton context. {}".format(str(e))
            with TpaLogger(**kafka) as o:
                o.error(msg)
            lst.append({'file_path': x['path'], 'results': msg})
            continue

        try:
            resource_file = get_context_from_resource_platform(request_id, resource_platform, repo_name, x['path'])
        except FatalError as e:
            msg = "Failded to get resource context. {}".format(str(e))
            with TpaLogger(**kafka) as o:
                o.error(msg)
            lst.append({'file_path': x['path'], 'results': msg})
            continue

        if resource_file['sha1'] == translation_file['sha1']:
            lst.append({'file_path': x['path'], 'identical': 'true', 'diff': None})
        else:
            diff = difflib.unified_diff(resource_file['context'].splitlines(), translation_file['context'].splitlines())
            delta = []
            for d in diff:
                delta.append(d)
            lst.append({'file_path': x['path'], 'identical': 'false', 'diff': delta})

    results = {'platform': resource_platform, 'owner': repo_owner, 'name': repo_name, 'resources': lst}

    return response_OK(request_id, "Executed", _format(style, results), kafka)

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

    
