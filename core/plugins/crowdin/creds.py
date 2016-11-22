import os
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

def to_dict(o):
    if type(o) == CrowdinCreds:
        return _CrowdinCreds_to_dict(o)
    else:
        logger.error("Unknown type: '{}'.".format(type(o)))
        return None

# Crowdin Creds
# 
# key                   value
# ------------------------------------------------------------------------
# username              User name.
# userpasswd            Password for the user.
# useremail             Email address for the user.
# project_slug_prefix   Prefix for project slugs.
# resource_slug_prefix  Prefix for resource slugs.
# project_keys          List of dictionaries where key is project name and value is the project key.
CrowdinCreds = namedtuple('TransifexCreds', 'username, userpasswd, useremail, project_slug_prefix, resource_slug_prefix', 'project_keys')

def _CrowdinCreds_to_dict(o):
    return {'username': o.username, 'userpasswd': o.userpasswd, 'useremail': o.useremail, 'project_slug_prefix': o.project_slug_prefix, 'resource_slug_prefix': o.resource_slug_prefix, 'project_keys': o.project_keys_asdict()}

def create_CrowdinCreds(path):
    if not os.path.isfile(path):
        logger.error("File not found: {}.\n".format(path))
        return None 

    with open(path, 'r') as fi:
        try:
            j = json.load(fi)
            pkeys = []
            for x in j['project_keys']:
                for k,v in x.items():
                    pkeys.append({k: v})
            c = CrowdinCreds(j['user_name'], j['user_passwd'], j['user_email'], j['project_slug_prefix'], j['resource_slug_prefix'], pkeys)
        except ValueError as e:
            logger.error("Failed to parse. File: '{}', Reason: '{}'.\n".format(path, str(e)))
            return None
        else:
            return c

def get(path):
    return _create_CrowdinCreds(path)

