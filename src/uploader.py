import sys, os
from ResourceRepositoryClass import ResourceRepository, ResourceRepositoryInitializationError, Resource, PullRequest
from TranslationRepositoryClass import TranslationRepository, TranslationRepositoryInitializationError, Translation

def _find_translation_config_file(resource_repo_name, config_dir):
    translation_config_dir = os.path.join(config_dir, 'translation')
    if not os.path.isdir(translation_config_dir):
        sys.stderr.write("Translation config directory NOT found: '{}'.\n".format(translation_config_dir))
        return None

    candidates = []
    for filename in os.listdir(translation_config_dir):
        if os.path.splitext(filename)[1] == '.yaml':
            path = os.path.join(translation_config_dir, filename)
            if resource_repo_name in open(path).read():
                candidates.append(path)

    result = None
    total = len(candidates)
    if total == 1:
        sys.stdout.write("Paired configuration: '{}'.\n".format(candidates[0]))
        result = candidates[0]
    elif total == 0:
        sys.stderr.write("Failed pairing configuration. No translation configuration found in: '{}'.\n".format(translation_config_dir))
    else:
        sys.stderr.write("Failed pairing configuration due to multiple configuration found in: '{}'.\n".format(translation_config_dir))
        sys.stderr.write("Duplicates...\n")
        for i in range(0, total):
            sys.stderr.write("- '{}'.\n".format(candidates[i]))
    return result

def _create_resource_repository(config_file_path, log_dir):
    """ terminate script on failure since nothing can do w/o resource repository.
    """
    try:
        repo = ResourceRepository(config_file_path, log_dir)
    except ResourceRepositoryInitializationError as e:
        sys.stderr.write("'{}'.\n".format(e))
        sys.exit(1)
    else:
        return repo

def _create_translation_repository(config_file_path, log_dir):
    repo = None
    try:
        repo = TranslationRepository(config_file_path, log_dir)
    except TranslationRepositoryInitializationError as e:
        sys.stderr.write("'{}'.\n".format(e))
    else:
        pass
    return repo

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

def _upload_translation(resource_repository, resource_bundle, translation_repository, log_dir):
    success = True
    trans_bundles = []
    for resource in resource_bundle:
        sys.stdout.write("Preparing translation candidates for resource: '{}'...\n".format(resource.resource_path))

        if not resource.available():
            sys.stdout.write("Skipped. Resource not available in local.\n")
            continue

        trans_bundle = translation_repository.get_translation_bundle(resource)
        if trans_bundle:
            trans_bundles.append(trans_bundle)
        else:
            sys.stdout.write("Skipped. No translation bundle for this resource.\n")

    feature_branch_name = resource_repository.import_bundles(trans_bundles)
    if feature_branch_name:
        sys.stdout.write("Imports in branch: '{}'.\n".format(feature_branch_name))
        pr = PullRequest()
        pr.branch_name = feature_branch_name
        pr.reviewers = list(set(translation_repository.get_reviewers() + resource_repository.get_reviewers()))
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

    resource_repo = _create_resource_repository(config_file_path, log_dir)
    if not resource_repo:
        sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
        sys.exit(1)

    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    sys.stdout.write("Number of resources: '{}'.\n".format(num_resources))
    if num_resources == 0:
        sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
        sys.exit(0)

    trans_config_path = _find_translation_config_file(resource_repo.get_repository_name(), config_dir)
    if not trans_config_path:
        sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
        sys.exit(1)

    trans_repo = _create_translation_repository(trans_config_path, log_dir)
    if not trans_repo:
        sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
        sys.exit(1)

    success = False
    if upload_destination_string == 'translation_repository':
        success = _upload_resource(trans_repo, resource_bundle, log_dir)
    elif upload_destination_string == 'resource_repository':
        success = _upload_translation(resource_repo, resource_bundle, trans_repo, log_dir)
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

