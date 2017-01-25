import os
from collections import namedtuple
import json
from datetime import datetime

import logging
logger = logging.getLogger('tpa')

import plugins.bitbucket.utils as bitbucket_utils
import plugins.github.utils as github_utils
import plugins.github.api as github_api

import settings
import creds

def to_dict(o):
    if type(o) == ResourceDetails:
        return _ResourceDetails_to_dict(o)
    elif type(o) == PullRequestSummary:
        return _PullRequestSummary_to_dict(o)
    elif type(o) == ResourceConfiguration:
        return _ResourceConfiguration_to_dict(o)
    else:
        logger.error("Unknown type: '{}'.".format(type(o)))
        return {}



'''
    Resource

    This is to provide information of translatable resources defined in resource configuration file.
'''

# Translation
#
# keys              values
# ----------------------------------------------------------------------
# language_code     Language code for the translation.
# path              Path of the translation.
Translation = namedtuple('Translation', 'language_code, path')

def _Translation_to_dict(o):
    return o._asdict()

def _to_translations(translations):
    results = []
    for t in translations:
        results.append(Translation(t.language_code, t.path))
    return results

# Resource
#
# keys              values
# ----------------------------------------------------------------------
# path              Path of the resource.
# translations      List of translation for the resource (Translation tuple).
Resource = namedtuple('Resource', 'path, translations')

def _Resource_to_dict(o):
    translations = []
    for t in o.translations:
        translations.append(_Translation_to_dict(t))
    return {'path': o.path, 'translations': translations}

def _to_resources(resources):
    results = []
    for r in resources:
        results.append(Resource(r.path, _to_translations(r.translations)))
    return results

# Resource Reposiory Details.
#
# keys              values
# ----------------------------------------------------------------------
# url               URL to the repository.
# platform          Resource repository platform name (e.g. Bitbucket).
# owner             Resource repository owner of the platform (e.g. inindca)
# name              Resource repository name.
# branch            Branch of the repository (e.g. master).
# resources         List of resources (Resource tuple).
ResourceDetails = namedtuple('ResourceDetails', 'url, platform, owner, name, branch, resources') 

def _ResourceDetails_to_dict(o):
    resources = []
    for res in o.resources:
        resources.append(_Resource_to_dict(res))
    return {'url': o.url, 'platform': o.platform, 'owner': o.owner, 'name': o.name, 'branch': o.branch, 'resources': resources}

def get_details(config_filename):
    """
    Return resource details, or None on any errors.
    """
    c = get_configuration(filename=config_filename)
    if c:
        return ResourceDetails(c.repository_url, c.repository_platform, c.repository_owner, c.repository_name, c.repository_branch, _to_resources(c.resources))
    else:    
        logger.error("Failed to get configuration for resource repository details. configuration file: '{}'.".format(config_filename))
        return None

'''
    Pull Request Summary

'''
# Pull Request Summary.
#
# key                           value
# -------------------------------------------------------
# date                          Date of pull request is issued.
# number                        Pull request number.
# url                           URL to the pull request.
# state                         Pull rquest state. e.g. 'open'
PullRequestSummary = namedtuple('PullRequestSummary', 'date, number, url, state')

def _PullRequestSummary_to_dict(o):
    return {'date': o.date, 'number': o.number, 'url': o.url, 'state': o.state}

def query_pullrequest(platform, repository_owner, repository_name, author=None, limit=1):
    """
    Return list of pull request summary.

    OPTION
    ------
    author:                 Username of pull request submitter. Default author is obtained from  username in creds file.
    limit:                  Max number of pullrequest to obtain for the author.
    """
    
    # Try query 30 pull requests for ANY author with hoping that pull requests we are looking for are in the first 30. 
    NUM_TOTAL_QUERY = 30

    if platform == 'bitbucket':
        c = creds.get('bitbucket')
        if not c:
            return None
        PR_STATE_STRINGS = [] # query all state
        l = bitbucket_utils.get_pullrequests({'username':c.username, 'userpasswd': c.userpasswd}, repository_owner, repository_name, PR_STATE_STRINGS, NUM_TOTAL_QUERY)
        if l == None or len(l) == 0:
            return None

        # Try pcik up pull requests for the specific author.
        if author:
            submitter = author
        else:
            submitter = c.username
        r = []
        n = 0
        for x in l:
            if n >= limit:
                break
            else:
                if submitter == x['submitter']:
                    r.append(PullRequestSummary(x['date'], x['number'], x['pr_url'], x['state']))
                    n += 1
                else:
                    pass
        return r
    elif platform== 'github':
        c = creds.get('github')
        if not c:
            return None

        PR_STATE_STRINGS = ['open', 'closed'] # query all state
        # Try pcik up pull requests for the specific author.
        if author:
            submitter = author
        else:
            submitter = c.username
        l = github_utils.get_pullrequests({'username':c.username, 'userpasswd': c.userpasswd}, repository_owner, repository_name, PR_STATE_STRINGS, submitter, NUM_TOTAL_QUERY)
        if l == None or len(l) == 0:
            return None

        r = []
        n = 0
        for x in l:
            if n >= limit:
                break
            else:
                r.append(PullRequestSummary(x['date'], x['number'], x['pr_url'], x['state']))
                n += 1
        return r
    else:
        logger.error("Unknown resource platform: '{}'.\n".format(resource_platform))
        return None 


'''
    Resoruce Configuration


    Resource configuration file format.

{
    "repository": {
        "platform": "bitbucket",
        "url": "https://bitbucket.org/inindca/i18n-automation.git",
        "owner": "inindca"
        "name": "i18n-automation",
        "branch": "master",
        "resources": [
            {
                "resource": {
                    "path": "test/src/flat.json",
                    "filetype": "json",
                    "language_code": "en-US"
                    "translations": [
                        {"ja": "test/src/flat_ja.json"}
                    ]
                }
            }, 
            {
                "resource": {
                    "path": "test/src/structured.json",
                    "filetype": "json",
                    "language_code": "en-US"
                    "translations": [
                        {"ja": "test/src/structured.json"}
                    ]
                }
            }
        ],
        "pullrequest": {
            "reviewers": ["kiyoshiiwase"],
            "title": "(TEST) Translation Updates"
        },
        "options": [
            "option_1",
            "option_2"
        ]
    }
}
'''

# ResourceConfigurationTranslation
#
# keys          values
# -----------------------------------
# language_code     Language code for the translation file. e.g. 'es-MX'
# path              Path to the translation file in repository. e.g. src/strings/en-MX/localizable.json
ResourceConfigurationTranslation = namedtuple('ResourceConfigurationTranslation', 'language_code, path')

# ResourceConfigurationResource
#
# keys          values
# -----------------------------------
# path          Path to a resouce file in repository. e.g. 'src/strings/en-US.json'
# filetype      File type string for the resource file. e.g. 'json'
# language_code     Language code for the resouce file. e.g. 'en-US'
# translations      List of Translation tuples for translation files.
ResourceConfigurationResource = namedtuple('ResourceConfigurationResoruce', 'path, filetype, language_code, translations')

# PullRequest for ResourceConfiguration 
# keys          values
# -----------------------------------
# title         One line text string for a pull request title.
# reviewers     List of reviewers.
ResourceConfigurationPullRequest = namedtuple('ResourceConfigurationPullRequest', 'title, reviewers')

# Option
#
# keys          values
# -----------------------------------
# name          Name of option. 
# value         Value of the option. 
ResourceConfigurationOption = namedtuple('ResourceConfigurationOption', 'name, value')

# Represents a Resource Configuration file.
#
# keys          values
# -----------------------------------
# filename                  Resource file name
# path                      Resource file path
# --- configuration file context ----
# repository_platform       Resource repository platform name (e.g. Bitbucket).
# repository_url            URL to the repository.
# repository_name           Resource repository name.
# repository_owner          Resource repository owner of the platform (e.g. inindca)
# repository_branch         Branch of the repository (e.g. master).
# resources                 List of Resource tuples
# pullrequest               A PullRequest tule
# options                   List of Option tuples.
ResourceConfiguration = namedtuple('ResourceConfiguration', 'filename, path, repository_platform, repository_url, repository_name, repository_owner, repository_branch, resources, pullrequest, options')

def _options_to_dict(o):
    results = []
    for x in o:
        results.append({x.name: x.value})
    return results

def _PullRequest_to_dict(o):
    return {'title': o.title, 'reviewers': o.reviewers}

def _translations_to_dict(o):
    results = []
    for x in o:
        results.append({x.language_code: x.path})
    return results

def _resources_to_dict(o):
    results = []
    for x in o:
        results.append({'path': x.path, 'filetype': x.filetype, 'language_code': x.language_code, 'translations': _translations_to_dict(x.translations)})
    return results

def _ResourceConfiguration_to_dict(o):
    return {
            'filename': o.filename,
            'path': o.path,
            'repository_platform': o.repository_platform,
            'repository_url': o.repository_url,
            'repository_name': o.repository_name,
            'repository_owner': o.repository_owner,
            'repository_branch': o.repository_branch,
            'resources': _resources_to_dict(o.resources),
            'pullrequest': _PullRequest_to_dict(o.pullrequest),
            'options': _options_to_dict(o.options)
            }

def _revert_ResourceConfigurationResources_to_dict(o):
    l = []
    for x in o:
        l.append({"resource": x})
    return l

def _revert_ResourceConfiguration_to_dict(o):
    """
    This performs vice versa operation of _ResoruceConfiguration_to_dict().
    'filename' and 'path' will be discarded as a result of this operation.

    Return dictonary in original configuration file format.
    Return None on any errors.
    """
    try:
        d = { "repository": {
                "platform": o['repository_platform'],
                "url": o['repository_url'],
                "owner": o['repository_owner'],
                "name": o['repository_name'],
                "branch": o['repository_branch'],
                "resources": _revert_ResourceConfigurationResources_to_dict(o['resources']),
                "pullrequest": o['pullrequest'],
                "options": o['options']
                }}
    except KeyError as e:
        logger.error("Unknown dict format. Reason: '{}'.".format(str(e)))
        return None
    else:
        return d

def to_resource_configuration_file_format(o):
    """
    Return dict of resource configuration out of given str or dict object.
    Return None on any errors.
    """
    if type(o) == str:
        try:
            d = json.loads(o)
        except ValueError as e:
            logger.error("Failed to load as json. Reason: '{}', Text: '{}'".format(str(e), o))
            return None
        else:
            return _revert_ResourceConfiguration_to_dict(d)
    elif type(o) == dict:
        return _revert_ResourceConfiguration_to_dict(o)
    else:
        logger.error("Unknown object type to convert to ResourceConfiguratrion tuple. Type: '{}'.".format(type(o)))
        return None

def update_configuration(resource_configuration_filename, obj):
    """
    Return updated configuration in ResourceConfiguration, when update is succeeded.
    Return None on any errors.
    """
    data = to_resource_configuration_file_format(obj)
    if data:
        if write_configuration(resource_configuration_filename, data):
            return get_configuration(filename=resource_configuration_filename)
    else:
        return None

# TODO --- separate into two functions like below. 
#          get_configurations() <--- returns list of ResourceConfiguration
#          get_configuration(filename or json) <--- return a single ResourceConfiguration
def get_configuration(**kwargs):
    """ 
    Return list of ResourceConfiguration for all of resource configuration files.
    Or
    Return a ResoruceConfiguration for specified filename when filename is specified.
    Or
    Return None on any errors. 
    """

    if 'filename' in kwargs:
        return _read_configuration_file(os.path.join(settings.CONFIG_RESOURCE_DIR, kwargs['filename']))
    else:
        results = []
        for filename in os.listdir(settings.CONFIG_RESOURCE_DIR):
            if not os.path.splitext(filename)[1] == '.json':
                continue
            c = _read_configuration_file(os.path.join(settings.CONFIG_RESOURCE_DIR, filename))
            if c:
                results.append(c)
        return results

def _read_options(o):
    options = []
    # options are optional.
    if o:
        for x in o:
            for k, v in x.items():
                options.append(ResourceConfigurationOption(k, v))
    return options
    
def _read_pullrequest(o):
    reviewers = []
    # reviewers are optional.
    if o['reviewers']:
        for x in o['reviewers']:
            reviewers.append(x)
    return ResourceConfigurationPullRequest(o['title'], reviewers)

def _read_translations(o):
    results = []
    for x in o:
        for k,v in x.items():
            results.append(ResourceConfigurationTranslation(k, v))
    return results

def _read_resources(o):
    results = []
    for x in o:
        translations = _read_translations(x['resource']['translations'])
        results.append(ResourceConfigurationResource(x['resource']['path'], x['resource']['filetype'], x['resource']['language_code'], translations))
    return results

def _read_configuration_file(file_path):
    with open(file_path) as fi:
        try: # catch all exceptions here, including one raised in subsquent functions.
            j = json.load(fi)
            platform = j['repository']['platform']
            url = j['repository']['url']
            owner = j['repository']['owner']
            name = j['repository']['name']
            branch = j['repository']['branch']
            resources = _read_resources(j['repository']['resources'])
            pullrequest = _read_pullrequest(j['repository']['pullrequest'])
            options = _read_options(j['repository']['options'])
        except ValueError as e:
            logger.error("Failed to load json. File: '{}', Reason: '{}'.".format(file_path, e))
            return None
        except KeyError as e:
            logger.error("Failed to read json. File: '{}', Reason: '{}'.".format(file_path, e))
            return None
        else:
            return ResourceConfiguration(os.path.basename(file_path), file_path, platform, url, name, owner, branch, resources, pullrequest, options)

def _create_ResourceConfiguration(resource_configuration_file_path, json_data):
    try: # catch all exceptions here, including one raised in subsquent functions.
        platform = json_data['repository']['platform']
        url = json_data['repository']['url']
        owner = json_data['repository']['owner']
        name = json_data['repository']['name']
        branch = json_data['repository']['branch']
        resources = _read_resources(json_data['repository']['resources'])
        pullrequest = _read_pullrequest(json_data['repository']['pullrequest'])
        options = _read_options(json_data['repository']['options'])
    except KeyError as e:
        logger.error("Failed to read json. Reason: '{}', json_data: '{}'.".format(resource_configuration_file_path, e, json_data))
        return None
    else:
        return ResourceConfiguration(os.path.basename(resource_configuration_file_path),
                    resource_configuration_file_path, platform, url, name, owner, branch, resources, pullrequest, options)

def write_configuration(resource_configuration_filename, data):
    """
    Return True on success.
    Return None otherwise.
    """
    path = os.path.join(settings.CONFIG_RESOURCE_DIR, resource_configuration_filename)
    if not os.path.isfile(path): 
        return False

    # TODO --- use git to keep changes
    old = os.path.join(settings.CONFIG_RESOURCE_DIR, resource_configuration_filename + '.OLD.'+ datetime.now().strftime('%Y%m%d.%H%M%S'))
    os.rename(path, old)
    with open(path, 'w') as fo:
        fo.write(json.dumps(data))
    return True
