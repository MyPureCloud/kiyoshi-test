import os
import re

import logging
logger = logging.getLogger('tpa')

import settings
import creds
from resource import ResourceConfiguration
from translation import TranslationConfiguration
from plugins.bitbucket.repository import BitbucketRepository
from plugins.github.repository import GithubRepository
from plugins.transifex.repository import TransifexRepository
from plugins.crowdin.repository import CrowdinRepository
import plugins.git.commands as git

def get_local_repository_branches(repo_name):
    """ Return list of branches of specified local repository.
        Ruturn None on any errors.
    """
    rootdir = get_local_repository_directory()
    if rootdir == None:
        return None
    else:
        ret = git.get_branch_all(os.path.join(rootdir, repo_name))
        if ret.succeeded:
            regex = re.compile(r'\x1b[^m]*m')
            l = []
            for x in ret.output:
                x = regex.sub('', x) # remove ANSI escape sequence
                x = x.strip().rstrip()
                if not x:
                    continue
                if x.startswith('*'): # remove extra '*' from current branch name
                    x = x[1:].strip().rstrip()
                    l.append(x)
                else:
                    x = x.split('/')[-1] # remove extra path from remote branch name
                    l.append(x)
            return l
        else:
            return None

def get_local_repository_directory():
    """ Return settins.LOCAL_REPO_DIR.
        Ruturn None on any errors.
    """
    if os.path.isdir(settings.LOCAL_REPO_DIR):
        return settings.LOCAL_REPO_DIR
    else:
        logger.error("Local repository directory not found. LOCAL_REPO_DIR: '{}'.".format(settings.LOCAL_REPO_DIR))
        return None

def _create_resource_repository(config, log_dir):
    """ Create exact resource repository (sub class of ResourceRepository) for given
        resource configuration.
        Return None on any errors.
    """
    c = creds.get(config.repository_platform)
    if c:
        if config.repository_platform == 'github':
            return GithubRepository(config, c, log_dir)
        elif config.repository_platform == 'bitbucket':
            return BitbucketRepository(config, c, log_dir)
        else:
            logger.error("Unknown resource platform: '{}'".format(config.repository_platform))
            return None
    else:
        logger.error("Failed to get creds for platform: '{}'".format(config.repository_platform))
        return None

def _create_translation_repository(config, log_dir):
    """ Create exact translation repository (sub class of TranslationRepository) for given
        tranalation configuration.
        Return None on any errors.
    """
    c = creds.get(config.project_platform)
    if c:
        if config.project_platform == 'transifex':
            return TransifexRepository(config, c, log_dir)
        elif config.project_platform == 'crowdin':
            return CrowdinRepository(config, c, log_dir)
        else:
            logger.error("Unknown translation platform: '{}'".format(config.project_platform))
            return None
    else:
        logger.error("Failed to get creds for platform: '{}'".format(config.project_platform))
        return None

def create(config, log_dir):
    """ Return repository based on given configuration. 
        Return None on any errors.
    """
    if type(config) == ResourceConfiguration:
        return _create_resource_repository(config, log_dir)
    elif type(config) == TranslationConfiguration:
        return _create_translation_repository(config, log_dir)
    else:
        logger.error("Unknonw configuration type: '{}'".format(type(config)))
        return None
