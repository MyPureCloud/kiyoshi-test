import logging
logger = logging.getLogger('tpa')

import core.plugins.git.creds as git

def to_dict(o):
    if type(o) == get.GitCreds:
        return git.to_dict(o)
    else:
        logger.error("Unknown type: '{}'.".format(type(o)))
        return None

def get(path):
    return git.get(path)

