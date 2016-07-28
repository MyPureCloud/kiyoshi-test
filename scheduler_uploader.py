import sys, os
import json
from core.ResourceConfigurationClass import ResourceConfiguration
from core.TranslationConfigurationClass import TranslationConfiguration
from core.ResourceRepositoryClass import ResourceRepositoryInitializationError, Resource, PullRequest
from core.GithubRepositoryClass import GithubRepository
from core.BitbucketRepositoryClass import BitbucketRepository
from core.TranslationRepositoryClass import TranslationRepositoryInitializationError
from core.TransifexRepositoryClass import TransifexRepository
from core.CrowdinRepositoryClass import CrowdinRepository


def _upload_resource(translation_repository, resource_bundle, log_dir):
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

def _upload_translation(resource_repository, resource_bundle, translation_repository, assignee, reviewers, log_dir, options):
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

def _check_args(argv):
    if not (argv[0] == 'resource_repository' or argv[0] == 'translation_repository'):
        sys.stderr.write("Unknown upload destination string: '{}'.\n".format(argv[0]))
        return None

    if not os.path.isfile(argv[1]):
        sys.stderr.write("Resource configuration file not found: '{}'.\n".format(argv[1]))
        return None

    if not os.path.isfile(argv[2]):
        sys.stderr.write("Translation configuration file not found: '{}'.\n".format(argv[2]))
        return None

    if not os.path.isdir(argv[3]):
        sys.stderr.write("Log directory not found: '{}'.\n".format(argv[3]))
        return None

    params = {'upload_destination_string': argv[0], 'resource_config_file': argv[1], 'translation_config_file': argv[2], 'log_dir': argv[3]}

    # argv[4] is a string for optional parameters, such as option1:option2.
    if argv[4] == 'ALL_LANG_PER_RESOURCE':
        params['all_lang_per_resource'] = True
    elif argv[4] == 'ANY_LANG_PER_RESOURCE':
        params['all_lang_per_resource'] = False
    else:
        sys.stderr.write("Ignored unknown option string: '{}'.\n".format(argv[4]))
        params['all_lang_per_resource'] = False

    return params 
    
def _get_resource_configuration(resource_config_file):
    config = ResourceConfiguration()
    if config.parse(resource_config_file):
        return config
    else:
        return None

def _get_translation_configuration(translation_config_file):
    config = TranslationConfiguration()
    if config.parse(translation_config_file):
        return config
    else:
        return None

def _get_resource_repository(resource_config, log_dir):
    platform =  resource_config.get_repository_platform()
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

def _get_translation_repository(trans_config, log_dir):
    platform =  trans_config.get_project_platform()
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

def main(argv):
    param = _check_args(argv)
    if not param:
        return

    options = {}
    options['all_lang_per_resource'] = param['all_lang_per_resource']

    sys.stdout.write("Start processing: '{}'...\n".format(param['resource_config_file']))

    resource_config = _get_resource_configuration(param['resource_config_file'])
    trans_config = _get_translation_configuration(param['translation_config_file'])
    if resource_config == None or trans_config == None:    
        sys.stdout.write("End processing: '{}'.\n".format(param['resource_config_file']))
        return

    resource_repo = _get_resource_repository(resource_config, param['log_dir'])
    trans_repo = _get_translation_repository(trans_config, param['log_dir'])
    if resource_repo == None or trans_repo == None:    
        sys.stdout.write("End processing: '{}'.\n".format(param['resource_config_file']))
        return

    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    sys.stdout.write("Number of resources: '{}'.\n".format(num_resources))
    if num_resources == 0:
        sys.stdout.write("End processing: '{}'.\n".format(param['resource_config_file']))
        return

    success = False
    if param['upload_destination_string'] == 'translation_repository':
        success = _upload_resource(trans_repo, resource_bundle, param['log_dir'])
    elif param['upload_destination_string'] == 'resource_repository':
        reviewers = list(set(resource_config.get_pullrequest_reviewers() + trans_config.get_project_reviewers()))
        assignee = resource_config.get_pullrequest_assignee()
        success = _upload_translation(resource_repo, resource_bundle, trans_repo, assignee, reviewers, param['log_dir'], options)
    else:
        pass

    sys.stdout.write("End processing: '{}'.\n".format(param['resource_config_file']))
    sys.stdout.flush()
    sys.stderr.flush()

if __name__ == '__main__':
    main(sys.argv[1:])

