"""
Helper functions used by executors.


"""
import os
import json
import hashlib
import difflib
from tempfile import mkdtemp
from shutil import rmtree
try:
    from urllib import quote
except ImportError:
    from urllib.parse import quote

from common.common import FatalError
from common.common import GET
from common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR
#from common.common import gen_sha1_from_strings
from common.common import save_text, gen_sha1_from_file_context

providers = {
    'configurator': {
        'api': 'http://localhost:65000/api/v0'
        },
    'repository_carrier': {
        'api': 'http://localhost:64700/api/v0'
        }
    }

# TODO --- remove request_id arg (since helpers will not log anything and the caller should know the request id and log with it.
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

def get_context_from_resource_platform(request_id, resource_platform_name, repo_name, resource_file_path):
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

def get_context_from_translation_platform(request_id, resource_file_path, translation_config):
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
                    msg = "Unexpected status code '{}' for translation file context. {}, {}, {}".format(r['status_code'], resource_platform_name, repo_name, resource_file_path)
                    raise FatalError(msg)
        else:
            msg = "Resource '{}' not found in translation config. '{}'".format(resource_file_path, translation_config['meta']['desc'])
            raise FatalError(msg)
    except KeyError as e:
        msg = "Failed to access key while processing translation file context. {}".format(str(e))
        raise FatalError(msg)

