"""
Helper functions used by executors.


"""
import os
import json
import hashlib
import difflib
from tempfile import mkdtemp
from shutil import rmtree
from urllib.parse import quote

from ...common.common import FatalError
from ...common.common import TpaLogger
from ...common.common import GET, PUT
from ...common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR
#from ...common.common import gen_sha1_from_strings
from ...common.common import save_text, gen_sha1_from_file_context

providers = {
    'configurator': {
        'api': 'http://localhost:65000/api/v0'
        },
    'repository_carrier': {
        'api': 'http://localhost:64700/api/v0'
        }
    }


#
# TODO --- remove request_id arg (since helpers will not log anything and the caller should know the request id and log with it.
#
#


def repository_file_exists(request_id, platform_name, repo_name, file_path):
    try:
        url = "{}/repository/platform/{}/repo/{}/file/path={}/exists".format(providers['repository_carrier']['api'],
                                                                                platform_name,
                                                                                repo_name,
                                                                                quote(file_path, safe=''))
        r = GET(url, request_id)
        if r['status_code'] == 200:
            return True 
        else:
            return False 
    except KeyError as e:
        msg = "Failed to access key in response for file existence. {}".format(str(e))
        raise FatalError(msg)


def get_config_context(request_id, configurator_id, config_path, expected_file_category):
    try:
        url = "{}/configuration/{}/path={}".format(providers['configurator']['api'], configurator_id, quote(config_path, safe=''))
        r = GET(url, request_id)
        config = r['results']
        if not config['meta']['category'] == expected_file_category:
            msg = "Unexpected config file category. '{}' Expected: '{}', Actual: '{}'".format(config_path, expected_file_category, config['meta']['category'])
            raise FatalError(msg)
        return config
    except KeyError as e:
        msg = "Failed to access key in response for uploader config. {}".format(str(e))
        raise FatalError(msg)
    except ValueError as e:
        msg = "Failed to load response as JSON for uploader config. {}".format(str(e))
        raise FatalError(msg)

def get_context_from_resource_repository(request_id, resource_platform_name, repo_name, resource_file_path):
    try:
        url = "{}/repository/platform/{}/repo/{}/file/path={}".format(providers['repository_carrier']['api'],
                                                                                resource_platform_name,
                                                                                repo_name,
                                                                                quote(resource_file_path, safe=''))
        r = GET(url, request_id)
        if r['status_code'] == 200:
            # FIXME --- generating sha1 directly from string does not match
            #           the one created by resource carier.
            #sha1 =  gen_sha1_from_strings(r['results']['context'])
            tempdir = mkdtemp()
            tempfile_path= os.path.join(tempdir, 'temp.file')
            save_text(tempfile_path, r['results']['context'])
            sha1 = gen_sha1_from_file_context(tempfile_path)
            rmtree(tempdir)
            if sha1 == r['results']['sha1']:
                return r['results']
            else:
                msg = "sha1 not match for file context from translation platform. Expected: '{}', Actual: '{}'".format(r['results']['sha1'], sha1)
                raise FatalError(msg)
        else:
            msg = "Unexpected status code '{}' for resource file context. {}, {}, {}".format(r['status_code'], resource_platform_name, repo_name, resource_file_path)
            raise FatalError(msg)
    except KeyError as e:
        msg = "Failed to access key in response for resource file context. {}".format(str(e))
        raise FatalError(msg)

def download_file_from_resource_repository(request_id, resource_platform_name, repo_name, resource_file_path, destpath):
    """ Download specified file from repository carrier and save it to 'destpath'.
    """
    url = "{}/repository/platform/{}/repo/{}/file/path={}".format(providers['repository_carrier']['api'],
                                                                                resource_platform_name,
                                                                                repo_name,
                                                                                quote(resource_file_path, safe=''))
    r = GET(url, request_id)
    try:
        with open(destpath, 'w') as fo:
            fo.write(r['results']['context'])
    except (IOError, OSError) as e:
        msg = "Failed to save donwloaded file. {}".format(str(e))
        raise FatalError(msg)
    except KeyError as e:
        msg = "Failed to access key in response for downloaded file context. {}".format(str(e))
        raise FatalError(msg)

    sha1 = gen_sha1_from_file_context(destpath)
    if sha1 == r['results']['sha1']:
        return
    else:
        msg = "Unexpected sha1 of downloaded file from resource platform. Expected: '{}', Actual: '{}'".format(r['results']['sha1'], sha1)
        raise FatalError(msg)

def upload_context_to_resource_repository(request_id, resource_platform, repository_name, file_path, context):
    creds = None        # creds will be set by repository carrier.
    url = "{}/repository/platform/{}/repo/{}/file/path={}".format(providers['repository_carrier']['api'], resource_platform, repository_name, quote(file_path, safe=''))
    r = PUT(url, request_id, creds, context)
    if r['status_code'] == 200:
        return
    else:
        msg = "Failed to upload context to resource repository. Platform: '{}', Repository: '{}', File: '{}', Context: '{}' {}".format(resource_platform, repository_name, file_path, context, r['message'])
        raise FatalError(msg)

def get_context_from_translation_platform(request_id, resource_file_path, translation_config):
    """ TODO --- this can be replaced with get_context_from_translation_platform_by_id()
    """
    try:
        for x in translation_config['project']['resources']:
            if x['origin'] == resource_file_path:
                url = "{}/repository/platform/{}/project/{}/resource/{}/lang/{}".format(providers['repository_carrier']['api'],
                                                                                    translation_config['platform'],
                                                                                    translation_config['project']['slug'],
                                                                                    x['slug'],
                                                                                    translation_config['project']['source_language'])
                r = GET(url, request_id)
                if r['status_code'] == 200:
                    # FIXME --- generating sha1 directly from string does not match
                    #           the one created by resource carier.
                    #sha1 = gen_sha1_from_strings(r['results']['context'])
                    tempdir = mkdtemp()
                    tempfile_path= os.path.join(tempdir, 'temp.file')
                    save_text(tempfile_path, r['results']['context'])
                    sha1 = gen_sha1_from_file_context(tempfile_path)
                    rmtree(tempdir)
                    if sha1 == r['results']['sha1']:
                        return r['results'] 
                    else:
                        msg = "sha1 not match for file context from translation platform. Expected: '{}', Actual: '{}'".format(r['results']['sha1'], sha1)
                        raise FatalError(msg)
                else:
                    msg = "Unexpected status code '{}' while obtaining file context form translation platform. {}, {}, {}".format(r['status_code'], resource_platform_name, repo_name, resource_file_path)
                    raise FatalError(msg)
        else:
            msg = "Resource '{}' not found in translation config. '{}'".format(resource_file_path, translation_config['meta']['desc'])
            raise FatalError(msg)
    except KeyError as e:
        msg = "Failed to access key while processing translation file context. {}".format(str(e))
        raise FatalError(msg)

def get_context_from_translation_platform_by_id(request_id, translation_platform, project_slug, resource_slug, language_id):
    """ Return file context, which is obtained from translation platform by specifying project id/slug, resource id/slug and language id.
        Caller is responsible to handle FailtalError.
    """
    try:
        url = "{}/repository/platform/{}/project/{}/resource/{}/lang/{}".format(providers['repository_carrier']['api'], translation_platform, project_slug, resource_slug, language_id)
        r = GET(url, request_id)
        if r['status_code'] == 200:
            # FIXME --- generating sha1 directly from string does not match
            #           the one created by resource carier.
            #sha1 = gen_sha1_from_strings(r['results']['context'])
            tempdir = mkdtemp()
            tempfile_path= os.path.join(tempdir, 'temp.file')
            save_text(tempfile_path, r['results']['context'])
            sha1 = gen_sha1_from_file_context(tempfile_path)
            rmtree(tempdir)
            if sha1 == r['results']['sha1']:
                return r['results'] 
            else:
                msg = "sha1 not match for file context from translation platform. Expected: '{}', Actual: '{}'".format(r['results']['sha1'], sha1)
                raise FatalError(msg)
        else:
            msg = "Unexpected status code '{}' while obtaining file context from translation platform. Platform: '{}', Project: '{}', Resource: '{}', Language: '{}'".format(r['status_code'], translation_platform, project_slug, resource_slug, language_id)
            raise FatalError(msg)
    except FatalError as e:
        msg = "Error while obtaining file context from translation platform. Platform: '{}', Project: '{}', Resource: '{}', Language: '{}', {}".format(translation_platform, project_slug, resource_slug, language_id, str(e))
        raise FatalError(msg)

def download_file_from_translation_platform_by_id(request_id, translation_platform, project_slug, resource_slug, language_id, destpath):
    """ Download a file, which is specified by project id/slug, resource id/slug and language id, from translation platform.
    """
    url = "{}/repository/platform/{}/project/{}/resource/{}/lang/{}".format(providers['repository_carrier']['api'], translation_platform, project_slug, resource_slug, language_id)
    r = GET(url, request_id)
    try:
        with open(destpath, 'w') as fo:
            fo.write(r['results']['context'])
    except (IOError, OSError) as e:
        msg = "Failed to save donwloaded file. {}".format(str(e))
        raise FatalError(msg)
    except KeyError as e:
        msg = "Failed to access key in response for downloaded file context. {}".format(str(e))
        raise FatalError(msg)

    sha1 = gen_sha1_from_file_context(destpath)
    if sha1 == r['results']['sha1']:
        return
    else:
        msg = "Unexpected sha1 of downloaded file from translation platform. Expected: '{}', Actual: '{}'".format(r['results']['sha1'], sha1)
        raise FatalError(msg)

def upload_context_to_translation_platform(request_id, translation_platform, project_slug, resource_slug, context):
    try:
        creds = None        # creds will be set by repository carrier.
        url = "{}/repository/platform/{}/project/{}/resource/{}".format(providers['repository_carrier']['api'], translation_platform, project_slug, resource_slug)
        r = PUT(url, request_id, creds, context)
        return r.status_code == 200
    except FatalError as e:
        return False

def get_translation_status(request_id, translation_platform, project_slug, resource_slug, lang, kafka):
    creds = None        # creds will be set by repository carrier.
    url = "{}/repository/platform/{}/project/{}/resource/{}/lang/{}/status".format(providers['repository_carrier']['api'], translation_platform, project_slug, resource_slug, lang)
    r = GET(url, request_id, creds)
    return r['results']

def ORIGget_translation_file_candidates(resource_config, translation_config, kafka):
    # Create list of uploadable translation files for all resource files.
    try:
        d = {'resource_platform': resource_config['repository']['platform'],
            'resource_repository_name': resource_config['repository']['name'],
            'resource_branch': resource_config['repository']['branch'],
            'translation_platform': translation_config['platform'],
            'translation_project_name': translation_config['project']['name'],
            'translation_project_slug': translation_config['project']['slug']}
        lst = []

        for x in resource_config['repository']['resources']:
            resource_full_path = os.path.join(resource_config['repository']['owner'], resource_config['repository']['name'], x['path'])
            for y in translation_config['project']['resources']:
                if resource_full_path == y['origin']:
                    translations = []
                    # Language should be listed in both resource configuration and translation configuration.
                    # Otherwise, ignore the language.
                    for z in x['translations']:
                        if z['lang'] in translation_config['project']['languages']:
                            translations.append({
                                'lang': z['lang'],
                                'path': z['path'],
                                'in_open_pullrequest': True,
                                'status': 'NOP',
                                'results': 'NOP'})
                        else:
                            with TpaLogger(**kafka) as o:
                                o.warn("Language not found in translation config. '{}'".format(z['lang']))
                    lst.append({
                        'resource_path': x['path'],
                        'translation_resource_name': y['name'],
                        'translation_resource_slug': y['slug'],
                        'translations': translations})
            else:
                with TpaLogger(**kafka) as o:
                    o.warn("Resource files not found in translation config. '{}'".format(x['path']))

        with TpaLogger(**kafka) as o:
            o.info("Uploadables ({}): {}".format(len(lst), lst))
        d['files'] = lst
        return d
    except KeyError as e:
        with TpaLogger(**kafka) as o:
            o.error("Failed to access key in resource/translation config file. {}".format(str(e)))
        return None 

def list_files(request_id, uploader_config_path, kafka):
    """ Create list of resource and translation files, which are listed in both resource configuration and
        translation configuration files.
    """
    try:
        configurator_id = 'tpa'
        uploader_config = get_config_context(request_id, configurator_id, uploader_config_path, 'uploader_configuration')
        resource_config = get_config_context(request_id, configurator_id, uploader_config['resource_config_path'], 'resource_configuration')
        translation_config = get_config_context(request_id, configurator_id, uploader_config['translation_config_path'], 'translation_configuration')
    except KeyError as e:
        msg = "Failed to access key in uploader config file. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except FatalError as e:
        msg = "Failed to get config context. {}".format(str(e))
        return response_BAD_REQUEST(request_id, msg, kafka)

    try:
        d = {'resource_platform': resource_config['repository']['platform'],
            'resource_repository_name': resource_config['repository']['name'],
            'resource_branch': resource_config['repository']['branch'],
            'translation_platform': translation_config['platform'],
            'translation_project_name': translation_config['project']['name'],
            'translation_project_slug': translation_config['project']['slug']}
        lst = []

        for x in resource_config['repository']['resources']:
            resource_full_path = os.path.join(resource_config['repository']['owner'], resource_config['repository']['name'], x['path'])
            for y in translation_config['project']['resources']:
                if resource_full_path == y['origin']:
                    translations = []
                    # Language should be listed in both resource configuration and translation configuration.
                    # Otherwise, ignore the language.
                    for z in x['translations']:
                        if z['lang'] in translation_config['project']['languages']:
                            translations.append({
                                'lang': z['lang'],
                                'path': z['path']})
                        else:
                            with TpaLogger(**kafka) as o:
                                o.warn("Language not found in translation config. '{}'".format(z['lang']))
                    lst.append({
                        'resource_path': x['path'],
                        'translation_resource_name': y['name'],
                        'translation_resource_slug': y['slug'],
                        'translations': translations})
            else:
                with TpaLogger(**kafka) as o:
                    o.warn("Resource files not found in translation config. '{}'".format(x['path']))

        with TpaLogger(**kafka) as o:
            o.info("Translation files ({}): {}".format(len(lst), lst))
        d['files'] = lst
        return d
    except KeyError as e:
        with TpaLogger(**kafka) as o:
            o.error("Failed to access key in resource/translation config file. {}".format(str(e)))
        return None 

def list_files_in_open_pullrequest(request_id, uploader_config_path, kafka):
    # Returns list of pull request description text, which currently contains list of files.
    try:
        configurator_id = 'tpa'
        uploader_config = get_config_context(request_id, configurator_id, uploader_config_path, 'uploader_configuration')
    except KeyError as e:
        msg = "Failed to access key in uploader config file. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except FatalError as e:
        msg = "Failed to get config context. {}".format(str(e))
        return response_BAD_REQUEST(request_id, msg, kafka)

    lst = []
    try:
        creds = None        # creds will be set by repository carrier.
        url = "{}/repository/pullrequest/state=open".format(providers['repository_carrier']['api'])
        data = json.dumps({'request_id': request_id, 'config_path': uploader_config['resource_config_path']})
        r = GET(url, request_id, creds, data)
        if r['status_code'] == 200:
            for x in r['results']:
                lst.append(x['description'])
        return lst 
    except FatalError as e:
        with TpaLogger(**kafka) as o:
            o.error("Failed to get files in open pulll request. {}".format(str(e)))
        return None

