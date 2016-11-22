import os
import sys
import json
import copy
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

import settings
import core.plugins.git.creds as git
import core.plugins.bitbucket.creds as bitbucket
import core.plugins.github.creds as github
import core.plugins.transifex.creds as transifex

def to_dict(o):
    if type(o) == transifex.TransifexCreds:
        return transifex.to_dict(o)
    elif type(o) == git.GitCreds:
        return git.to_dict(o)
    else:
        logger.error("Unknown type: '{}'.".format(type(o)))
        return None

def get(platform_name):
    """
    Return platform specific creds, or None on any errors.
    """
    if platform_name == 'transifex':
        return transifex.get(settings.TRANSIFEX_CREDS_FILE)
    elif platform_name == 'bitbucket':
        return bitbucket.get(settings.BITBUCKET_CREDS_FILE)
    elif platform_name == 'github':
        return github.get(settings.GITHUB_CREDS_FILE)
    else:
        logger.error("Unknown platform: '{}'.".format(platform_name))
        return None

