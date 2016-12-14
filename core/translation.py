import os
from collections import namedtuple
import json

import logging
logger = logging.getLogger(__name__)

import settings
import core.creds as creds
import core.plugins.transifex.utils as transifex_utils

def to_dict(o):
    if type(o) == TranslationDetails:
        return _TranslationDetails_to_dict(o)
    elif type(o) == LanguageStats:
        return _LanguageStats_to_dict(o)
    elif type(o) == TranslationConfiguration:
        return _TranslationConfiguration_to_dict(o)
    elif type(o) == TranslationPlatformProject:
        return _TranslationPlatformProject_to_dict(o)
    elif type(o) == TranslationPlatformProjectDetails:
        return _TranslationPlatformProjectDetails_to_dict(o)
    elif type(o) == TranslationPlatformProjectResourceDetails:
        return _TranslationPlatformProjectResourceDetails_to_dict(o)
    elif type(o) == TranslationPlatformTranslationStringDetails:
        return _TranslationPlatformTranslationStringDetails_to_dict(o)
    elif type(o) == TranslationPlatformSourceStringDetails:
        return _TranslationPlatformSourceStringDetails_to_dict(o)
    else:
        logger.error("Unknown type: '{}'.".format(type(o)))
        return {}




'''
    Translation Details 



'''

# Translated Resource Repository
#
# keys          values
# ----------------------------------------------------------------------
# Platform      Platform name of the resource repository.
# owner         Owner of the resource repository.
# name          Name of the resource repository.
TranslatedResourceRepository = namedtuple('TranslatedResourceRepository', 'platform, owner, name')

def _TranslatedResourceRepository_to_dict(o):
    return {'platform': o.platform, 'owner': o.owner, 'name': o.name}

# Translation Reposiory Details.
#
# keys              values
# ----------------------------------------------------------------------
# platform                          Translation repository platform name (e.g. transifex).
# project_name                      Translation project name.
# project_languages                 List of language code the project is translated into.
# translated_resource_repositories  List of translated resource repository (TranslatedResourceRepository tuple).
TranslationDetails = namedtuple('TranslationDetails', 'platform, project_name, project_languages, translated_resource_repositories') 

def _TranslationDetails_to_dict(o):
    repositories = []
    for r in o.resource_repositories:
        repositories.append(_ResourceRepository_to_dict(r))
    return {'platform': o.platform, 'project_name': o.project_name, 'project_languages': o.project_languages, 'translated_resource_repositories': repositories}

def get_details(config_filename):
    """
    Return Translation details, or None on any errors.
    """
    c = get_configuration(filename=os.path.join(settings.CONFIG_TRANSLATION_DIR, config_filename))
    if c:
        repositories = []
        for r in c.project_repositories:
            repositories.append(TranslatedResourceRepository(r.platform, r.owner, r.name))
        return TranslationDetails(c.project_platform, c.project_name, c.project_language_codes, repositories)
    else:
        logger.error("Failed to get configuration for translation repository details. configuration file: '{}'.".format(config_filename))
        return None



'''
    Language Stats

    Stats of a translated resource for a langauge.
'''
# LanguageStats 
#
# key                           value
# -------------------------------------------------------
# language_code                 language code of this stats
# last_updated                  last updated date for the resource
# num_reviewed_strings          number of reviewed strings.
# percentage_reviewed_strings   percentage of reviewed strings. e.g. '80%'
# num_translated_strings        number of translated strings.
# num_untranslated_strings      number of untranslated strings.
# percentage_translated_strings percentage of translated strings. e.g. '80%'
# num_translated_words          number of translated words.
# num_untranslated_words        number of untranslated words.
LanguageStats = namedtuple('LanguageStats', 'language_code, last_updated, num_reviewed_strings, percentage_reviewed_strings, num_translated_strings, num_untranslated_strings, percentage_translated_strings, num_translated_words, num_untranslated_words')

def _LanguageStats_to_dict(o):
    return {
            'language_code': o.language_code,
            'last_updated': o.last_updated,
            'num_reviewed_strings': o.num_reviewed_strings,
            'percentage_reviewed_strings': o.percentage_reviewed_strings,
            'num_translated_strings': o.num_translated_strings,
            'num_untranslated_strings': o.num_untranslated_strings,
            'percentage_translated_strings': o.percentage_translated_strings,
            'num_translated_words': o.num_translated_words,
            'num_untranslated_words': o.num_untranslated_words
            }

def get_language_stats(translation_platform, translation_project_name, resource_repository_name, resource_path):
    """ Return language stats (LanguageStats tuple) for a specified resource of a langauge.
    """
    if translation_platform == 'transifex':
        c = creds.get(translation_platform)
        if not c:
            logger.error("Failed to get creds for platform: '{}'.\n".format(translation_platform))
            return None 

        project_slug = transifex_utils.generate_project_slug(c.project_slug_prefix, translation_project_name)
        resource_slug = transifex_utils.generate_resource_slug(c.resource_slug_prefix, [resource_repository_name, resource_path])
        d = transifex_utils.get_all_translation_stats(c, project_slug, resource_slug)
        if not d:
            return None 

        results = []
        # convert TransifeixTranslationStats to LanguageStats
        for stats in d:
            results.append(LanguageStats(
                                stats.language_code,
                                stats.last_updated,
                                stats.num_reviewed_strings,
                                stats.percentage_reviewed_strings,
                                stats.num_translated_strings,
                                stats.num_untranslated_strings,
                                stats.percentage_translated_strings,
                                stats.num_translated_words,
                                stats.num_untranslated_words))
        return results
    elif translation_platform == 'crowdin':
        logger.error("NIY: get_language_stats() for crowdin.")
        return None 
    else:
        logger.error("Unknown translation platform: '{}'.\n".format(translation_platform))
        return None 



'''
    Master Language Stats

    Stats of a resource file in master langauge.
    
'''
# Master Language Stats
#
# slug                  resource slug
# name                  resource name
# last_updated          last updated date for the resource
# num_strings           number of strings in the resource
# num_words             number of words in the source
# language_code         language_code of the source
MasterLanguageStats = namedtuple('MasterLanguageStats', 'slug, name, last_updated, num_strings, num_words, language_code')

def get_master_language_stats(**kwargs):
    """ 
    Return stats of a resource file (MasterLanguageStats tuple).

    Mandatory
    ---------
    platform                    Translation platform name.
    project_name                Translation project name.
    resource_repository_name    Resource repository name.
    resource_path               Path of a resouce in the resource repository to obtain stats.
    """
    if kwargs['platform'] == 'transifex':
        c = creds.get('transifex')
        if not c:
            logger.error("Failed to get creds for transifex.")
            return None 

        pslug = transifex_utils.generate_project_slug(c.project_slug_prefix, kwargs['project_name'])
        rslug = transifex_utils.generate_resource_slug(c.resource_slug_prefix, [kwargs['resource_repository_name'], kwargs['resource_path']])

        _setup_dir(os.path.join(settings.CACHE_DIR, kwargs['platform'], 'projects', pslug, rslug))
        out = os.path.join(settings.CACHE_DIR, kwargs['platform'], 'projects', pslug, rslug, 'resource.cache')

        d = transifex_utils.get_platform_project_resource_details(c, out, pslug, rslug)
        if d != None:
            # convert TransifeixMasterLanguageStats to MasterLanguageStats
            return MasterLanguageStats(d.slug, d.name, d.last_updated, d.num_strings, d.num_words, d.language_code)
        else:
            logger.error("Failed to get resource details for '{}/{}'.".format(kwargs['resource_repository_name'], kwargs['resource_path']))
            return None
    elif kwargs['platform'] == 'crowdin':
        logger.error("NIY: get_master_language_stats() for crowdin.")
        return None
    else:
        logger.error("Unknown translation platform: '{}'.\n".format(kwargs['platform']))
        return None 



'''
    Translation Configuration


'''

# Repository
#
# keys          values
# -----------------------------------
# platform      Platform of resource repository. e.g. bitbucket
# owner         Owner of the repository.
# name          Name of the repository. 
TranslationConfigurationRepository = namedtuple('TranslationConfigurationRepository', 'platform, owner, name')

# Represents a Translation Configuration file.
#
# keys                      values
# -----------------------------------
# filename                  Resource file name
# path                      Resource file path
# --- configuration file context ----
# project_name              Translation project name.
# project_platform          Translation project platform name (e.g. transifex).
# project_language_codes    List of language codes defined in the projects.
# project_repositories      List of repositories (Repository tuple) in the project.
# project_reviewers         List of reviewers (username) for the project.
TranslationConfiguration = namedtuple('TranslationConfiguration', 'filename, path,  project_name, project_platform, project_language_codes, project_repositories, project_reviewers')

def _TranslationConfiguration_to_dict(o):
    repositories = []
    for x in o.project_repositories:
        repositories.append({'platform': x.platform, 'owner': x.owner, 'name': x.name})
    return {
            'filename' : o.filename,
            'path': o.path,
            'project_name': o.project_name,
            'project_platform': o.project_platform,
            'project_language_codes': o.project_language_codes,
            'project_repositories': repositories,
            'project_reviewers': o.project_reviewers
            }

def get_configuration(**kwargs):
    """ 
    Return TranslationConfiguration for a translatin configuration file (w/ 'filename' option),
    or list of available TranslationConfiguration.

    OPTION:
        'filename': To specify a specific translation configuration filename.
    """

    if 'filename' in kwargs:
        return _read_configuration_file(os.path.join(settings.CONFIG_TRANSLATION_DIR, kwargs['filename']))
    else:
        results = []
        for filename in os.listdir(settings.CONFIG_RESOURCE_DIR):
            if not os.path.splitext(filename)[1] == '.json':
                continue
            results.append(_read_configuration_file(os.path.join(settings.CONFIG_TRANSLATION_DIR, filename)))
        return results

def _read_repositories(o):
    results = []
    for x in o:
        results.append(TranslationConfigurationRepository(x['repository']['platform'], x['repository']['owner'], x['repository']['name']))
    return results

def _read_reviewers(o):
    results = []
    for x in o:
        results.append(x)
    return results

def _read_configuration_file(file_path):
    with open(file_path) as fi:
        try:
            j = json.load(fi)
        except ValueError as e:
            logger.error("Failed to load json. File: '{}', Reason: '{}'.".format(file_path, e))
            return None
        else:
            try: # catch all exceptions here, including one raised in subsquent functions.
                platform = j['project']['platform']
                name = j['project']['name']
                languages = j['project']['languages'].split(',')
                repositories = _read_repositories(j['project']['repositories'])
                reviewers = _read_reviewers(j['project']['reviewers'])
            except KeyError as e:
                logger.error("Failed to read json. File: '{}', Reason: '{}'.".format(file_path, e))
                return None
            else:
                return TranslationConfiguration(os.path.basename(file_path), file_path, name, platform, languages, repositories, reviewers)

def get_resource_slugs(translation_platform, translation_project_name, resource_repository_name, resource_paths):
    """ Return list of {<resource path>:<resource slug>} dictionary.
        Resource slugs are generated by given parameters (instead of querying them from translation platform).
    """
    if translation_platform == 'transifex':
        c = creds.get(translation_platform)
        if not c:
            logger.error("Failed to get creds for platform: '{}'.\n".format(translation_platform))
            return None 

        # @@@@ why did i need line below ???
        #project_slug = transifex_utils.generate_project_slug(c.project_slug_prefix, translation_project_name)
        results = []
        for r in resource_paths:
            results.append({r: transifex_utils.generate_resource_slug(c.resource_slug_prefix, [resource_repository_name, r])})
        return results
    else:
        logger.error("NIY: get_resource_slugs() for '{}'".format(translation_platform))
        return []

def get_translation_resource_slugs(translation_platform, translation_project_name):
    """ Return list of {<resource slug>:<name of resource} dictionary by querying specified project
        in translation platform.
        Project cache file will be created as results of this operation.
    """
    if translation_platform == 'transifex':
        c = creds.get(translation_platform)
        if not c:
            logger.error("Failed to get creds for platform: '{}'.\n".format(translation_platform))
            return None 
        pslug = transifex_utils.generate_project_slug(c.project_slug_prefix, translation_project_name)
        
        _setup_dir(os.path.join(settings.CACHE_DIR, translation_platform, 'projects', pslug))
        out = os.path.join(settings.CACHE_DIR, translation_platform, 'projects', pslug, 'project.cache')
        
        d = transifex_utils.get_platform_project_details(c, out, pslug)
        if d != None:
            results = []
            for x in d.resources:
                results.append({x.slug:x.name})
            return results
        else:
            logger.error("Failed to query project. project: '{}'.".format(pslug))
            return []
    else:
        logger.error("NIY: get_resource_slugs() for '{}'".format(translation_platform))
        return []

def _setup_dir(path):
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except OSError as e:
            logger.error("Failed to create directory: '{}'. Reason: {}".format(path, e))
        else:
            if not os.path.isdir(path):
                logger.error("Created directory does not exist: '{}'.".format(path))

'''
    Translation Platform Project Summary



'''
# Summary of a project in translation platform.
#
# keys          values
# -----------------------------------
# name          Name of the project.
# description   Project description.
# slug          Project slug.
TranslationPlatformProject = namedtuple('TranslationPlatformProject', 'name, description, slug')

def _TranslationPlatformProject_to_dict(o):
    return {'name': o.name, 'description': o.description, 'slug': o.slug}

def get_platform_projects(platform):
    """
    Return list of project information (summary).
    Return None on any errors.
    """
    c = creds.get(platform)
    if not c:
        logger.error("Failed to get creds for platform: '{}'.\n".format(platform))
        return None 
        
    # Cache directory (e.g. cache/transifex/projects) should be created before
    # any other platform query is made.
    _setup_dir(os.path.join(settings.CACHE_DIR, platform))
    _setup_dir(os.path.join(settings.CACHE_DIR, platform, 'projects'))
    out = os.path.join(settings.CACHE_DIR, platform, 'projects', 'projects.cache')

    if platform == 'transifex':
        d = transifex_utils.get_platform_projects(c, out)
        if d != None:
            l = []
            for x in d:
                l.append(TranslationPlatformProject(x.name, x.description, x.slug))
            return l
        else:
            return None
    else:
        logger.error("NIY: get_platform_projects() for '{}'".format(platform))
        return None

'''
    Translation Platform Project Details



'''
# Summary of a project resource in translation platform.
#
# slug                  resource slug
# name                  resource name
TranslationPlatformProjectResource = namedtuple('TranslationPlatformProjectResource', 'slug, name')

def _TranslationPlatformResource_to_dict(o):
    return {'slug': o.slug, 'name': o.name}

# Details of a project in translation plotform.
#
# keys                      values
# ---------------------------------------------------------------------
# name                      Name of the project.
# description               Project description.
# slug                      Project slug.
# source_language_code      Langauge code of source strings.
# resources                 List of TranslationPlatformProjectResource.
TranslationPlatformProjectDetails = namedtuple('TranslationPlatformProjectDetails', 'name, description, slug, source_language_code, resources')

def _TranslationPlatformProjectDetails_to_dict(o):
    l = []
    for x in o.resources:
        l.append(_TranslationPlatformResource_to_dict(x))
    return {'name': o.name, 'description': o.description, 'slug': o.slug, 'source_language_code': o.source_language_code, 'resources': l}

def get_platform_project_details(platform, pslug, use_cache=True):
    """
    Return project details (TranslationPlatformProjectDetails tuple) for a translation project.
    Return None on any errors.

    When use_cache=True and the cache file exists, read project details from the file.
    """
    c = creds.get(platform)
    if not c:
        logger.error("Failed to get creds for platform: '{}'.\n".format(platform))
        return None 
        
    _setup_dir(os.path.join(settings.CACHE_DIR, platform, 'projects', pslug))
    out = os.path.join(settings.CACHE_DIR, platform, 'projects', pslug, 'project.cache')

    if platform == 'transifex':
        if use_cache and os.path.isfile(out):
            d = transifex_utils.read_platform_project_details(c, out)
        else:
            d = transifex_utils.get_platform_project_details(c, out, pslug)
        if d != None:
            l = []
            for x in d.resources:
                l.append(TranslationPlatformProjectResource(x.slug, x.name))
            return TranslationPlatformProjectDetails(d.name, d.description, d.slug, d.source_language_code, l)
        else:
            logger.error("Failed to query translation project details. Reason: '{}'".format(ret.message))
            return None
    else:
        logger.error("NIY: get_platform_project_details() for '{}'".format(platform))
        return None

# Details of a resource in translation platform project.
#
# slug                  resource slug
# name                          resource name
# last_updated                  last updated date for the resource
# num_strings                   number of strings in the resource
# num_words                     number of words in the source
# language_code                 language code of the resource
# translated_language_codes     list of language code for translations
TranslationPlatformProjectResourceDetails = namedtuple('TranslationPlatformProjectResourceDetails', 'slug, name, last_updated, num_strings, num_words, language_code, translated_language_codes')

def _TranslationPlatformProjectResourceDetails_to_dict(o):
    return {'slug': o.slug, 'name': o.name, 'last_updated': o.last_updated, 'num_strings': o.num_strings, 'num_words': o.num_words, 'language_code': o.language_code, 'translated_language_codes': o.translated_language_codes}

def get_platform_project_resource_details(platform, pslug, rslug, use_cache=True):
    """
    Return details (TranslationPlatformProjectResource tuple) for a specified resource.
    Return None on any errors.

    When use_cache=True and the cache file exists, read resource details from the file.
    """
    c = creds.get(platform)
    if not c:
        logger.error("Failed to get creds for platform: '{}'.\n".format(platform))
        return None 
        
    _setup_dir(os.path.join(settings.CACHE_DIR, platform, 'projects', pslug, rslug))
    out = os.path.join(settings.CACHE_DIR, platform, 'projects', pslug, rslug, 'resource.cache')

    if platform == 'transifex':
        if use_cache and os.path.isfile(out):
            d = transifex_utils.read_platform_project_resource_details(c, out)
        else:
            d = transifex_utils.get_platform_project_resource_details(c, out, pslug, rslug)
        if d != None:
           return TranslationPlatformProjectResourceDetails(d.slug, d.name, d.last_updated, d.num_strings, d.num_words, d.language_code, d.translated_language_codes)
        else:
           return None
    else:
        logger.error("Unknown platform: '{}'.\n".format(platform))
        return None

# Details of translation strings.
#
# key                   key for the string.
# source                source string.
# translation           translation for the source string.
# reviewed              true when reviewed, false otherwise.               
# last_updated          last updated date.
TranslationPlatformTranslationStringDetails = namedtuple('TranslationPlatformTranslationStringDetails', 'key, source, translation, reviewed, last_updated')

def _TranslationPlatformTranslationStringDetails_to_dict(o):
    return {'key': o.key, 'source': o.source, 'translation': o.translation, 'reviewed': o.reviewed, 'last_updated': o.last_updated}

def get_platform_project_translation_strings(platform, pslug, rslug, lang, use_cache=True):
    """
    Return list of translated string (TranslationPlatformTranslationString tuple) for a specified language of resource.
    Return None on any errors.

    When use_cache=True and the cache file exists, read strings from the file.
    """
    c = creds.get(platform)
    if not c:
        logger.error("Failed to get creds for platform: '{}'.\n".format(platform))
        return None 
        
    _setup_dir(os.path.join(settings.CACHE_DIR, platform, 'projects', pslug, rslug))
    out = os.path.join(settings.CACHE_DIR, platform, 'projects', pslug, rslug, 'strings.' + lang + '.cache')

    if platform == 'transifex':
        if use_cache and os.path.isfile(out):
            d = transifex_utils.read_platform_project_translation_strings(c, out)
        else:
            d = transifex_utils.get_platform_project_translation_strings(c, out, pslug, rslug, lang)
        if d != None:
            l = []
            for x in d:
                l.append(TranslationPlatformTranslationStringDetails(x.key, x.source, x.translation, x.reviewed, x.last_updated))
            return l
        else:
           return None
    else:
        logger.error("Unknown platform: '{}'.\n".format(platform))
        return None

def get_platform_string_id(platform, **kwargs):
    if platform == 'transifex':
        if 'string_key' in kwargs:
            return transifex_utils.calc_string_hash(kwargs['string_key'])
        else:
            logger.error("string_key is missing to calc string hash for Transifex.")
            return None
    else:
        logger.error("Unknown platform: '{}'.\n".format(platform))
        return None

# Details of a source string.
#
# comment               Comment string attached to the source string.
# tags                  list of tags attached to the source string.
TranslationPlatformSourceStringDetails = namedtuple('TranslationPlatformSourceStringDetails', 'comment, tags')

def _TranslationPlatformSourceStringDetails_to_dict(o):
    l = []
    if o.tags:
        for x in o.tags:
            l.append(x)
    return {'comment': o.comment, 'tags': l}

def get_platform_project_source_string_details(platform, pslug, rslug, string_id, use_cache=True):
    """
    Return details of a source sting.
    Return None on any errors.

    When use_cache=True and the cache file exists, read string details from the file.
    """
    c = creds.get(platform)
    if not c:
        logger.error("Failed to get creds for platform: '{}'.\n".format(platform))
        return None 

    destdir = os.path.join(settings.CACHE_DIR, platform, 'projects', pslug, rslug, 'source')
    _setup_dir(destdir)
    out = os.path.join(destdir, string_id + '.cache')

    if platform == 'transifex':
        if use_cache and os.path.isfile(out):
            d = transifex_utils.read_platform_project_source_string_details(c, out)
        else:
            d = transifex_utils.get_platform_project_source_string_details(c, out, pslug, rslug, string_id)
        if d != None:
            return TranslationPlatformSourceStringDetails(d.comment, d.tags)
        else:
           return None
    else:
        logger.error("Unknown platform: '{}'.\n".format(platform))
        return None

