import os
import json
import hashlib

from ....common.common import FatalError
from ....common.common import TpaLogger
from ....common.common import GET, PUT
from ....common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR, response_NOT_FOUND
from ....common.common import save_text, gen_sha1_from_file_context
from . import settings

TRANSIFEX_API = 'https://www.transifex.com/api/2'

def _get_resource_stats(request_id, creds, local_cache_root_dir, kafka, **kwargs):
    try:
        pslug = kwargs['pslug']
        rslug = kwargs['rslug']
        url = '{}/project/{}/resource/{}/stats/'.format(TRANSIFEX_API, pslug, rslug)
        r = GET(url, request_id, auth=creds)
        return response_OK(request_id, "Resource status.", r, kafka)
    except FatalError as e:
        return response_INTERNAL_SERVER_ERROR(request_id, "Failed to get resource status. {}".format(str(e)), kafak)

def _get_translation_stats(request_id, creds, local_cache_root_dir, kafka, **kwargs):
    try:
        pslug = kwargs['pslug']
        rslug = kwargs['rslug']
        lang = kwargs['lang']
        url = '{}/project/{}/resource/{}/stats/{}/'.format(TRANSIFEX_API, pslug, rslug, lang)
        r = GET(url, request_id, auth=creds)
        return response_OK(request_id, "Translation status.", r, kafka)
    except FatalError as e:
        return response_INTERNAL_SERVER_ERROR(request_id, "Failed to get translation status. {}".format(str(e)), kafak)

def _get_translation(request_id, creds, pslug, rslug, lang):
    try:
        url = '{}/project/{}/resource/{}/translation/{}/'.format(TRANSIFEX_API, pslug, rslug, lang)
        j = GET(url, request_id, auth=creds)
        return j['content']
    except KeyError as e:
        raise FatalError("Failed to access key in translation. '{}'." .format(str(e)))

def _download_file_context(request_id, creds, local_cache_root_dir, kafka, **kwargs):
    # always download the file from Transifex.
    try:
        pslug = kwargs['pslug']
        rslug = kwargs['rslug']
        lang = kwargs['lang']
        context = _get_translation(request_id, creds, pslug, rslug, lang)
    except FatalError as e:
        # pslug, rslug and lang has to be valid value.
        msg = "Failed to download file context. {}".format(str(e))
        return response_BAD_REQUEST(request_id, msg, kafka)

    # store the context in cache directory. 
    try:
        projdir = os.path.join(local_cache_root_dir, pslug)
        if not (os.path.exists(projdir) and os.path.isdir(projdir)):
            os.makedirs(projdir)
    except OSError as e:
        msg = "Failed to create project dir. {}".format( str(e))
        raise FatalError(message)
    
    try:
        path = os.path.join(projdir, rslug + '_' + lang + '.context')
        save_text(path, context)
        sha1 = gen_sha1_from_file_context(path)
        return response_OK(request_id, "Completed.", {'file_path': path, 'sha1': sha1, 'context': context}, kafka)
    except FatalError as e:
        msg = "Failed to download file context. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

def _upload_resource_file_context(request_id, creds, local_cache_root_dir, kafka, **kwargs):
    try:
        pslug = kwargs['pslug']
        rslug = kwargs['rslug']
        context = json.dumps(kwargs['context'])
    except KeyError as e:
        msg = "Failed to access key in put resource file context kwargs. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except ValueError as e:
        msg = "Failed to load context as json. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    try:
        url = '{}/project/{}/resource/{}/content/'.format(TRANSIFEX_API, pslug, rslug)
        data=json.dumps({"content": context})
        headers = {'Content-type': 'application/json'}
        r = PUT(url, request_id, creds, data)
        return response_OK(request_id, "Resource file uploaded.", {'platform': 'transifex', 'pslug': pslug, 'rslug': rslug, 'context': context, 'response': r}, kafka)
    except FatalError as e:
        msg = "Failed to put resource file context. '{}'." .format(str(e))
        # FIXME --- this could be 400 from Transifex but cannot know abuot it here b/c 
        #           PUT catches the exception and re-raise it as FatalError.
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

commands = {
        'get_file_context': _download_file_context,
        'put_resource_file_context': _upload_resource_file_context,
        'get_resource_stats': _get_resource_stats,
        'get_translation_stats': _get_translation_stats
        }

def _init_cache_dir(request_id):
    try:
        localdir = settings.local_cache_dir
        if os.path.exists(localdir) and os.path.isdir(localdir):
            return localdir
        else:
            os.makedirs(localdir)
            return localdir
    except KeyError as e:
        raise FatalError("Failed to access key in repo config file. '{}'".format(str(e)))
    except OSError as e:
        raise FatalError("Failed to create local cache dir. '{}' {}".format(localdir, str(e)))

def _get_creds(request_id):
    try:
        return {'userfullname': settings.creds['userfullname'],
            'username': settings.creds['username'],
            'userpasswd': settings.creds['userpasswd'],
            'useremail': settings.creds['useremail']}
    except KeyError as e:
        raise FatalError("Failed to access key in creds config file. '{}'".format(str(e)))

def get_carrier(request_id, **kwargs):
    kafka = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port'],
        'topic': settings.kafka['topic'],
        'key': 'default'}

    initialized = False
    try:
        local_cache_root_dir = _init_cache_dir(request_id)
        creds = _get_creds(request_id)
        initialized = True
    except FatalError as e:
        message = "Failed to initialize carrier. {}".format(str(e))
        error(message, request_id)

    def _dispatcher(request_id, command, **kwargs):
        if not initialized:
            msg = "Carrier is not operational due to initialization error."
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
        try:
            # request_id, creds, local_repo_root_dir are mandatory args for all commands.
            return commands[command](request_id, creds, local_cache_root_dir, kafka, **kwargs)
        except KeyError as e:
            msg = "Command not found in commands list. '{}'.".format(command)
            return response_BAD_REQUEST(request_id, msg, kafka)

    return _dispatcher

