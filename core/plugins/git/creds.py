import os
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

def to_dict(o):
    if type(o) == GitCreds:
        return _GitCreds_to_dict(o)
    else:
        logger.error("Unknown type: '{}'.".format(type(o)))
        return None

# Git Creds
# 
# key           value
# ----------------------------
# username      User name.
# userpasswd    Password.
# useremail     Email address for the user.
# userfullname  Full name of the user.
GitCreds = namedtuple('GitCreds', 'username, userpasswd, useremail, userfullname')

def _GitCreds_to_dict(o):
    return {'username': o.username, 'userpasswd': o.userpasswd, 'useremail': o.useremail, 'userfullname': o.userfullname}

def _create_GitCreds(path):
    if not os.path.isfile(path):
        logger.error("File not found: {}.\n".format(path))
        return None 

    with open(path, 'r') as fi:
        try:
            j = json.load(fi)
            c = GitCreds(j['user_name'], j['user_passwd'], j['user_email'], j['user_fullname'])
        except ValueError as e:
            logger.error("Failed to parse. File: '{}', Reason: '{}'.\n".format(path, str(e)))
            return None
        else:
            return c

def get(path):
    return _create_GitCreds(path)

