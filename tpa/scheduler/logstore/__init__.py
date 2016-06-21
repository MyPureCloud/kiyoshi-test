""" file system based log store
"""

import os, sys
import logging

import tpa.settings as settings

logger = logging.getLogger(__name__)

_errors = 0

logger.info("Initializing logstore...")

def _ensure_dir(path):
    if os.path.isdir(path):
        return True
    else:
        logger.error("Directory does not exist: '{}'.".format(path))
        return False

def _setup_dir(path):
    if os.path.isdir(path):
        return True
    else:
        try:
            os.makedirs(path)
        except OSError as e:
            logger.error("Failed to create directory: '{}'. Reason: {}".format(path, e))
            return False
        else:
            if os.path.isdir(path):
                return True
            else:
                logger.error("Created directory does not exist: '{}'.".format(path))
                return False


if not _ensure_dir(settings.CONFIG_BASE_DIR):
    sys.exit(1)
if not _ensure_dir(settings.CONFIG_RESOURCE_DIR):
    sys.exit(1)
if not _ensure_dir(settings.CONFIG_TRANSLATION_DIR):
    sys.exit(1)

if not _setup_dir(settings.LOG_BASE_DIR):
    sys.exit(1)
if not _setup_dir(settings.LOG_RU_DIR):
    sys.exit(1)
if not _setup_dir(settings.LOG_TU_DIR):
    sys.exit(1)
if not _setup_dir(settings.LOG_AUX_DIR):
    sys.exit(1)

