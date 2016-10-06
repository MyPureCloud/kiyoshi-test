import os

import logging
logger = logging.getLogger(__name__)

import settings

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

def initialize():
    logger.info("Initializing cachestore...")
    if not _setup_dir(settings.CACHE_DIR):
        return False

    # nothing special for now...
    return True

