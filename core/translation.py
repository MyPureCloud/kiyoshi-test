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
    else:
        logger.error("Unknown type: '{}'.".format(type(o)))
        return {}




'''
    Translation Details 

    Translation repository information.
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
# translated_resource_repositories  List of translated resource repository.
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
            'num_translated_strings': o.num_translated_strigs,
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
        ret = transifex_utils.get_all_translation_stats(c, project_slug, resource_slug)
        if not ret.succeeded:
            logger.error("Failed to get resource details for '{}/{}'. Reason: '{}'.".format(resource_repository_name, resource_path, ret.message))
            return None 

        results = []
        # convert TransifeixTranslationStats to LanguageStats
        for stats in ret.output:
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

        project_slug = transifex_utils.generate_project_slug(c.project_slug_prefix, kwargs['project_name'])
        resource_slug = transifex_utils.generate_resource_slug(c.resource_slug_prefix, [kwargs['resource_repository_name'], kwargs['resource_path']])
        ret = transifex_utils.get_resource_details(c, project_slug, resource_slug)
        if ret.succeeded:
            # convert TransifeixMasterLanguageStats to MasterLanguageStats
            return MasterLanguageStats(ret.output.slug, ret.output.name, ret.output.last_updated, ret.output.num_strings, ret.output.num_words, ret.output.language_code)
        else:
            logger.error("Failed to get resource details for '{}/{}'. Reason: '{}'.".format(kwargs['resource_repository_name'], kwargs['resource_path'], ret.message))
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
    """ Return list of {<resource path>:<resource slug>} dictionary. """
    if translation_platform == 'transifex':
        c = creds.get(translation_platform)
        if not c:
            logger.error("Failed to get creds for platform: '{}'.\n".format(translation_platform))
            return None 

        project_slug = transifex_utils.generate_project_slug(c.project_slug_prefix, translation_project_name)
        results = []
        for r in resource_paths:
            results.append({r: transifex_utils.generate_resource_slug(c.resource_slug_prefix, [resource_repository_name, r])})
        return results
    else:
        logger.error("NIY: get_resource_slugs() for '{}'".format(translation_platform))
        return []

def get_translation_slugs(translation_platform, translation_project_name):
    """ Return list of {<slug>:<name of the slug>} dictionary. """
    if translation_platform == 'transifex':
        c = creds.get(translation_platform)
        if not c:
            logger.error("Failed to get creds for platform: '{}'.\n".format(translation_platform))
            return None 
        project_slug = transifex_utils.generate_project_slug(c.project_slug_prefix, translation_project_name)
        ret = transifex_utils.query_project(c, project_slug)
        if ret.succeeded:
            results = []
            for r in ret.output.resources:
                results.append({r.slug:r.name})
            return results
        else:
            logger.error("Failed to query project. project: '{}', Reason: '{}'.".format(project_slug, ret.message))
            return []
    else:
        logger.error("NIY: get_resource_slugs() for '{}'".format(translation_platform))
        return []

