import os, sys, codecs
import json
import logging

import settings
import core.transifex.transifex_api as transifex

logger = logging.getLogger(__name__)

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

def _setup_cache_dir():
    cache_dir = settings.CACHE_DIR
    if not os.path.isdir(cache_dir):
        if not _setup_dir(cache_dir):
            return False

    transifex_dir = os.path.join(cache_dir, 'transifex')
    if not os.path.isdir(transifex_dir):
        if not _setup_dir(transifex_dir):
            return False

    transifex_projects_dir = os.path.join(transifex_dir, 'projects')
    if not os.path.isdir(transifex_projects_dir):
        if not _setup_dir(transifex_projects_dir):
            return False

    # TODO - crowdin dirs

    return True

def initialize():
    logger.info("Initializing transifex cache...")
    return _setup_cache_dir()

def _get_project_dir(project_slug):
    return os.path.join(_get_projects_dir(), project_slug)

def _get_source_strings_cache_path(project_dir, resource_slug):
    return os.path.join(project_dir, resource_slug + '_source')

def _get_translation_strings_cache_path(project_dir, resource_slug, language_code):
    return os.path.join(project_dir, resource_slug + '_' + language_code)

def _get_resources_cache_path(project_dir):
    return os.path.join(project_dir, 'reosurces.cache')

def _get_project_cache_path(project_dir):
    return os.path.join(project_dir, 'project.cache')

def _get_projects_dir():
    return os.path.join(settings.CACHE_DIR, 'transifex', 'projects')

def _get_projects_cache_path():
    projects_dir = _get_projects_dir()
    return os.path.join(projects_dir, 'projects.cache')

def get_projects():
    """ Return cached Transifex projects data, or None if no such cached data.
    """
    path = _get_projects_cache_path()
    try:
        fi = open(path)
    except (OSError, IOError) as e:
        logger.error("Failed to open Transifex projects cache file. Reason: '{}'.".format(e))
        return None

    try:
        results = json.load(fi)
    except ValueError as e:
        logger.error("Failed to read Transifex projects cache. Reason: '{}'.".format(e))
        fi.close()
        return None
    else:
        logger.info("Read Transifex projects from cache.")
        fi.close()
        return results

def create_projects_cache():
    """ Return newly cached Transifex projects data, None if it fails to fetch the data.
    """
    response_text = transifex.get_projects()
    if not response_text:
        return None

    try:
        results = json.loads(response_text)
    except ValueError as e:
        logger.error("Failed to read response from Transifex as json. Reason: '{}'.".format(e))
        return None

    path = _get_projects_cache_path()
    if os.path.isfile(path):
        os.remove(path)

    try:
        with open(path, 'w') as fo:
            fo.write(response_text)
    except(IOError, OSError) as e:
        logger.error("Failed to create transifex projects cache. Reason: '{}'.".format(e)) 
    else:
        logger.info("Created transifex projects cache: {}".format(path))
        return results

def get_project_details(project_slug):
    """ Return cached Transifex project details data.
    """
    project_dir = _get_project_dir(project_slug)
    path = _get_project_cache_path(project_dir)
    try:
        fi = open(path)
    except (OSError, IOError) as e:
        logger.error("Failed to open Transifex project cache file. Reason: '{}'.".format(e))
        return None

    try:
        results = json.load(fi)
    except ValueError as e:
        logger.error("Failed to read Transifex project cache. Reason: '{}'.".format(e))
        fi.close()
        return None
    else:
        logger.info("Read Transifex project from cache.")
        fi.close()
        return results

def create_project_details_cache(project_slug):
    """ Return newly cached Transifex project details data, None if it fails to fetch the data.
    """
    response_text = transifex.get_project_details(project_slug)
    if not response_text:
        return None

    try:
        project = json.loads(response_text)
    except ValueError as e:
        logger.error("Failed read response result as json. Reason: '{}'.".format(e))
        return None 

    project_dir = _get_project_dir(project_slug)
    _setup_dir(project_dir)

    path = _get_project_cache_path(project_dir)
    if os.path.isfile(path):
        os.remove(path)

    try:
        with open(path, 'w') as fo:
            fo.write(response_text)
    except(IOError, OSError) as e:
        logger.error("Failed to create transifex project cache. Reason: '{}'.".format(e)) 
    else:
        logger.info("Created transifex project cache: {}".format(path))

    return project

def get_resources_details(project_slug):
    """ Return cached list of Transifex resource details data. None if no such cached data.
    """
    project_dir = _get_project_dir(project_slug)
    path = _get_resources_cache_path(project_dir)
    try:
        fi = open(path)
    except (OSError, IOError) as e:
        logger.error("Failed to open Transifex resources cache file. Reason: '{}'.".format(e))
        return None

    try:
        results = json.load(fi)
    except ValueError as e:
        logger.error("Failed to read Transifex resources cache. Reason: '{}'.".format(e))
        fi.close()
        return None
    else:
        logger.info("Read Transifex resources from cache.")
        fi.close()
        return results

def create_resources_details_cache(project_slug):
    """ Return newly cached list of Transifex resource detals data. None if it fails to fetch the data.
    """
    project = create_project_details_cache(project_slug)
    if not project:
        return None

    resources = []
    for r in project['resources']:
        response_text = transifex.get_resource_details(project['slug'], r['slug'])
        if response_text:
            try:
                resource = json.loads(response_text)
            except ValueError as e:
                logger.error("Failed read response result as json. Reason: '{}'.".format(e))
            else:
                resource['project_slug'] = project_slug
                resource['name'] = r['name']
                resources.append(resource)
        else:
            pass

    if not resources:
        return None

    project_dir = _get_project_dir(project_slug)
    path = _get_resources_cache_path(project_dir)
    if os.path.isfile(path):
        os.remove(path)

    try:
        fo = open(path, 'w')
    except(IOError, OSError) as e:
        logger.error("Failed to create transifex resources details cache. Reason: '{}'.".format(e)) 
    else:
        logger.info("Created transifex resources details cache: {}".format(path))

    try:
        json.dump(resources, fo)
    except ValueError as e:
        fo.close()
        logger.error("Failed dump json. Reason: '{}'.".format(e))
        return None

    fo.close()
    return resources

def get_translation_strings_details(project_slug, resource_slug, language_code):
    """ Return cached list of Transifex translation strings data. None if no such cached data.
    """
    project_dir = _get_project_dir(project_slug)
    path = _get_translation_strings_cache_path(project_dir, resource_slug, language_code)
    try:
        fi = open(path)
    except (OSError, IOError) as e:
        logger.error("Failed to open Transifex translation strings cache file. Reason: '{}'.".format(e))
        return None

    try:
        results = json.load(fi)
    except ValueError as e:
        logger.error("Failed to read Transifex translation strings cache. Reason: '{}'.".format(e))
        fi.close()
        return None
    else:
        logger.info("Read Transifex translation strings from cache.")
        fi.close()
        return results

def create_translation_strings_details_cache(project_slug, resource_slug, language_code):
    """ Return newly cached list of Transifex translation strings data. None if it fails to fetch the data.
    """
    response_text = transifex.get_translation_strings_details(project_slug, resource_slug, language_code)
    if not response_text:
        return None

    try:
        project = json.loads(response_text)
    except ValueError as e:
        logger.error("Failed read response result as json. Reason: '{}'.".format(e))
        return None 

    project_dir = _get_project_dir(project_slug)
    _setup_dir(project_dir)

    path = _get_translation_strings_cache_path(project_dir, resource_slug, language_code)
    if os.path.isfile(path):
        os.remove(path)

    try:
        if sys.version_info[0:1] == (2,):
            with codecs.open(path, 'w', encoding='utf-8') as fo:
                fo.write(response_text)
        else:
            with open(path, 'w') as fo:
                fo.write(response_text)
    except(IOError, OSError) as e:
        logger.error("Failed to create transifex translation strings cache. Reason: '{}'.".format(e)) 
    else:
        logger.info("Created transifex translation strings cache: {}".format(path))

    return project

def get_source_strings_details(project_slug, resource_slug):
    """ Return cached soruce strings details. None if there is no cached data.
    """
    project_dir = _get_project_dir(project_slug)
    path = _get_source_strings_cache_path(project_dir, resource_slug)
    try:
        fi = open(path)
    except (OSError, IOError) as e:
        logger.error("Failed to open Transifex source strings cache file. Reason: '{}'.".format(e))
        return None

    try:
        results = json.load(fi)
    except ValueError as e:
        logger.error("Failed to read Transifex source strings cache. Reason: '{}'.".format(e))
        fi.close()
        return None
    else:
        logger.info("Read Transifex source strings from cache.")
        fi.close()
        return results

def create_source_strings_details_cache(project_slug, resource_slug):
    """ Return newly created cache of source strings details. Return None if it fails to fetch data.
        
        Source string details is not just source string details. It is combination of en-US translation
        string details and source string details.
    """
    strings = create_translation_strings_details_cache(project_slug, resource_slug, 'en-US')
    if not strings:
        return None

    results = []
    for s in strings:
        response_text = transifex.get_source_string_details(project_slug, resource_slug, s['key'])
        if response_text:
            try:
                d = json.loads(response_text)
            except ValueError as e:
                logger.error("Failed read response result as json. Reason: '{}'.".format(e))
            else:
                temp = s.copy()
                temp.update(d)
                results.append(temp)

    if not results:
        return None

    project_dir = _get_project_dir(project_slug)
    path = _get_source_strings_cache_path(project_dir, resource_slug)
    if os.path.isfile(path):
        os.remove(path)

    try:
        fo = open(path, 'w')
    except(IOError, OSError) as e:
        logger.error("Failed to create transifex sources details cache. Reason: '{}'.".format(e)) 
    else:
        logger.info("Created transifex sources details cache: {}".format(path))

    try:
        json.dump(results, fo)
    except ValueError as e:
        fo.close()
        logger.error("Failed dump json. Reason: '{}'.".format(e))
        return None

    fo.close()
    return results

