import os
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

def to_dict(o):
    if type(o) == TransifexCreds:
        return _TransifexCreds_to_dict(o)
    else:
        logger.error("Unknown type: '{}'.".format(type(o)))
        return None

# Transifex Creds
# 
# key           value
# ----------------------------
# username      User name.
# userpasswd    Password for the user.
# useremail     Email address for the user.
# project_slug_prefix   Prefix for project slugs.
# resource_slug_prefix  Prefix for resource slugs.
TransifexCreds = namedtuple('TransifexCreds', 'username, userpasswd, useremail, project_slug_prefix, resource_slug_prefix')

def _TransifexCreds_to_dict(o):
    return {'username': o.username, 'userpasswd': o.userpasswd, 'useremail': o.useremail, 'project_slug_prefix': o.project_slug_prefix, 'resource_slug_prefix': o.resource_slug_prefix}

def _create_TransifexCreds(path):
    if not os.path.isfile(path):
        logger.error("File not found: {}.\n".format(path))
        return None 

    with open(path, 'r') as fi:
        try:
            j = json.load(fi)
            c = TransifexCreds(j['user_name'], j['user_passwd'], j['user_email'], j['project_slug_prefix'], j['resource_slug_prefix'])
        except ValueError as e:
            logger.error("Failed to parse. File: '{}', Reason: '{}'.\n".format(path, str(e)))
            return None
        else:
            return c

def get(path):
    return _create_TransifexCreds(path)

