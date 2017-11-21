import os
import json
import hashlib
import difflib

from ....common.common import FatalError
from ....common.common import GET
from ....common.common import TpaLogger
from ....common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR, response_ACCEPTED
from ..helper import get_config_context, get_context_from_translation_platform, get_context_from_resource_repository
from . import settings

def _text(feeds, show_diff):
    text = ''

    # summary
    #
    summary = []
    num_failure = 0
    for x in feeds:
        response = x['output']['results']
        platform_name = response['platform']
        repo_owner = response['owner']
        repo_name = response['name']

        if x['status'] == 'success':
            num_difference = 0
            for r in response['resources']:
                if r['identical'] == 'true':
                    pass 
                else:
                    num_difference += 1
            summary.append({'name': "{}/{}/{}".format(platform_name, repo_owner, repo_name), 'status': 'success', 'total': len(response['resources']), 'diffs': num_difference})
        else:
            summary.append({'name': "{}/{}/{}".format(platform_name, repo_owner, repo_name), 'status': 'failure'})
            num_failure += 1

    text += "\n{}\n".format("SUMMARY")
    text += "{}\n".format("=======")
    if num_failure >= 1:
        text += "{}\n".format("Failed to compare resource(s) on following repository(s):")
        for x in summary:
            if x['status'] == 'failure':
                text += "\t{}\n".format(x['name'])

    text += "{}\n".format("Repositories with different resources:")
    count = 0
    for x in summary:
        if x['status'] == 'success' and x['diffs'] >= 1:
            text += "\t{} ({}/{})\n".format(x['name'], x['diffs'], x['total'])
            count += 1
    if count == 0:
            text += "\t{}\n".format("(None)")

    text += "{}\n".format("Repositories with identical resources:")
    count = 0
    for x in summary:
        if x['status'] == 'success' and x['diffs'] == 0:
            text += "\t{} ({}/{})\n".format(x['name'], x['total'], x['total'])
            count += 1
    if count == 0:
            text += "\t{}\n".format("(None)")

    if show_diff == False:
        return text

    # details w/ diff
    #
    text += "\n\n{}\n".format("DETAILS")
    text += "{}\n".format("=======")

    for x in feeds:
        response = x['output']['results']
        platform_name = response['platform']
        repo_owner = response['owner']
        repo_name = response['name']
        text += "\n{}/{}/{}\n".format(platform_name, repo_owner, repo_name)
        if x['status'] == 'success':
            for r in response['resources']:
                if r['identical'] != 'true':
                    text += "\t{}\n".format(r['file_path'])
                    for s in r['diff']:
                        text += "\t\t{}\n".format(s)
            text = "{}\n".format(text)

    return text

def execute(request_id, config_path, kafka, **kwargs):
    try:
        # FIXME
        # Always use tpa configurator for now but it should be explicitly
        # specified.
        configurator_id = 'tpa'
        formatter_config = get_config_context(request_id, configurator_id, config_path, 'formatter_configuration')
        style = formatter_config['format']
    except FatalError as e:
        msg = "Failed to get config context. {}".format(str(e))
        return response_BAD_REQUEST(request_id, msg, kafka)
    except KeyError as e:
        msg = "Failed to access key in formatter config context. {} {}".format(config_path, str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    if 'feeds' in kwargs:
        feeds = kwargs['feeds']
    else:
        msg = "NOP. No feeds given to resource_comparator_fomatter."
        return response_ACCEPTED(request_id, msg, '', kafka)
    
    if style == 'text':
        return response_OK(request_id, "Executed.", _text(feeds, show_diff=True), kafka)
    elif style == 'text_summary':
        return response_OK(request_id, "Executed.", _text(feeds, show_diff=False), kafka)
    else:
        msg = "Executed as text format due to unknown format specified. '{}'.".format(style)
        return response_OK(request_id, msg, _text(feeds, show_diff=True), kafka)

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


