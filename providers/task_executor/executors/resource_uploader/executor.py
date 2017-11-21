import os
import json
import hashlib
import difflib

from ....common.common import FatalError
from ....common.common import GET
from ....common.common import TpaLogger 
from ....common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR
from ..helper import get_config_context, get_context_from_translation_platform, get_context_from_resource_repository, upload_context_to_translation_platform
from . import settings

def execute(request_id, config_path, kafka, **kwargs):
    """
    No kwargs used.
    """

    # Pick up config files. 
    try:
        configurator_id = 'tpa'
        uploader_config = get_config_context(request_id, configurator_id, config_path, 'uploader_configuration')
        resource_config = get_config_context(request_id, configurator_id, uploader_config['resource_config_path'], 'resource_configuration')
        translation_config = get_config_context(request_id, configurator_id, uploader_config['translation_config_path'], 'translation_configuration')
    except KeyError as e:
        msg = "Failed to access key in uploader config file. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except FatalError as e:
        msg = "Failed to get config context. {}".format(str(e))
        return response_BAD_REQUEST(request_id, msg, kafka)

    # Create list of uploadable resource files. A uploadable resource has to be listed in both resoruce configuration
    # and translation configuration. If a resource file is listed in only one of those configuration, do not count 
    # it as uploadable.
    try:
        resource_platform = resource_config['repository']['platform']
        resource_repository_name = resource_config['repository']['name']
        resource_branch = resource_config['repository']['branch']
        translation_platform = translation_config['platform']
        translation_project_name = translation_config['project']['name']
        translation_project_slug = translation_config['project']['slug']
        uploadables = [] 
        for x in resource_config['repository']['resources']:
            resource_full_path = os.path.join(resource_config['repository']['owner'], resource_config['repository']['name'], x['path'])
            for y in translation_config['project']['resources']:
                if resource_full_path == y['origin']:
                    uploadables.append({'resource_path': x['path'],
                        'translation_resource_name': y['name'],
                        'translation_resource_slug': y['slug'],
                        'resource_fetched': False,
                        'resource_uploaded': False})
            else:
                with TpaLogger(**kafka) as o:
                    o.warn("Resource files not found in translation config. '{}'".format(x['path']))

        with TpaLogger(**kafka) as o:
            o.info("Uploadables ({}): {}".format(len(uploadables), uploadables))
    except KeyError as e:
        msg = "Failed to access key in resource/translation config file. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    # Upload resource file one by one in uploadable list. Try uploading all of files.
    for i in range(0, len(uploadables)):
        try:
            r = get_context_from_resource_platform(request_id, resource_platform, resource_repository_name, uploadables[i]['resource_path'])
            uploadables[i]['resource_fetched'] = True
        except FatalError as e:
            msg = "Failed to get resource context. Resource: '{}' {}".format(uploadables[i]['resource_path'], str(e))
            with TpaLogger(**kafka) as o:
                o.error(msg)
            continue
        with TpaLogger(**kafka) as o:
            o.info("{}".format(r))

        r = upload_context_to_translation_platform(request_id, translation_platform, translation_project_slug, uploadables[i]['translation_resource_slug'], r['context'])
        if r:
            uploadables[i]['resource_uploaded'] = True
        else: 
            uploadables[i]['resource_uploaded'] = False
            msg = "Failed to upload resource context. Resource: '{}' {}".format(uploadables[i]['resource_path'], str(e))
            with TpaLogger(**kafka) as o:
                o.error(msg)

    results = uploadables
    return response_OK(request_id, "Executed", results, kafka)

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

    
