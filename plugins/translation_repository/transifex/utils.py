import os
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

from core.common.results import succeeded_util_call_results, failed_util_call_results
import api as transifex

import settings # temp for CACHE_DIR
PROJECT_BASE_DIR =  os.path.join(settings.CACHE_DIR, 'transifex', 'projects')
PROJECTS_CACHE_FILE_PATH = os.path.join(PROJECT_BASE_DIR, 'projects.cache')

# For Transifex project (summary).
#
# keys                  values
# -------------------------------------------
# slug                  project slug
# name                  project name
# description           project description
TransifexProject = namedtuple('TransifexProject', 'slug, name, description')

# For Transifex project details. 
#
# keys                  values
# -------------------------------------------
# slug                  project slug
# name                  project name
# description           project description
# resources             list of TransifexResource
TransifexProjectDetails = namedtuple('TransifexProject', 'slug, name, description, resources')

# For Transifex resource (summary).
#
# slug                  resource slug
# name                  resource name
TransifexResource = namedtuple('TransifexResource', 'slug, name')

# For Transifex resource details.
#
# slug                  resource slug
# name                  resource name
# last_updated          last updated date for the resource
# num_strings           number of strings in the resource
# num_words             number of words in the source
TransifexResourceDetails = namedtuple('TransifexResource', 'slug, name, last_updated, num_strings, num_words')

# For Transiefx source string details.
#
# comment               instructions attached to the source string
# tags                  list of tags attached to the source string
TransifexSourceStringDetails = namedtuple('TransifexSourceStringDetails', 'comment, tags')

# For Transifex translation strings details.
#
# 
#
# key                   key for the string.
# source_string         source string.
# translation           translation for the string.
# reviewed              true when reviewed, false otherwise.               
# last_update           last updated date.
TransifexTranslationStringDetails = namedtuple('TransifexTranslationStringDetails', 'key, source, translation, reviewed, last_updated')

def translation_review_completed(language_stats_response_text):
    try:
        d = json.loads(language_stats_response_text)
    except ValueError as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(d['reviewed_percentage'] == '100%')

def get_translation_content(get_translation_response_text):
    try:
        d = json.loads(get_translation_response_text)
    except ValueError as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(d['content'])

def _create_response_text_file(response, path):
    if os.path.isfile(path):
        os.remove(path)
        
    try:
        with open(path, 'w') as fo:
            fo.write(response.text)
    except(IOError, OSError) as e:
        return failed_util_call_results("Failed to write response text '{}' as file '{}'. Reason: '{}'.".format(response.text, path, e)) 
    else:
        return succeeded_util_call_results(None)

def _response_file_to_json(path):
    try:
        fi = open(path)
    except (OSError, IOError) as e:
        return failed_util_call_results("Failed to open response file '{}'. Reason: '{}'.".format(path, e))

    try:
        data = json.load(fi)
    except ValueError as e:
        fi.close()
        return failed_util_call_results("Failed to load response file '{}' as json. Reason: '{}'.".format(path, e))
    else:
        return succeeded_util_call_results(data)

def _response_text_to_json(response_text):
    try:
        data = json.loads(response_text)
    except ValueError as e:
        return failed_util_call_results("Failed to load response text '{}' as json. Reason: '{}'.".format(response_text, e))
    else:
        return succeeded_util_call_results(data)

def _to_list_projects(json_data):
    results = []
    try:
        for project in json_data:
            results.append(
                TransifexProject(
                    project['slug'],
                    project['name'],
                    project['description']
                ))
    except KeyError as e:
        return failed_util_call_results("Failed to read Transifex projects json '{}'. Reason: '{}'.".format(json_data, e))
    else: 
        return succeeded_util_call_results(results)

def _to_project_details(json_data):
    resources = []
    try:
        for resource in json_data['resources']:
            resources.append(TransifexResource(resource['slug'], resource['name']))
    except KeyError as e:
        return failed_util_call_results("Failed to read Transifex resource in project details json '{}'. Reason: '{}'.".format(json_data, e))

    try:
        results = TransifexProjectDetails(
                    json_data['slug'],
                    json_data['name'],
                    json_data['description'],
                    resources
                )
    except KeyError as e:
        return failed_util_call_results("Failed to read Transifex project details json '{}'. Reason: '{}'.".format(json_data, e))
    else: 
        return succeeded_util_call_results(results)

def _to_resource_details(json_data):
    try:
        results = TransifexResourceDetails(
                    json_data['slug'],
                    json_data['name'],
                    json_data['last_update'],
                    json_data['total_entities'],
                    json_data['wordcount']
        )
    except KeyError as e:
        return failed_util_call_results("Failed to read Transifex resources json '{}'. Reason: '{}'.".format(json_data, e))
    
    return succeeded_util_call_results(results)

def _to_translation_string_details(json_data):
    try:
        results = TransifexTranslationStringDetails(
                    json_data['key'],
                    json_data['source_string'],
                    json_data['translation'],
                    json_data['reviewed'],
                    json_data['last_update']
        )
    except KeyError as e:
        return failed_util_call_results("Failed to read Transifex translation string details json '{}'. Reason: '{}'.".format(json_data, e))
    
    return succeeded_util_call_results(results)

def _to_source_string_details(json_data):
    try:
        results = TransifexSourceStringDetails(
                    json_data['comment'],
                    json_data['tags']
        )
    except KeyError as e:
        return failed_util_call_results("Failed to read Transifex source string details json '{}'. Reason: '{}'.".format(json_data, e))
    
    return succeeded_util_call_results(results)

def _setup_dir(path):
    if os.path.isdir(path):
        return True
    else:
        try:
            os.makedirs(path)
        except OSError as e:
            logger.error("Failed to create directory: '{}'. Reason: {}".format(path, e))
            return False
        else:
            if os.path.isdir(path):
                return True
            else:
                logger.error("Created directory does not exist: '{}'.".format(path))
                return False

def _get_source_string_details_path(project_slug, resource_slug, key):
    return os.path.join(_get_source_dir(project_slug, resource_slug), key + '.cache')

def _get_source_dir(project_slug, resource_slug):
    global PROJECT_BASE_DIR
    return os.path.join(PROJECT_BASE_DIR, project_slug, resource_slug + '_source')

def _get_translation_strings_details_cache_path(project_slug, resource_slug, language_code):
    return os.path.join(_get_project_dir(project_slug), resource_slug + '.strings.cache.' + language_code)

def _get_resource_cache_path(project_slug, resource_slug):
    return os.path.join(_get_project_dir(project_slug), resource_slug + '.resource.cache')

def _get_project_cache_path(project_slug):
    return os.path.join(_get_project_dir(project_slug), 'project.cache')

def _get_project_dir(project_slug):
    global PROJECT_BASE_DIR
    return os.path.join(PROJECT_BASE_DIR, project_slug)

def _query_projects(creds, output_path=None):
    ret = transifex.get_projects(creds)
    if not ret.succeeded:
        return failed_util_call_results(ret.message)

    ret2 = _response_text_to_json(ret.response.text)
    if not ret2.succeeded:
        return failed_util_call_results(ret2.message)

    if output_path:
        ret3 = _create_response_text_file(ret.response, output_path)
        if not ret3.succeeded:
            return failed_util_call_results(ret3.message)

    ret3 = _to_list_projects(ret2.output)
    if ret3.succeeded:
        return succeeded_util_call_results(ret3.output)
    else:
        return failed_util_call_results(ret3.message)

def _ensure_transifex_cache_directory():
    _setup_dir(os.path.join(settings.CACHE_DIR, 'transifex'))
    _setup_dir(os.path.join(settings.CACHE_DIR, 'transifex', 'projects'))

def query_projects(creds):
    """ Return list of project information (list of TransifexProject tuples).

        This is to get all projects (slugs and names) by quering Transifex
        with specified creds.

        NOTE:
        A projects cache file is created each time this is called (but this
        function never read the file because accessible projects are based
        on creds).
    """

    # FIXME
    # Directory like cache/transifex/projects should be created somewhere
    # before any util function is called.
    # Since this is the very first function to be called to list
    # Transifex contents, create director in here, just for the time being...
    _ensure_transifex_cache_directory()

    global PROJECTS_CACHE_FILE_PATH
    ret = _query_projects(creds, PROJECTS_CACHE_FILE_PATH)
    if ret.succeeded:
        return succeeded_util_call_results(ret.output)
    else:
        return failed_util_call_results("Failed to get projects. Reason: '{}'.".format(ret.message))

def _read_project_details_response_file(path):
    if not os.path.isfile(path):
        return failed_util_call_results("Transifex project details response file not found: '{}'.".format(path))

    ret = _response_file_to_json(path)
    if not ret.succeeded:
        return failed_util_call_results(ret.message)

    ret2 = _to_project_details(ret.output)
    if ret2.succeeded:
        return succeeded_util_call_results(ret2.output)
    else:
        return failed_util_call_results(ret2.message)

def _get_project_details(creds, project_slug):
    path = _get_project_cache_path(project_slug)
    if not os.path.isfile(path):
        ret = transifex.get_project_details(project_slug, creds)
        if not ret.succeeded:
            return failed_util_call_results("Failed to query project details from Transifex. Reason: '{}'.".format(ret.message))

        project_dir = _get_project_dir(project_slug)
        if not os.path.isdir(project_dir):
            try:
                os.makedirs(project_dir)
            except OSError as e:
                return failed_util_call_results("Failed to create project dir. Reason: '{}'.".format(e))

        ret2 = _create_response_text_file(ret.response, path)
        if not ret2.succeeded:
            return failed_util_call_results("Failed to create project details cache file. Reason: '{}'.".format(ret2.message))

    ret3 = _read_project_details_response_file(path)
    if not ret3.succeeded:
        return failed_util_call_results("Failed to read project details cache file. Reason: '{}'.".format(ret3.message))

    return ret3

def query_project(creds, project_slug):
    """ Return project information (TransifexProjectDetails tuple) and
        list of resouce information (TransifexResource tuples).

        This is to get details information of a specific project.

        NOTE:
        A project details cache file is created if it does not exist.
        If it does, project details information is read from the cache file.
    """
    ret = _get_project_details(creds, project_slug)
    if not ret.succeeded:
        return failed_util_call_results("Failed to query project details. Reason: '{}'.".format(ret.message))

    return ret

def _read_resource_details_response_file(path):
    if not os.path.isfile(path):
        return failed_util_call_results("Transifex resource details response file not found: '{}'.".format(path))

    ret = _response_file_to_json(path)
    if not ret.succeeded:
        return failed_util_call_results(ret.message)

    ret2 = _to_resource_details(ret.output)
    if ret2.succeeded:
        return succeeded_util_call_results(ret2.output)
    else:
        return failed_util_call_results(ret2.message)

def _get_resource(creds, project_slug, resource_slug):
    path = _get_resource_cache_path(project_slug, resource_slug)
    if not os.path.isfile(path):
        ret = transifex.get_resource_details(project_slug, resource_slug, creds)
        if not ret.succeeded:
            return failed_util_call_results("Failed to query resource details from Transifex. Reason: '{}'.".format(ret.message))

        ret2 = _create_response_text_file(ret.response, path)
        if not ret2.succeeded:
            return failed_util_call_results("Failed to create resource details cache file. Reason: '{}'.".format(ret2.message))

    ret3 = _read_resource_details_response_file(path)
    if not ret3.succeeded:
        return failed_util_call_results("Failed to read resource details cache file. Reason: '{}'.".format(ret3.message))

    return ret3

def query_resource(creds, project_slug, resource_slug):
    """ Return resouce information (TransifexResourceDetails tuple).

        This is to get details information of a specific resource.

        NOTE:
        A resource details cache file is created if it does not exist.
        If it does, resource details information is read from the cache file.
    """
    ret = _get_resource(creds, project_slug, resource_slug)
    if not ret.succeeded:
        return failed_util_call_results("Failed to query resorce details. Reason: '{}'.".format(ret.message))

    return ret

def _read_translation_strings_details_response_file(path):
    if not os.path.isfile(path):
        return failed_util_call_results("Transifex translation strings details response file not found: '{}'.".format(path))

    ret = _response_file_to_json(path)
    if not ret.succeeded:
        return failed_util_call_results(ret.message)

    results = []
    for entry in ret.output:
        ret2 = _to_translation_string_details(entry)
        if ret2.succeeded:
            results.append(ret2.output)
        else:
            return failed_util_call_results("Failed to read translation string detail json. Reason: '{}'".format(ret2.message))

    return succeeded_util_call_results(results)

def _get_translation_strings_details(creds, project_slug, resource_slug, language_code):
    path = _get_translation_strings_details_cache_path(project_slug, resource_slug, language_code)
    if not os.path.isfile(path):
        ret = transifex.get_translation_strings_details(project_slug, resource_slug, language_code, creds)
        if not ret.succeeded:
            return failed_util_call_results("Failed to query translation string details from Transifex. Reason: '{}'.".format(ret.message))

        ret2 = _create_response_text_file(ret.response, path)
        if not ret2.succeeded:
            return failed_util_call_results("Failed to create translation strings details cache file. Reason: '{}'.".format(ret2.message))

    ret3 = _read_translation_strings_details_response_file(path)
    if not ret3.succeeded:
        return failed_util_call_results("Failed to read translation strings details cache file. Reason: '{}'.".format(ret3.message))

    return ret3

def _read_source_string_details_response_file(path):
    if not os.path.isfile(path):
        return failed_util_call_results("Transifex source string details response file not found: '{}'.".format(path))

    ret = _response_file_to_json(path)
    if not ret.succeeded:
        return failed_util_call_results(ret.message)

    ret2 = _to_source_string_details(ret.output)
    if ret2.succeeded:
        return succeeded_util_call_results(ret2.output)
    else:
        return failed_util_call_results("Failed to read source string detail json. Reason: '{}'".format(ret2.message))

def _get_source_string_details(creds, project_slug, resource_slug, string_details):
    path = _get_source_string_details_path(project_slug, resource_slug, string_details.key)
    if not os.path.isfile(path):
        ret = transifex.get_source_string_details(project_slug, resource_slug, string_details.key, creds)
        if not ret.succeeded:
            return failed_util_call_results("Failed to query source string details for key: '{}'. Reason: '{}'.".format(string_details.key, ret.message))

        # ensure soruce directory exists.
        if not os.path.isdir(_get_source_dir(project_slug, resource_slug)):
            _setup_dir(_get_source_dir(project_slug, resource_slug))

        ret2 = _create_response_text_file(ret.response, path)
        if not ret2.succeeded:
            return failed_util_call_results("Failed to create source string details cache file. Reason: '{}'.".format(ret2.message))

    ret3 = _read_source_string_details_response_file(path)
    if not ret3.succeeded:
        return failed_util_call_results("Failed to read source string details cache file. Reason: '{}'.".format(ret3.message))

    return ret3

def query_source_strings_details(creds, project_slug, resource_slug):
    """ Return list of source string information of a specific resource.
        A source string information consists of following two tuples.
            {
                source: TransifexSoruceStringDetails,
                translation: TransifexTranslationStringDetails
            }

        For this case, 'translation' is translation string details for en-US. 

        NOTE:
        A translation strings details cache file is created as result of this query, if previously
        cached file does not exist.
        
        Source string dtails cahce file(s) is created as a result of this query, if previousely
        cached file(s) does not exist.
    """
    ret = _get_translation_strings_details(creds, project_slug, resource_slug, 'en-US')
    if not ret.succeeded:
        return failed_util_call_results("Failed to get translation strings details cache file. Reason: '{}'.".format(ret.message))

    results = []
    for translation_string in ret.output:
        ret2 = _get_source_string_details(creds, project_slug, resource_slug, translation_string)
        if ret2.succeeded:
            results.append({'source': ret2.output, 'translation': translation_string})
        else:
            # return as much as possible, instead of making it error. 
            results.append({'source': None, 'translation': translation_string})

    return succeeded_util_call_results(results)

