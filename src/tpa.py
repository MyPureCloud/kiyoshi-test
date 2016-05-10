import sys, os, getopt, datetime
from subprocess import call
from sh import pwd

# Usage is only for display (not for log).
def usage(dest_module):
    dest_module.write("Usage\n")
    dest_module.write("tpa.py --dest=[resource_repository|translaton_repository] --config=<path/to/config/dir> --log=<path/to/log/dir> [OPTION]\n")
    dest_module.write("    --dest=[resource_repository|translation_repository]\n")
    dest_module.write("        specify upload destination.\n")
    dest_module.write("        specify resource_repository to upload translation from translation repository to resource repository.\n")
    dest_module.write("        specify translation_repository: upload resource from resource repository to translation repository.\n")
    dest_module.write("    --config=</path/to/config/dir>\n")
    dest_module.write("        path to config directory which is accessible from this script.\n")
    dest_module.write("        In the config directory, two sub directories 'resource' and 'translation' which\n")
    dest_module.write("        provide configuration files to this script are required.\n")
    dest_module.write("    --log=</path/to/log/dir>\n")
    dest_module.write("        path to log directory which is accessible from this script. All work files and logs are stored\n")
    dest_module.write("        in this directory.\n")
    dest_module.write("    [OPTION]\n")
    dest_module.write("    --exec-only=<config file name>\n")
    dest_module.write("        execute specified config file. the config file has to reside in path specified by --config.\n")

def _process_args(argv, options):
    try:
        opts, args = getopt.getopt(argv, 'h', ['help', 'config=', 'dest=', 'log=', 'exec-only'])
    except getopt.GetoptError:
        usage(sys.stderr)
        sys.stderr.write("Invalid command line option.\n")
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(sys.stdout)
            system.exit(0)
        elif opt == '--config':
            options['config'] = arg
        elif opt == '--dest':
            options['dest'] = arg
        elif opt == '--log':
            options['log'] = arg
        elif opt == '--exec-only':
            options['exec_only'] = arg
        else:
            sys.stderr.write("Unknown option: {}\n".format(opt))
            system.exit(1)

    if not options['dest']:
        sys.stdout.write("--dest option is required in command line arguments.\n")
        usage(sys.stderr)
        sys.exit(1)
    else:
        if not ('resource_repository' == options['dest'] or 'translation_repository' == options['dest']):
            sys.stderr.write("Unknown value for --dest option: {}.\n".format(destination))
            usage(sys.stderr)
            sys.exit(1)

    if not options['config']:
        sys.stdout.write("--config option is required in command line arguments.\n")
        usage(sys.stderr)
        sys.exit(1)
    else:
        if not os.path.isdir(options['config']):
            sys.stderr.write("Config directory not found: '{}'.".format(options['config']))
            usage(sys.stderr)
            sys.exit(1)

def main(argv):

    # FIXME --- it looks that using sh lib gets into os.waitpid() which never come back on python 3.5.  
    #           this can be removed if the issue is no longer seen with Python3.
    if sys.version_info[0:1] == (3,):
        sys.stdout.write("Test is not passed with Python3.")
        sys.exit(1)
    
    params = {'config': None, 'dest': None, 'log': None, 'exec_only': None}
    _process_args(argv, params)
    
    destination = params['dest']
    RESOURCE_CONFIG_DIR_NAME = 'resource'
    config_base_dir = params['config']
    config_dir = os.path.join(config_base_dir, RESOURCE_CONFIG_DIR_NAME)
    if not os.path.isdir(config_dir):
        sys.stderr.write("Config directory not found: '{}'.\n".format(config_dir))
        sys.exit(1)

    config_paths = []
    exec_only_file_name = params['exec_only']
    if exec_only_file_name:
        exec_only_file_path = os.path.isfile(os.path.join(config_dir, exec_only_file_name))
        if os.path.isfile(exec_only_file_path):
            config_path.append(exec_only_file_path)
        else:
            sys.stderr.write("Config file specified by --exec-only not found: '{}'.".format(exec_only_file_name))
            sys.exit(1)
    else:
        for filename in os.listdir(config_dir):
            if os.path.splitext(filename)[1] == '.yaml':
                config_paths.append(filename)

    log_base_dir = params['log']
    if not os.path.isdir(log_base_dir):
        try:
            os.makedirs(log_base_dir)
        except OSError as e:
            sys.stderr.write("Failed to create log directory: '{}'. Reason: '{}'.\n".format(log_base_dir, e))
            sys.exit(1)

    log_sub_dir = os.path.join(log_base_dir, '{}'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
    if not os.path.isdir(log_sub_dir):
        try:
            os.makedirs(log_sub_dir)
        except OSError as e:
            sys.stderr.write("Failed to create log directory: '{}'. Reason: '{}'.\n".format(log_sub_dir, e))
            sys.exit(1)

    success = 0
    for config_path in config_paths:
        log_dir = os.path.join(log_sub_dir, '{}'.format(os.path.splitext(os.path.basename(config_path))[0]))
        if not os.path.isdir(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError as e:
                sys.stderr.write("Failed to create log directory: '{}'. Reason: '{}'.\n".format(log_dir, e))
                continue

        log_path = os.path.join(log_dir, 'tpa.log')
        err_path = os.path.join(log_dir, 'tpa.err')

        uploader_path = os.path.join(os.path.dirname(__file__),  'uploader.py')
        with open(log_path, 'w') as log, open(err_path, 'w') as err:
            if call(['python', uploader_path, destination, config_base_dir, os.path.join(config_dir, config_path), log_dir],  stdout=log, stderr=err) == 0:
                success += 1

        #
        # TEMP --- for test
        print("--- LOG START ---")
        call(['cat', log_path])
        print("--- LOG END ---")
        print("--- ERR START ---")
        call(['cat', err_path])
        print("--- ERR END ---")

    total = len(config_paths)
    sys.stdout.write("Total: '{}' Success: '{}' Failure: '{}'.\n".format(total, success, total - success))
    if total == success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main(sys.argv[1:])

