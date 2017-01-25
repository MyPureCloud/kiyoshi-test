import os
import sys
import json
import codecs

import logging
logger = logging.getLogger('tpa')

import api

def _split_path(path):
    d, f = os.path.split(path)
    if d == '' and f == '':
        return
    elif d == '' and f != '':
        if f == '.':
            return []
        else:
            return [f]
    elif d != '' and f == '':
        if d == os.pathsep:
            return []
        else:
            return [d]
    elif d != '' and f != '':
        return _split_path(d) + [f]

def all_strings_approved(api_key, project_slug, branch_name, crowdin_resource_path, language_code):
    """
    Return True when specified resource is translated into language and all strings are approved.
    Return False when approval is not completed or on any errors.
    """
    stats = get_language_stats(api_key, project_slug, language_code)

    # crowdin has to be configured with branch.
    for x in stats['files']:  
        if x['node_type'] == 'branch' and x['name'] == branch_name:
            sub = x
            break
        else:
            pass
    else:
        logger.error("Branch not found in language stats. Branch: '{}', Stats: '{}'.".format(branch_name, stats))
        return False

    splits = _split_path(crowdin_resource_path)
    for i in range(0, len(splits) - 1):
        for x in sub['files']:
            if x['node_type'] == 'directory' and x['name'] == splits[i]:
                sub = x
                break
        else:
            logger.error("Directory not found in language stats. Directory: '{}', Stats: '{}'.".format(splits[i], x))
            return False

    for x in sub['files']:  
        if x['node_type'] == 'file' and x['name'] == splits[-1]:
            if x['phrases'] == x['approved']:
                logger.info("String review completed. Branch: '{}', File: '{}', Language: '{}'.".format(branch_name, crowdin_resource_path, language_code))
                return True
            else:
                logger.info("String review not completed. Branch: '{}', File: '{}', Language: '{}'.".format(branch_name, crowdin_resource_path, language_code))
                return False
    else:
        logger.error("File not found in language stats. File: '{}', Stats: '{}'.".format(splits[-1], sub))
        return False


def get_language_stats(api_key, project_slug, language_code):
    params = {'language': language_code, 'json': True}
    ret = api.get_language_stats(api_key, project_slug, params)
    if ret.succeeded:
        d = ret.response.json()
        d['project_slug'] = project_slug 
        d['language_code'] = language_code
        logger.info('LanguageStats=' + json.dumps(d))
        return ret.response.json() # ensure it is in json....
    else:
        logger.error("Failed to get language status. Project: '{}', Language: '{}, Reason: '{}'.".format(project_slug, language_code, ret.message))
        return None

def update_file(api_key, project_slug, branch_name, crowdin_resource_path, local_file_path):
    """
    Upload a file.
    Rturn True on success. False otherwise.
    """
    payload = {'branch': branch_name, 'json': True}
    with open(local_file_path, 'r') as fi:
        ret = api.update_file(api_key, project_slug, {'files[{}]'.format(crowdin_resource_path): fi}, payload)
        if ret.succeeded:
            return True
        else:
            logger.error("Failed to upload file. Destination: '{}', Local: '{}', Reason: '{}'.".format(crowdin_resource_path, local_file_path, ret.message))
            return False

def export_file(api_key, project_slug, branch_name, crowdin_translation_path, language_code, destination_path):
    """
    Export a file to specified destination path.
    Return the destination path on success.
    Return None on any errors.
    """
    # crowdin file path starts with a directory of branch name.
    path = os.path.join(branch_name, crowdin_translation_path)
    params = {'file': path, 'language': language_code, 'json': True}
    ret = api.export_file(api_key, project_slug, params)
    if ret.succeeded:
        if sys.version_info[0:1] == (2,):
            with codecs.open(destination_path, 'w', encoding='utf-8') as fo:
                fo.write(ret.response.text)
        else:
            with open(destination_path, 'w') as fo:
                fo.write(ret.response.text)
        logger.info("Exported file. File: '{}' as '{}', Language: '{}'.".format(path, destination_path, language_code))
        return destination_path
    else:
        logger.error("Failed to export file. File: '{}', Language: '{}', Message: '{}'".format(os.path.join(branch_name, crowdin_translation_path), language_code, ret.message))
        return None

