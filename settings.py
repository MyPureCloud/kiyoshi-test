import os.path

# root directory where tpa script, configuration and log files reside.
TPA_ROOT_DIR = '/home/kiyoshi/tpa-testing---scheduler'

# tpa core scrpt directory.
CORE_DIR = os.path.join(TPA_ROOT_DIR, 'translation-process-automation/tpa/core')



#
# Configuration Directories
#
CONFIG_BASE_DIR = os.path.join(TPA_ROOT_DIR, 'config')

# configuration directory for resource configuration files.
CONFIG_RESOURCE_DIR = os.path.join(CONFIG_BASE_DIR, 'resource')

# configuration directroy for translation configuration files.
CONFIG_TRANSLATION_DIR = os.path.join(CONFIG_BASE_DIR, 'translation')



#
# Log Directories
#
LOG_BASE_DIR = os.path.join(TPA_ROOT_DIR, 'logs')

# log directory for Resource Uploader.
LOG_RU_DIR = os.path.join(LOG_BASE_DIR, 'ru')

# log directory for Translation Uploader.
LOG_TU_DIR = os.path.join(LOG_BASE_DIR, 'tu')

# log directory for auxiliary jobs.
LOG_AUX_DIR = os.path.join(LOG_BASE_DIR, 'aux')



#
# Credential files
#
BITBUCKET_CREDS_FILE = os.path.join(TPA_ROOT_DIR, 'bitbucket_creds.yaml')
GITHUB_CREDS_FILE = os.path.join(TPA_ROOT_DIR, 'github_creds.yaml')
TRANSIFEX_CREDS_FILE = os.path.join(TPA_ROOT_DIR, 'transifex_creds.yaml')
CROWDIN_CREDS_FILE = os.path.join(TPA_ROOT_DIR, 'crowdin_creds.yaml')



#
# Scheduler job File
#
JOB_FILE = os.path.join(TPA_ROOT_DIR, 'jobs.json')



# Uploader for  scheduler.
SCHEDULER_UPLOADER = os.path.join(TPA_ROOT_DIR, 'translation-process-automation/scheduler_uploader.py')


#
# Tornado server
#
# tornado server port.
HTTP_PORT='8080'
