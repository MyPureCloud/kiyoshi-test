import os.path

# root directory where tpa script, configuration and log files reside.
TPA_ROOT_DIR = '/Users/kiyoshi.iwase/work/current/tpa-work/tpa-mac-scheduler/'

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
# Job File
#
JOB_FILE = os.path.join(TPA_ROOT_DIR, 'job.json')



#
# Tornado server
#
# tornado server port.
HTTP_PORT='8080'
