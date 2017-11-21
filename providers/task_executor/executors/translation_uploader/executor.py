import os
import json
import hashlib
import difflib
from tempfile import mkdtemp
from shutil import rmtree
import datetime

from ....common.common import FatalError
from ....common.common import GET
from ....common.common import TpaLogger 
from ....common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR, response_ACCEPTED
from ..helper import get_config_context, list_files, list_files_in_open_pullrequest, get_translation_status, download_file_from_resource_repository, download_file_from_translation_platform_by_id, upload_context_to_resource_repository
from . import settings

def _in_open_pullrequest(d, kafka):
    if y['in_open_pullrequest'] == True:
        y['status'] = 'success'
        y['results'] = 'Skipped (in open pull request).'
        with TpaLogger(**kafka) as o:
            o.info("In open pull request: '{}'".format(y['path']))
        return True
    else:
        return False

def _review_completed(d, kafka):
    if d['reviewed_percentage'] == '100%':
        return True
    else:
        d['status'] = 'success'
        d['results'] = 'Skipped (review not completed).'
        with TpaLogger(**kafka) as o:
            o.info("Review not completed: '{}'".format(d['path']))
        return False

def _update_resource_repository(request_id, candidates, branch_name, kafka):
    # Download tranaltion file, which is 100% completed, one by one from translation platform repository.
    # Then update local repository with them. Return list of updated files actually.
    for x in candidates['files']:
        with TpaLogger(**kafka) as o:
            o.info("Start updating process for resource: '{}/{}'".format(candidates['resource_repository_name'], x['resource_path']))
        for y in x['translations']:
            if not _review_completed(y, kafka):
                continue
            if _in_open_pullrequest(y, kafka):
                continue

            # Download translation file from resource repository.
            try:
                tempdir = mkdtemp()
                orig  = os.path.join(tempdir, 'file.orig')
                download_file_from_resource_repository(request_id, candidates['resource_platform'], candidates['resource_repository_name'], y['path'], orig)
            except FatalError as e:
                rmtree(tempdir)
                y['status'] = 'failure'
                y['results'] = "{}".format(str(e))
                with TpaLogger(**kafka) as o:
                    o.error("Skipped due to error (w/ orig translation file): '{}' {}".format(y['path'], str(e)))
                continue

            # download transltion file from translation repository.
            try:
                latest  = os.path.join(tempdir, 'file.latest')
                download_file_from_translation_platform_by_id(request_id, candidates['translation_platform'], candidates['translation_project_slug'], x['translation_resource_slug'], y['lang'], latest)
            except FatalError as e:
                rmtree(tempdir)
                y['status'] = 'failure'
                y['results'] = "{}".format(str(e))
                with TpaLogger(**kafka) as o:
                    o.error("Skipped due to error (w/ latest translation file): '{}/{} ({})' {}".format(x['translation_resource_slug'], y['lang'], y['path'], str(e)))
                continue

            # if files are different, set diff string to y['results'], otherwise 'identical'.
            try:
                with open(orig, 'r') as f1, open(latest, 'r', encoding='utf-8') as f2:
                    diff = difflib.unified_diff(f1.readlines(), f2.readlines())

                # @@@ TEST
                diff_text = ""
                minus = 0
                plus = 0
                with TpaLogger(**kafka) as o:
                    o.info("-------- starting diff --------\n")
                    for line in diff:
                        diff_text += line
                        o.info("{}".format(line))
                        if line.startswith('- '):
                            minus += 1
                        elif line.startswith('+ '):
                            plus += 1
                        else:
                            pass
                    o.info("minus: {}".format(minus))
                    o.info("plus: {}".format(plus))
                    o.info("-------- ending diff --------\n")

            except OSError as e:
                rmtree(tempdir)
                y['status'] = 'failure'
                y['results'] = "{}".format(str(e))
                with TpaLogger(**kafka) as o:
                    o.error("Skipped due to error (w/ diff): '{}/{} ({})' {}".format(x['translation_resource_slug'], y['lang'], y['path'], str(e)))
                continue

            # upload the file on resource repository, if there are differences.
            if minus >= 1 or plus >= 1:
                with open(latest, 'r', encoding='utf-8') as f:
                    context = f.read() 
                try:
                    upload_context_to_resource_repository(request_id, candidates['resource_platform'], candidates['resource_repository_name'], y['path'], context)
                    y['status'] = 'success'
                    y['results'] = diff_text
                    with TpaLogger(**kafka) as o:
                        o.info("Updated: '{}/{} ({})'".format(x['translation_resource_slug'], y['lang'], y['path']))
                except FatalError as e:
                    y['status'] = 'failure'
                    y['results'] = r['message']
                    with TpaLogger(**kafka) as o:
                        o.error("Failed to update: '{}/{} ({})' {}".format(x['translation_resource_slug'], y['lang'], y['path'], str(e)))
            else:
                y['status'] = 'success'
                y['results'] = ''
                with TpaLogger(**kafka) as o:
                    o.info("Not updated (no diffs): '{}/{} ({})'".format(x['translation_resource_slug'], y['lang'], y['path']))

            rmtree(tempdir)
    return candidates

def _submit_pull_request():
    return ''

def _list_uplodable_files(request_id, uploader_config_path, kafka):
    """ Create list of uplodadable translation files, with necessary information for uploading files, such as
        about resource platform, translation platform, if translation file is compltely reviewed and if the
        translation file is in open pull requests.
    """
    try:
        files = list_files(request_id, uploader_config_path, kafka)
        in_open_pr = list_files_in_open_pullrequest(request_id, uploader_config_path, kafka)
        for x in files['files']:
            for y in x['translations']:
                r = get_translation_status(request_id, files['translation_platform'], files['translation_project_slug'], x['translation_resource_slug'], y['lang'], kafka)
                with TpaLogger(**kafka) as o: # Log all translation stats in case of investigaton.
                    o.info("{}".format(r))
                y['reviewed_percentage'] = r[y['lang']]['reviewed_percentage']

                for z in in_open_pr:
                    if y['path'] in z:
                        y['in_open_pullrequest'] = True
                        break
                else:
                    y['in_open_pullrequest'] = False
                with TpaLogger(**kafka) as o:
                    o.info("Path: '{}', In open PR: {} ".format(y['path'], y['in_open_pullrequest']))
        return files
    except FatalError as e:
        return response_INTERNAL_SERVER_ERROR(request_id, "Failed to list uploadable translation files. {}".format(str(e)), kafka)

def execute(request_id, uploader_config_path, kafka, **kwargs):
    """
    No kwargs used.
    """
    candidates = _list_uplodable_files(request_id, uploader_config_path, kafka)
    with TpaLogger(**kafka) as o:
        o.info("{}".format(candidates))
    if candidates == None:
        return response_INTERNAL_SERVER_ERROR(request_id, "Failed to create list of translation file candidates.", kafka)
    if len(candidates) == 0:
        return response_ACCEPTED(request_id, "No resource file has uploadable translation files.")

    branch_name = 'TPA_{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    updates = _update_resource_repository(request_id, candidates, branch_name, kafka)
    # @@@ TEST
    return response_OK(request_id, "Executed", candidates, kafka)

    results = submit_pull_request() # request_id, branch, updates 
    return response_OK(request_id, "Executed", results, kafka)

def get_executor(request_id, **kwargs):
    kafka = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port'],
        'topic': settings.kafka['topic'],
        'key': 'default'}

    # nothing special for now
    initialized = True

    def _executor(request_id, config_path, **kwargs):
        if initialized:
            return execute(request_id, config_path, kafka, **kwargs)
        else:
            msg = "REQ[{}] {} is not operational due to initialization error.".format(request_id, settings.identity['name'])
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    return _executor

    
