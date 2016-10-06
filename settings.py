import os.path

# root directory where tpa script, configuration and log files reside.
TPA_ROOT_DIR = '/home/kiyoshi/tpa-testing'

#
# Configuration Directories
#
CONFIG_BASE_DIR = os.path.join(TPA_ROOT_DIR, 'config')
CONFIG_RESOURCE_DIR = os.path.join(CONFIG_BASE_DIR, 'resource')
CONFIG_TRANSLATION_DIR = os.path.join(CONFIG_BASE_DIR, 'translation')

#
# Log Directories
#
LOG_BASE_DIR = os.path.join(TPA_ROOT_DIR, 'logs')
LOG_RU_DIR = os.path.join(LOG_BASE_DIR, 'ru')
LOG_TU_DIR = os.path.join(LOG_BASE_DIR, 'tu')
LOG_AUX_DIR = os.path.join(LOG_BASE_DIR, 'aux')

#
# Cache Directory
#
CACHE_DIR = os.path.join(TPA_ROOT_DIR, 'cache')

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
SCHEDULER_UPLOADER = os.path.join(TPA_ROOT_DIR, 'translation-process-automation/uploader_cmd.py')

#
# Tornado server
#
# tornado server port.
HTTP_PORT='8080'
