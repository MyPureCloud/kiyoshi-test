import sys, os
import json

import util.tpa_utils as utils

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

    params = {'upload_destination_string': argv[0], 'resource_config_file': argv[1], 'translation_config_file': argv[2], 'log_dir': argv[3]}

    # 5th arg: string for optional parameters. Format is  option1:option2.  Or empty string when no options.
    #   ALL_LANG_PER_RESOURCE: Submit a PR for a resoruce when all languages are completed.
    #   ANY_LANG_PER_RESOURCE: Submit a PR for a resource for completed languages.
    if argv[4] == 'ALL_LANG_PER_RESOURCE':
        params['all_lang_per_resource'] = True
    elif argv[4] == 'ANY_LANG_PER_RESOURCE':
        params['all_lang_per_resource'] = False
    else:
        if argv[4] == '':
            pass
        else:
            sys.stderr.write("Ignored unknown option string: '{}'.\n".format(argv[4]))
        params['all_lang_per_resource'] = False

    return params 

def main(argv):
    params = _check_args(argv)
    if not params:
        sys.exit(1)

    options = {}
    options['all_lang_per_resource'] = params['all_lang_per_resource']
    if utils.upload(params, options):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])

