import os, sys
import logging
import collections
import json

import settings
from core.ResourceConfigurationClass import ResourceConfiguration
from core.TranslationConfigurationClass import TranslationConfiguration
from core.ResourceRepositoryClass import ResourceRepositoryInitializationError, Resource, PullRequest
from core.GithubRepositoryClass import GithubRepository
from core.BitbucketRepositoryClass import BitbucketRepository
from core.TranslationRepositoryClass import TranslationRepositoryInitializationError
from core.TransifexRepositoryClass import TransifexRepository
from core.CrowdinRepositoryClass import CrowdinRepository

logger = logging.getLogger(__name__)

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
    logger.info(result)
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

def upload(params, options):
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
        reviewers = list(set(resource_config.get_pullrequest_reviewers() + trans_config.get_project_reviewers()))
        assignee = resource_config.get_pullrequest_assignee()
        success = upload_translation(resource_repo, resource_bundle, trans_repo, assignee, reviewers, params['log_dir'], options)
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

    config = ResourceConfiguration()
    if config.parse(resource_config_file):
        return config
    else:
        return None

def create_translation_configuration(translation_config_file):
    if not os.path.isfile(translation_config_file):
        logger.error("File not found: {}".format(translation_config_file))
        return None

    config = TranslationConfiguration()
    if config.parse(translation_config_file):
        return config
    else:
        return None

def create_resource_repository(resource_config, log_dir):
    platform = resource_config.get_repository_platform()
    if platform == 'github':
        try:
            repo = GithubRepository(resource_config, log_dir)
        except ResourceRepositoryInitializationError as e:
            sys.stderr.write("'{}'.\n".format(e))
            return None
        else:
            return repo
    elif platform == 'bitbucket':
        try:
            repo = BitbucketRepository(resource_config, log_dir)
        except ResourceRepositoryInitializationError as e:
            sys.stderr.write("'{}'.\n".format(e))
            return None 
        else:
            return repo
    else:
        sys.stderr.write("Unknown resource repository platform: '{}'.\n".format(platform))
        return None

def create_translation_repository(trans_config, log_dir):
    platform = trans_config.get_project_platform()
    if platform == 'transifex':
        try:
            repo = TransifexRepository(trans_config, log_dir)
        except TranslationRepositoryInitializationError as e:
            sys.stderr.write("'{}'.\n".format(e))
            return None
        else:
            return repo
    elif platform == 'crowdin':
        try:
            repo = CrowdinRepository(trans_config, log_dir)
        except TranslationRepositoryInitializationError as e:
            sys.stderr.write("'{}'.\n".format(e))
            return None
        else:
            return repo
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
                "operation": "ResourceUpload",
                "results": "Skipped (resource not available in local)",
                "resource_full_path": os.path.join(resource.repository_name, resource.resource_path)
                }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            continue

        if not translation_repository.import_resource(resource):
            success = False

    return success

def upload_translation(resource_repository, resource_bundle, translation_repository, assignee, reviewers, log_dir, options):
    success = True
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

    feature_branch_name = resource_repository.import_bundles(trans_bundles, options)
    if feature_branch_name:
        sys.stdout.write("Imports in branch: '{}'.\n".format(feature_branch_name))
        pr = PullRequest()
        pr.branch_name = feature_branch_name
        pr.assignee = assignee
        pr.reviewers = reviewers
        resource_repository.submit_pullrequest(pr)
        if pr.submitted:
            if not pr.number:
                sys.stdout.write("Submitted pull request.\n")
            else:
                sys.stdout.write("Submitted pull request #{}.\n".format(pr.number))
        else:
            if pr.errors == 0:
                sys.stdout.write("{}\n".format(pr.message))
            else:
                success = False
                sys.stderr.write("{}\n".format(pr.message))
    else:
        sys.stdout.write("(No pull request submitted.)\n")

    return success

