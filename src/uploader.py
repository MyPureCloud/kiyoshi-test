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

def main(argv):
    upload_destination_string = argv[0]
    config_dir = argv[1]
    config_file_path =  argv[2]
    log_dir = argv[3]

    if upload_destination_string == 'translation_repository':
        _upload_resource(config_dir, config_file_path, log_dir)
    elif upload_destination_string == 'resource_repository':
        _upload_translation(config_dir, config_file_path, log_dir)
    else:
        sys.stderr.write("BUG: Unknown upload destination string '{}'\n".format(upload_destination_string))
    
def _upload_resource(config_dir, config_file_path, log_dir):
    success = False
    display_python_version()
    sys.stdout.write("Start processing: '{}'...\n".format(config_file_path))
    resource_repo = _create_resource_repository(config_file_path, log_dir)
    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    sys.stdout.write("Number of resources: '{}'.\n".format(num_resources))
    trans_config_path = _find_translation_config_file(resource_repo.get_repository_name(), config_dir)
    trans_repo = _create_translation_repository(trans_config_path, log_dir)

    success = True
    trans_bundles = []
    for resource in resource_bundle:
        sys.stdout.write("Processing resource '{}'...\n".format(resource.resource_path))

        if not resource.available():
            sys.stdout.write("(Resource not available in local.)\n")
            continue

        if trans_repo.import_resource(resource):
            sys.stdout.write("Uploaded.\n")
        else:
            sys.stdout.write("Failed uploading.\n")
            success = False

    sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
    sys.stdout.flush()
    sys.stderr.flush()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)

def _upload_translation(config_dir, config_file_path, log_dir):
    success = False
    display_python_version()
    sys.stdout.write("Start processing: '{}'...\n".format(config_file_path))
    resource_repo = _create_resource_repository(config_file_path, log_dir)
    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    sys.stdout.write("Number of resources: '{}'.\n".format(num_resources))
    trans_config_path = _find_translation_config_file(resource_repo.get_repository_name(), config_dir)
    trans_repo = _create_translation_repository(trans_config_path, log_dir)

    success = True
    trans_bundles = []
    for resource in resource_bundle:
        sys.stdout.write("Processing resource '{}'...\n".format(resource.resource_path))

        if not resource.available():
            sys.stdout.write("(Resource not available in local.)\n")
            continue

        trans_bundle = trans_repo.get_translation_bundle(resource)
        if trans_bundle:
            trans_bundles.append(trans_bundle)
        else:
            sys.stdout.write("(No translation bundle for this resource.)\n")

    total_imports = resource_repo.add_import_entry(trans_bundles)
    sys.stdout.write("Number of import candidates: '{}'.\n".format(total_imports))
        
    if total_imports >= 1:
        feature_branch_name = resource_repo.import_bundles(trans_bundles)
        if feature_branch_name:
            pr = PullRequest()
            pr.branch_name = feature_branch_name
            pr.reviewers = list(set(trans_repo.get_reviewers() + resource_repo.get_reviewers()))
            resource_repo.submit_pullrequest(pr)
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
            sys.stdout.write("(No pull request submitted.\n")

    sys.stdout.write("End processing: '{}'.\n".format(config_file_path))
    sys.stdout.flush()
    sys.stderr.flush()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)

def mainORIG(argv):
    upload_destination_string = argv[0]
    config_dir = argv[1]
    config_file_path =  argv[2]
    log_dir = argv[3]

    success = False
    display_python_version()
    sys.stdout.write("Start processing: '{}'...\n".format(config_file_path))
    resource_repo = _create_resource_repository(config_file_path, log_dir)
    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    sys.stdout.write("Number of resources: '{}'.\n".format(num_resources))
    trans_config_path = _find_translation_config_file(resource_repo.get_repository_name(), config_dir)
    trans_repo = _create_translation_repository(trans_config_path, log_dir)

    success = True
    trans_bundles = []
    for resource in resource_bundle:
        sys.stdout.write("Processing resource '{}'...\n".format(resource.resource_path))

        if not resource.available():
            sys.stdout.write("(Resource not available in local.)\n")
            continue

        if upload_destination_string == 'translation_repository':
            if trans_repo.import_resource(resource):
                sys.stdout.write("Uploaded.\n")
            else:
                sys.stdout.write("Failed uploading.\n")
                success = False
        elif upload_destination_string == 'resource_repository':
            trans_bundle = trans_repo.get_translation_bundle(resource)
            if trans_bundle:
                trans_bundles.append(trans_bundle)
            else:
                sys.stdout.write("(No translation bundle for this resource.)\n")
        else:
            sys.stderr.write("BUG: Unknown upload destination string '{}'\n".format(upload_destination_string))

    if upload_destination_string == 'translation_repository':
        pass 
    elif upload_destination_string == 'resource_repository':
        total_imports = resource_repo.add_import_entry(trans_bundles)
        sys.stdout.write("Number of import candidates: '{}'.\n".format(total_imports))
        
        if total_imports >= 1:
            feature_branch_name = resource_repo.import_bundles(trans_bundles)
            if feature_branch_name:
                pr = PullRequest()
                pr.branch_name = feature_branch_name
                pr.reviewers = list(set(trans_repo.get_reviewers() + resource_repo.get_reviewers()))
                resource_repo.submit_pullrequest(pr)
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
                sys.stdout.write("(No pull request submitted.\n")
        else:
            sys.stdout.write("(No pull request submitted.\n")
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

