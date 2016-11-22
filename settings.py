import os.path

# Root directory where tpa script and configuration files reside.
TPA_ROOT_DIR = '/path/to/tpa/dir'

# Configuration file Directories.
CONFIG_BASE_DIR = os.path.join(TPA_ROOT_DIR, 'config')
CONFIG_RESOURCE_DIR = os.path.join(CONFIG_BASE_DIR, 'resource')
CONFIG_TRANSLATION_DIR = os.path.join(CONFIG_BASE_DIR, 'translation')

# Credential files.
BITBUCKET_CREDS_FILE = os.path.join(TPA_ROOT_DIR, 'bitbucket_creds.json')
GITHUB_CREDS_FILE = os.path.join(TPA_ROOT_DIR, 'github_creds.json')
TRANSIFEX_CREDS_FILE = os.path.join(TPA_ROOT_DIR, 'transifex_creds.json')
CROWDIN_CREDS_FILE = os.path.join(TPA_ROOT_DIR, 'crowdin_creds.json')

# Scheduler project file and job File.
PROJECT_FILE = os.path.join(TPA_ROOT_DIR, 'projects.json')
JOB_FILE = os.path.join(TPA_ROOT_DIR, 'jobs.json')

# Uploader for  scheduler.
SCHEDULER_UPLOADER = os.path.join(TPA_ROOT_DIR, 'translation-process-automation/uploader_cmd.py')

# Local repository directory. All repsitories are cloned in this directory.
LOCAL_REPO_DIR = '/path/to/repo/dir'

# Log directory for uploaders.
LOG_DIR = '/path/to/log/dir'

# Cache Directory.
CACHE_DIR = '/path/to/cache/dir'

#
# Tornado server
#
# tornado server port for scheduler.
HTTP_PORT='8080'

