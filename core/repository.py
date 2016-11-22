import sys
import os
import abc
from shutil import copyfile

import creds
from resource import ResourceConfiguration
from translation import TranslationConfiguration
from plugins.bitbucket.repository import BitbucketRepository
from plugins.github.repository import GithubRepository
from plugins.transifex.repository import TransifexRepository

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
            logger.error("NIY: create_translation_repository() for crowdin.")
            return None
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
