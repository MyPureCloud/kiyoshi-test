import os
import sys
import json

import settings
import core.job as job
import core.resource as resource
import core.translation as translation
import core.repository as repository

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
        if not resource.available():
            sys.stdout.write("No resource available in local: '{}'\n".format(resource.resource_path))
            continue

        trans_bundle = translation_repository.get_translation_bundle(resource.repository_name, resource.resource_path, resource.resource_translations)
        if trans_bundle:
            trans_bundles.append(trans_bundle)
        else:
            sys.stdout.write("No translation bundle created for resource: '{}'.\n".format(resource.resource_path))

    feature_branch_name = resource_repository.import_bundles(trans_bundles)
    if feature_branch_name:
        sys.stdout.write("Created branch for changes: '{}'.\n".format(feature_branch_name))
        additional_reviewers = trans_config.project_reviewers
        results = resource_repository.submit_pullrequest(feature_branch_name, additional_reviewers)
        return results.errors == 0
    else:
        sys.stdout.write("No branch created for changes.\n")
        return True

def _upload(params):
    sys.stdout.write("Start processing: '{}'...\n".format(params['resource_config_file']))

    resource_config = resource.get_configuration(filename=params['resource_config_file'])
    if resource_config == None:    
        sys.stderr.write("Failed to get configuration from: '{}'.".format(params['resource_config_file']))
        sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
        return False

    trans_config = translation.get_configuration(filename=params['translation_config_file'])
    if trans_config == None:    
        sys.stderr.write("Failed to get configuration from: '{}'.".format(params['translation_config_file']))
        sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
        return False

    resource_repo = repository.create(resource_config, params['log_dir'])
    if resource_repo == None:    
        sys.stderr.write("Failed to create resource repository for: '{}'.".format(params['resource_config_file']))
        sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
        return False

    trans_repo = repository.create(trans_config, params['log_dir'])
    if trans_repo == None:    
        sys.stderr.write("Failed to create translation repository for: '{}'.".format(params['translation_config_file']))
        sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
        return False

    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    if num_resources == 0:
        sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
        return True

    success = False
    if params['upload_destination_string'] == 'translation_repository':
        success = upload_resource(trans_repo, resource_bundle, params['log_dir'])
    elif params['upload_destination_string'] == 'resource_repository':
        success = upload_translation(resource_repo, resource_bundle, trans_repo, params['log_dir'], trans_config)
    else:
        sys.stdout.write("Unknown upload destination: '{}'.\n".format(params['upload_destination_string']))

    sys.stdout.write("End processing: '{}'.\n".format(params['resource_config_file']))
    sys.stdout.flush()
    sys.stderr.flush()
    return success

def _check_args(argv):
    # 1st arg: upload destination string.
    if not (argv[0] == 'resource_repository' or argv[0] == 'translation_repository'):
        sys.stderr.write("Unknown upload destination string: '{}'.\n".format(argv[0]))
        return None

    # 2nd arg: path to resource configuration file.
    if not os.path.isfile(argv[1]):
        sys.stderr.write("Resource configuration file not found: '{}'.\n".format(argv[1]))
        return None

    # 3rd arg: path to resource configuration file.
    if not os.path.isfile(argv[2]):
        sys.stderr.write("Translation configuration file not found: '{}'.\n".format(argv[2]))
        return None

    # 4th arg: path to (existing) log directory.
    if not os.path.isdir(argv[3]):
        sys.stderr.write("Log directory not found: '{}'.\n".format(argv[3]))
        return None

    return {'upload_destination_string': argv[0], 'resource_config_file': argv[1], 'translation_config_file': argv[2], 'log_dir': argv[3]}

def main(argv):
    params = _check_args(argv)
    if not params:
        sys.exit(1)

    if _upload(params):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])


