import sys, os
from ResourceConfigurationClass import ResourceConfiguration
from TranslationConfigurationClass import TranslationConfiguration
from ResourceRepositoryClass import ResourceRepositoryInitializationError, Resource, PullRequest
from GithubRepositoryClass import GithubRepository
from BitbucketRepositoryClass import BitbucketRepository
from TranslationRepositoryClass import TranslationRepositoryInitializationError
from TransifexRepositoryClass import TransifexRepository

def _find_translation_config(resource_repo_name, config_dir):
    translation_config_dir = os.path.join(config_dir, 'translation')
    if not os.path.isdir(translation_config_dir):
        sys.stderr.write("Translation config directory NOT found: '{}'.\n".format(translation_config_dir))
        return None

    sys.stdout.write("Looking for translation config in '{}'...\n".format(translation_config_dir))
    candidates = []
    for filename in os.listdir(translation_config_dir):
        if os.path.splitext(filename)[1] == '.yaml':
            path = os.path.join(translation_config_dir, filename)
            c = TranslationConfiguration()
            if not c.parse(path):
                continue
            n = c.get_project_repository_len()
            for i in range(0, n):
                if c.get_project_repository_name(i) == resource_repo_name:
                    candidates.append(c)
                    sys.stdout.write("Matched: '{}'.\n".format(path))

    total = len(candidates)
    if total == 1:
        return candidates[0]
    elif total == 0:
        sys.stderr.write("No translation config found for '{}'.\n".format(resource_repo_name))
        return None
    else:
        sys.stderr.write("Too many translation config found for '{}'.\n".format(resource_repo_name))
        return None

def display_python_version():
    sys.stdout.write("'{}'.\n".format(sys.version_info))
    
def _upload_resource(translation_repository, resource_bundle, log_dir):
    success = True
    trans_bundles = []
    for resource in resource_bundle:
        sys.stdout.write("Processing resource '{}'...\n".format(resource.resource_path))

        if not resource.available():
            sys.stdout.write("(Resource not available in local.)\n")
            continue

        if translation_repository.import_resource(resource):
            sys.stdout.write("Uploaded.\n")
        else:
            sys.stdout.write("Failed uploading.\n")
            success = False

    return success

def _upload_translation(resource_repository, resource_bundle, translation_repository, assignee, reviewers, log_dir):
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

    feature_branch_name = resource_repository.import_bundles(trans_bundles)
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

def main(argv):
    upload_destination_string = argv[0]
    config_dir = argv[1]
    config_file_path =  argv[2]
    log_dir = argv[3]

    display_python_version()
    sys.stdout.write("Start processing: '{}'...\n".format(config_file_path))

    resource_config = ResourceConfiguration()
    if not resource_config.parse(config_file_path):
        sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
        sys.exit(1)

    trans_config = _find_translation_config(resource_config.get_repository_name(), config_dir)
    if not trans_config:
        sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
        sys.exit(1)

    if resource_config.get_repository_platform() == 'github':
        try:
            resource_repo = GithubRepository(resource_config, log_dir)
        except ResourceRepositoryInitializationError as e:
            sys.stderr.write("'{}'.\n".format(e))
            sys.exit(1)
        else:
            pass
    elif resource_config.get_repository_platform() == 'bitbucket':
        try:
            resource_repo = BitbucketRepository(resource_config, log_dir)
        except ResourceRepositoryInitializationError as e:
            sys.stderr.write("'{}'.\n".format(e))
            sys.exit(1)
        else:
            pass
    else:
        sys.exit(1)

    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    sys.stdout.write("Number of resources: '{}'.\n".format(num_resources))
    if num_resources == 0:
        sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
        sys.exit(0)

    try:
        trans_repo = TransifexRepository(trans_config, log_dir)
    except TranslationRepositoryInitializationError as e:
        sys.stderr.write("'{}'.\n".format(e))
        sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
        sys.exit(1)
    else:
        pass

    success = False
    if upload_destination_string == 'translation_repository':
        success = _upload_resource(trans_repo, resource_bundle, log_dir)
    elif upload_destination_string == 'resource_repository':
        reviewers = list(set(resource_config.get_pullrequest_reviewers() + trans_config.get_project_reviewers()))
        assignee = resource_config.get_pullrequest_assignee()
        success = _upload_translation(resource_repo, resource_bundle, trans_repo, assignee, reviewers, log_dir)
    else:
        sys.stderr.write("BUG: Unknown upload destination string '{}'\n".format(upload_destination_string))

    sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
    sys.stdout.flush()
    sys.stderr.flush()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])

