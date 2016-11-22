import os
import sys
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

import settings
import resource
import translation
import job

def to_dict(o):
    if type(o) == ProjectConfiguration:
        return _ProjectConfiguration_to_dict(o)
    elif type(o) == ProjectSummary:
        return _ProjectSummary_to_dict(o)
    elif type(o) == ProjectDetails:
        return _ProjectDetails_to_dict(o)
    elif type(o) == TranslatedResourceStatus:
        return _TranslatedResourceStatus_to_dict(o)
    else:
        logger.error("Unknown object type: '{}', context:'{}'.".format(type(o), o))
        return {}



'''
    Project Configuration

    Represents properties for a project defined in a project configuration file.
'''

# Project configuation.
#
# keys                          values
# ----------------------------------------------------------------------
# status                        Status of a project. 'active' or 'suspended'.
# id                            Project ID string.
# name                          Project name for display purpose.
# description                   One line job description for display purpose.
# job_ids                       List of job id string.
ProjectConfiguration = namedtuple('ProjectConfiguration', 'status, id, name, description, job_ids')

def _ProjectConfiguration_job_ids_to_dict(ids):
    results = []
    for id in ids:
        results.append({'job_id': id})
    return results

def _ProjectConfiguration_to_dict(o):
    return {
            'status': o.status,
            'id': o.id,
            'name': o.name,
            'description': o.description,
            'job_ids': _ProjectConfiguration_job_ids_to_dict(o.job_ids)
            }

def _read_project_file(project_status_to_read='all'):
    """ Return list of ProjectConfiguration tuples by reading defalut project file.
        Return empty list if there is no projects or on any errors.
    """
    if not os.path.isfile(settings.PROJECT_FILE):
        logger.error("Project file not found: '{}'.".format(settings.PROJECT_FILE))
        return []

    with open(settings.PROJECT_FILE) as fi:
        try:
            data = json.load(fi)
        except ValueError as e:
            logger.error("Failed to read project file: '{}', Reason: {}".format(settings.PROJECT_FILE, e))
            return []

        results = []
        for p in data['projects']:
            if project_status_to_read == 'all' or project_status_to_read == p['status']:
                results.append(ProjectConfiguration(p['status'], p['id'], p['name'], p['description'], p['jobs']))
        return results

def _find_project_configuration(project_id):
    if not os.path.isfile(settings.PROJECT_FILE):
        logger.error("Project file not found: '{}'.".format(settings.PROJECT_FILE))
        return None

    with open(settings.PROJECT_FILE) as fi:
        try:
            data = json.load(fi)
        except ValueError as e:
            logger.error("Failed to read project file: '{}', Reason: {}".format(settings.PROJECT_FILE, e))
            return None

        for p in data['projects']:
            if p['id'] == project_id:
                return ProjectConfiguration(p['status'], p['id'], p['name'], p['description'], p['jobs'])

        logger.error("Project configuration not found for id: '{}'.".format(project_id))
        return None

'''
    Project Summary

    Lightweight project information.
'''

# Project Summary.
#
# keys                          values
# ----------------------------------------------------------------------
# status                        Status of a project. 'active' or 'suspended'.
# id                            Project ID string.
# name                          Project name for display purpose.
# description                   One line job description for display purpose.
ProjectSummary = namedtuple('ProjectSummary', 'status, id, name, description')

def _ProjectSummary_to_dict(o):
    return o._asdict()

#def _get_project_summary_all():
#    configs = _read_project_file() 
#    results = []
#    for c in configs:
#        results.append(ProjectSummary(c.status, c.id, c.name, c.description))
#    return results
#
#def _get_project_summary(project_id):
#    configs = _read_project_file() 
#    for c in configs:
#        if c.id == project_id:
#            return ProjectSummary(c.status, c.id, c.name, c.description)
#    else:
#        return {}

def get_summary(**kwargs):
    """
    Return a project summary (ProjectSummary tuple) for specified project id. Or return
    empty dictionary on if the project id does not exist or on any errors.

    Return list of project summary (ProjectSummary tuple) when project id is not specified.
    Or return empty list if there are no projects or on any errors.
    """
    configs = _read_project_file() 
    if 'id' in kwargs:
        for c in configs:
            if c.id == kargs['id']:
                return ProjectSummary(c.status, c.id, c.name, c.description)
        else:
            return {}
    else:
        results = []
        for c in configs:
            results.append(ProjectSummary(c.status, c.id, c.name, c.description))
        return results



'''
    Project Details

    Same as project summary except jobs property which contains job ids for
    the project.
'''

# Project Details.
#
# keys                          values
# ----------------------------------------------------------------------
# status                        Status of a project. 'active' or 'suspended'.
# id                            Project ID string.
# name                          Project name for display purpose.
# description                   One line job description for display purpose.
# jobs                          List of job ids
ProjectDetails = namedtuple('ProjectDetails', 'status, id, name, description, jobs')

def _ProjectDetails_to_dict(o):
    return o._asdict()

def get_details(**kwargs):
    """
    Return list of project details (ProjectDetails tuple). 
    Return empty dictionary on any errors.
    
    OPTIONS:
        'id': Return project details of the specified project id.
    """
    configs = _read_project_file() 
    if 'id' in kwargs:
        for c in configs:
            if c.id == kwargs['id']:
                return ProjectDetails(c.status, c.id, c.name, c.description, c.job_ids)
        else:
            return {}
    else:
        results = []
        for c in configs:
            results.append(ProjectDetails(c.status, c.id, c.name, c.description, c.job_ids))
        return results



'''
    Translation Status

'''

# Language Status
#
# keys                  values
# -----------------------------------
# language_code         Language of the translation.
# completed             True when traslation/review is complted.
LanguageStatus = namedtuple('LanguageStatus', 'language_code, completed')

def _LanguageStatus_to_dict(o):
    return {'language_code': o.language_code, 'completed': o.completed}

# Translation Status
# Translation status (in Translation platform)  for resources.
#
# keys                  values
# -----------------------------------
# platform              Translation platform name.
# path                  Path of the resource
# languages             List of language status (LanguageStatus tuple). 
TranslatedResourceStatus = namedtuple('TranslatedResourceStatus', 'platform, path, languages')

def _TranslatedResourceStatus_to_dict(o):
    languages = []
    for l in o.languages:
        languages.append(_LanguageStatus_to_dict(l))
    return {'platform': o.platform, 'path': o.path, 'languages': languages}

def _is_translation_completed(translation_stats):
    return translation_stats.percentage_reviewed_strings == '100%'

def get_translation_status(project_id):
    """
    Return list of translation status summary (TranslatedResourceStatus tuple) for each resource file.
    """
    c = _find_project_configuration(project_id)
    if not c:
        return None

    for job_id in c.job_ids:
        j = job.get_details(job_id)
        # Currntly, there should be only one RU job in a project, so, just use the first-found RU job.
        if j.class_name == 'ResourceUploaderJob':
            r =  resource.get_configuration(filename=j.resource_config_filename)
            if not r:
                return []

            t =  translation.get_configuration(filename=j.translation_config_filename)
            if not t:
                return []

            results = []
            for res in r.resources:
                entries = translation.get_language_stats(t.project_platform, t.project_name, r.repository_name, res.path)
                if entries:
                    languages = []
                    for entry in entries:
                        languages.append(LanguageStatus(entry.language_code, _is_translation_completed(entry)))
                    results.append(TranslatedResourceStatus(t.project_platform, res.path, languages))
                else:
                    logger.error("No language stats. platform: '{}', project: '{}', repository: '{}', resource: '{}'.".format(t.project_platform, t.project_name, r.repository_name, res.path))
            return results
        else:
            pass

    logger.info("get_translation_status(): No ResourceUploderJob jobs in project: '{}'.".format(project_id))
    return None

