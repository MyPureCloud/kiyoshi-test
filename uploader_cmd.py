import sys
import os
import json

import tpa.tpa as tpa

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

    if tpa.upload(params):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])

