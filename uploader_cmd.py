import os
import sys
import json

import logging
logger = None

import settings
import core.job as job
import core.resource as resource
import core.translation as translation
import core.repository as repository

def upload_resource(translation_repository, resource_bundle, log_dir):
    success = True
    trans_bundles = []
    for resource in resource_bundle:
        logger.info("Processing resource '{}'...".format(resource.resource_path))

        if not resource.available():
            d = {
                'operation': "ResourceUpload",
                'results': "FAILURE",
                'reason': "Resource not available in local repository.",
                'resource_full_path': os.path.join(resource.repository_name, resource.resource_path)
                }
            logger.info("ExecStats='{}'".format(json.dumps(d)))
            continue

        if not translation_repository.import_resource(resource):
            success = False

    return success

def upload_translation(resource_repository, resource_bundle, translation_repository, log_dir, trans_config):
    trans_bundles = []
    for resource in resource_bundle:
        if not resource.available():
            logger.info("No resource available in local: '{}'".format(resource.resource_path))
            continue

        trans_bundle = translation_repository.get_translation_bundle(resource.repository_name, resource.resource_path, resource.resource_translations)
        if trans_bundle:
            trans_bundles.append(trans_bundle)
        else:
            logger.info("No translation bundle created for resource: '{}'.".format(resource.resource_path))

    feature_branch_name = resource_repository.import_bundles(trans_bundles)
    if feature_branch_name:
        logger.info("Created branch for changes: '{}'.".format(feature_branch_name))
        additional_reviewers = trans_config.project_reviewers
        results = resource_repository.submit_pullrequest(feature_branch_name, additional_reviewers)
        return results.errors == 0
    else:
        logger.info("No branch created for changes.")
        return True

def _upload(params):
    logger.info("Start processing: '{}'...".format(params['resource_config_file']))

    resource_config = resource.get_configuration(filename=params['resource_config_file'])
    if resource_config == None:    
        logger.error("Failed to get configuration from: '{}'.".format(params['resource_config_file']))
        logger.info("End processing: '{}'.".format(params['resource_config_file']))
        return False

    trans_config = translation.get_configuration(filename=params['translation_config_file'])
    if trans_config == None:    
        logger.error("Failed to get configuration from: '{}'.".format(params['translation_config_file']))
        logger.info("End processing: '{}'.".format(params['resource_config_file']))
        return False

    resource_repo = repository.create(resource_config, params['log_dir'])
    if resource_repo == None:    
        logger.error("Failed to create resource repository for: '{}'.".format(params['resource_config_file']))
        logger.info("End processing: '{}'.".format(params['resource_config_file']))
        return False

    trans_repo = repository.create(trans_config, params['log_dir'])
    if trans_repo == None:    
        logger.error("Failed to create translation repository for: '{}'.".format(params['translation_config_file']))
        logger.info("End processing: '{}'.".format(params['resource_config_file']))
        return False

    resource_bundle = resource_repo.get_resource_bundle()
    num_resources = len(resource_bundle)
    if num_resources == 0:
        logger.info("End processing: '{}'.".format(params['resource_config_file']))
        return True

    success = False
    if params['upload_destination_string'] == 'translation_repository':
        success = upload_resource(trans_repo, resource_bundle, params['log_dir'])
    elif params['upload_destination_string'] == 'resource_repository':
        success = upload_translation(resource_repo, resource_bundle, trans_repo, params['log_dir'], trans_config)
    else:
        logger.info("Unknown upload destination: '{}'.".format(params['upload_destination_string']))

    logger.info("End processing: '{}'.".format(params['resource_config_file']))
    return success

def _check_args(argv):
    # 1st arg: upload destination string.
    if not (argv[0] == 'resource_repository' or argv[0] == 'translation_repository'):
        logger.error("Unknown upload destination string: '{}'.".format(argv[0]))
        return None

    # 2nd arg: path to resource configuration file.
    if not os.path.isfile(argv[1]):
        logger.error("Resource configuration file not found: '{}'.".format(argv[1]))
        return None

    # 3rd arg: path to resource configuration file.
    if not os.path.isfile(argv[2]):
        logger.error("Translation configuration file not found: '{}'.".format(argv[2]))
        return None

    # 4th arg: path to (existing) log directory.
    if not os.path.isdir(argv[3]):
        logger.error("Log directory not found: '{}'.".format(argv[3]))
        return None

    return {'upload_destination_string': argv[0], 'resource_config_file': argv[1], 'translation_config_file': argv[2], 'log_dir': argv[3]}

class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.INFO

class ErrorFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno == logging.ERROR

def _setup_logger():
    global logger
    logger = logging.getLogger('tpa')
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter('[%(levelname)s  %(asctime)s  %(module)s:%(funcName)s:%(lineno)d] %(message)s')

    # Send info messages to stdout
    h1 = logging.StreamHandler(sys.stdout)
    h1.setLevel(logging.INFO)
    h1.setFormatter(fmt)
    h1.addFilter(InfoFilter())
    logger.addHandler(h1)
    
    # Send error messages to stderr.
    h2 = logging.StreamHandler(sys.stderr)
    h2.setLevel(logging.ERROR)
    h2.setFormatter(fmt)
    h2.addFilter(ErrorFilter())
    logger.addHandler(h2)

def main(argv):
    _setup_logger()
    params = _check_args(argv)
    if not params:
        logging.shutdown()
        sys.exit(1)

    if _upload(params):
        logging.shutdown()
        sys.exit(0)
    else:
        logging.shutdown()
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])

