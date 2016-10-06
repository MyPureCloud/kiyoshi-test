import os
import sys
import collections
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

import settings
from core.config.resource.parser import ResourcePlatformConfiguration
from core.config.translation import TranslationPlatformConfiguration
from core.config.creds import GitCredsConfiguration, TransifexCredsConfiguration
from core.resource_repository import Resource

from plugins.resource_repository.github.repository import GithubRepository
from plugins.resource_repository.bitbucket.repository import BitbucketRepository
from plugins.translation_repository.transifex.api import TransifexApiCreds
from plugins.translation_repository.transifex.repository import TransifexRepository
from plugins.translation_repository.crowdin.repository import CrowdinRepository

import scheduler.jobstore.jobstore as jobstore 

# Resource Configuration file context.
#
#       NOTE:
#       This tuple is for specific display use. 
#       So, this is slightly different from core.config.resource.parser.ResourceConfiguration tuple, which
#       continas all of resouce configuration file context, but this does not.
#       This has extra field 'job_status' which needs to be read from the latest job execution file.
#
# keys          values
# -----------------------------------
# filename                  Resource file name
# path                      Resource file path
# parsed                    True when the resource file is successfully parsed, False otherwise.
# job_status                'NOT USED' if the resource configuration file is not used for any jobs.
#                           Othewise, job's status is set. e.g. 'active' or 'suspended'.
# repository_platform       Resource repository platform name (e.g. Bitbucket).
# repository_owner          Resource repository owner of the platform (e.g. inindca)
# repository_name           Resource repository name.
# repository_branch         Branch of the repository (e.g. master).
# repository_resource_len   Number of resource files defined in the resource file.
ResourceConfigurationFile = namedtuple('ResourceConfigurationFile', 'filename, path, parsed, job_status, repository_platform, repository_owner, repository_name, repository_branch, repository_resource_len')

def get_transifex_creds(non_default_creds_file_path=None):
    """ Return TransifexApiCreds by reading given creds file, or, by reading
        default Transifex creds file.
        Return empty tuple, when none of above is met.
    """
    if non_default_creds_file_path:
        path = non_default_creds_file_path
    else:
        path = settings.TRANSIFEX_CREDS_FILE

    if not os.path.isfile(path):
        sys.stderr.write("File not found: {}.\n".format(path))
        return TransifexApiCreds(None, None) 

    t = TransifexCredsConfiguration()
    if not t.parse(path):
        sys.stderr.write("Failed to parse: {}\n".format(path))
        return TransifexApiCreds(None, None) 
    else:
        return TransifexApiCreds(t.get_username(), t.get_userpasswd())

def get_resource_configuration_path(resource_config_file_name):
    path = os.path.join(settings.CONFIG_RESOURCE_DIR, resource_config_file_name)
    if os.path.isfile(path):
        return path
    else:
        return None

def get_resource_configurations_from_directory():
    """ Return list of ResourceConfigurationFile tuples by
        reading yaml files in resource configuation directory.

        parsed value is True when the yaml file is parsed
        properly, then repository informations are set in
        the tuple.
        Otherwise, the value is False and all of repository
        informations are set as 'N/A'. This is to indicate
        the yaml file exists but contians error(s).
    """
    jobs = jobstore.read_job_file()

    results = []
    for filename in os.listdir(settings.CONFIG_RESOURCE_DIR):
        if not os.path.splitext(filename)[1] == '.yaml':
            continue

        config_path = os.path.join(settings.CONFIG_RESOURCE_DIR, filename)
        config = create_resource_configuration(config_path)
        if config:
            status = 'NOT USED'
            for job in jobs:
                if filename == job.resource_config_filename:
                    status = job.status
                    break
            results.append(ResourceConfigurationFile(
                filename,
                config_path,
                True,
                status,
                config.get_repository_platform(),
                config.get_repository_owner(),
                config.get_repository_name(),
                config.get_repository_branch(),
                config.get_resource_len()
            ))
        else:
            logger.error("Faild to read resource config file: '{}'.".format(config_path))
            results.append(ResourceConfigurationFile(
                filename,
                config_path,
                False,
                'N/A',
                'N/A',
                'N/A',
                'N/A',
                'N/A',
                'N/A'
            ))

    return results

def get_translation_project_stats(translation_config_filename):
    trans_config = create_translation_configuration(os.path.join(settings.CONFIG_TRANSLATION_DIR, translation_config_filename))
    if not trans_config:    
        logger.error("Failed to create translation config.")
        return {}

    trans_repo = create_translation_repository(trans_config, '.') # 2nd param is log_dir (not using)
    if not trans_repo:    
        logger.error("Failed to create translation repository.")
        return {}
    
    stats = {}
    result = trans_repo.get_stats_project()
    if not result:
        return stats

    try:
        d = json.loads(result)
        stats['project_name'] = d['name']
        stats['project_slug'] = d['slug']
        for r in d['resources']:
            stats[r['slug']] = r['name']
    except ValueError as e:
        pass
    return stats 

def get_slugs(resource_config_filename, translation_config_filename, translation_slugs, resource_slugs):
    resource_config = create_resource_configuration(os.path.join(settings.CONFIG_RESOURCE_DIR, resource_config_filename))
    if not resource_config:    
        logger.error("Failed to create resource config.")
        return

    trans_config = create_translation_configuration(os.path.join(settings.CONFIG_TRANSLATION_DIR, translation_config_filename))
    if not trans_config:    
        logger.error("Failed to create translation config.")
        return

    trans_repo = create_translation_repository(trans_config, '.') # 2nd param is log_dir (not using)
    if not trans_repo:    
        logger.error("Failed to create translation repository.")
        return

    project_name = trans_config.get_project_name()
    translation_slugs['platform'] = trans_config.get_project_platform()
    translation_slugs['project_name'] = project_name
    translation_slugs['project_slug'] = trans_repo.generate_project_slug(project_name)

    repo_name = resource_config.get_repository_name()
    n = resource_config.get_resource_len()
    resource_paths = []
    for i in range(0, n):
        resource_paths.append(resource_config.get_resource_path(i))
    resource_paths.sort()
    for resource_path in resource_paths:
        resource_slugs[resource_path] = trans_repo.generate_resource_slug([repo_name, resource_path])

def upload(params):
    sys.stdout.write("Start processing: '{}'...\n".format(params['resource_config_file']))

    resource_config = create_resource_configuration(params['resource_config_file'])
    trans_config = create_translation_configuration(params['translation_config_file'])
    if resource_config == None or trans_config == None:    
        sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
        return False

    resource_repo = create_resource_repository(resource_config, params['log_dir'])
    trans_repo = create_translation_repository(trans_config, params['log_dir'])
    if resource_repo == None or trans_repo == None:    
        sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
        return False

    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    sys.stdout.write("Number of resources: '{}'.\n".format(num_resources))
    if num_resources == 0:
        sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
        return True

    success = False
    if params['upload_destination_string'] == 'translation_repository':
        success = upload_resource(trans_repo, resource_bundle, params['log_dir'])
    elif params['upload_destination_string'] == 'resource_repository':
        success = upload_translation(resource_repo, resource_bundle, trans_repo, params['log_dir'], trans_config)
    else:
        pass

    sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
    sys.stdout.flush()
    sys.stderr.flush()
    return success

def create_resource_configuration(resource_config_file):
    if not os.path.isfile(resource_config_file):
        logger.error("File not found: {}".format(resource_config_file))
        return None

    config = ResourcePlatformConfiguration()
    if config.parse(resource_config_file):
        return config
    else:
        return None

def create_translation_configuration(translation_config_file):
    if not os.path.isfile(translation_config_file):
        logger.error("File not found: {}".format(translation_config_file))
        return None

    config = TranslationPlatformConfiguration()
    if config.parse(translation_config_file):
        return config
    else:
        return None

def create_resource_repository(resource_config, log_dir):
    platform = resource_config.get_repository_platform()
    if platform == 'github':
        if not os.path.isfile(settings.GITHUB_CREDS_FILE):
            sys.stderr.write("File not found: {}.\n".format(settings.GITHUB_CREDS_FILE))
            return None

        creds = GitCredsConfiguration()
        if not creds.parse(settings.GITHUB_CREDS_FILE):
            sys.stderr.write("Failed to parse: {}\n".format(settings.GITHUB_CREDS_FILE))
            return None

        return GithubRepository(resource_config, creds, log_dir)
    elif platform == 'bitbucket':
        if not os.path.isfile(settings.BITBUCKET_CREDS_FILE):
            sys.stderr.write("File not found: {}.\n".format(settings.BITBUCKET_CREDS_FILE))
            return None

        creds = GitCredsConfiguration()
        if not creds.parse(settings.BITBUCKET_CREDS_FILE):
            sys.stderr.write("Failed to parse: {}\n".format(settings.BITBUCKET_CREDS_FILE))
            return None
        
        return BitbucketRepository(resource_config, creds, log_dir)
    else:
        sys.stderr.write("Unknown resource repository platform: '{}'.\n".format(platform))
        return None

def create_translation_repository(trans_config, log_dir):
    platform = trans_config.get_project_platform()
    if platform == 'transifex':
        if not os.path.isfile(settings.TRANSIFEX_CREDS_FILE):
            sys.stderr.write("File not found: {}.\n".format(settings.TRANSIFEX_CREDS_FILE))
            return None

        creds = TransifexCredsConfiguration()
        if not creds.parse(settings.TRANSIFEX_CREDS_FILE):
            sys.stderr.write("Failed to parse: {}\n".format(settings.TRANSIFEX_CREDS_FILE))
            return False

        return TransifexRepository(trans_config, creds, log_dir)
    elif platform == 'crowdin':
        return CrowdinRepository(trans_config, log_dir)
    else:
        sys.stderr.write("Unknown translation platform: '{}'.\n".format(platform))
        return None

def upload_resource(translation_repository, resource_bundle, log_dir):
    success = True
    trans_bundles = []
    for resource in resource_bundle:
        sys.stdout.write("Processing resource '{}'...\n".format(resource.resource_path))

        if not resource.available():
            d = {
                'operation': "ResourceUpload",
                'results': "FAILURE",
                'reason': "Resource not available in local repository.",
                'resource_full_path': os.path.join(resource.repository_name, resource.resource_path)
                }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            continue

        if not translation_repository.import_resource(resource):
            success = False

    return success

def upload_translation(resource_repository, resource_bundle, translation_repository, log_dir, trans_config):
    trans_bundles = []
    for resource in resource_bundle:
        sys.stdout.write("Preparing translation candidates for resource: '{}'...\n".format(resource.resource_path))

        if not resource.available():
            sys.stdout.write("Skipped. Resource not available in local.\n")
            continue

        trans_bundle = translation_repository.get_translation_bundle(resource.repository_name, resource.resource_path, resource.resource_translations)
        if trans_bundle:
            trans_bundles.append(trans_bundle)
        else:
            sys.stdout.write("Skipped. No translation bundle for this resource.\n")

    feature_branch_name = resource_repository.import_bundles(trans_bundles)
    if feature_branch_name:
        sys.stdout.write("Created branch for changes: '{}'.\n".format(feature_branch_name))
        additional_reviewers = trans_config.get_project_reviewers()
        results = resource_repository.submit_pullrequest(feature_branch_name, additional_reviewers)
        return results.errors == 0
    else:
        sys.stdout.write("No branch created for changes.\n")
        return True

