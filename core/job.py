import os
import json
from collections import namedtuple
import abc
import datetime
from subprocess import call

import logging
logger = logging.getLogger(__name__)

import settings
import resource
import translation

def to_dict(o):
    if type(o) == JobConfiguration:
        return _JobConfiguration_to_dict(o)
    elif type(o) == JobSummary:
        return _JobSummary_to_dict(o)
    elif type(o) == JobDetails:
        return _JobDetails_to_dict(o)
    elif type(o) == JobExecStatus:
        return _JobExecStatus_to_dict(o)
    elif type(o) == JobSyncStatus:
        return _JobSyncStatus_to_dict(o)
    else:
        logger.error("Unknown type: '{}, context: '{}'.".format(type(o), o))
        return {}



'''
        Job Configuration

        Job configuration describes all properties for a job which are defined in a job configuration file.

'''

# JobConfiguation
#
# keys                          values
# ----------------------------------------------------------------------
# status                        Status of a job. 'active' or 'suspended'.
# class_name                    Job class name. e.g. 'ResourceUploaderJob'.
# id                            Job ID.
# name                          Job name for display. e.g. 'RU bitbuckettest'.
# description                   One line job description texst string.
# resource_config_filename      Resource configuration file name.
# translation_config_filename   Translation configuration file name.
# month                         Scheduled month.
# day                           Scheduled day.
# day_of_week                   Scheduled day of week.
# hour                          Scheduled hour.
# minute                        Scheduled minutes.
JobConfiguration = namedtuple('JobConfiguration', 'status, class_name, id, name, description, resource_config_filename, translation_config_filename, month, day, day_of_week, hour, minute')

def _JobConfiguration_to_dict(o):
    return { 
        'status': o.status,                     
        'class_name': o.class_name,                 
        'id': o.id,                         
        'name': o.name,                       
        'description': o.description,                
        'resource_config_filename': o.resource_config_filename,   
        'translation_config_filename': o.translation_config_filename,
        'month': o.month,                      
        'day': o.day,                        
        'day_of_week': o.day_of_week,                
        'hour': o.hour,                       
        'minute': o.minute
        }

def _get_job_configuration(job_status_to_read='all'):
    """ Return list of JobConfiguration tuples by reading defalut job file.
        Return empty list if there is no jobs or on any errors.
    """
    if not os.path.isfile(settings.JOB_FILE):
        logger.error("Job file not found: '{}'.".format(settings.JOB_FILE))
        return []

    results = []
    with open(settings.JOB_FILE) as fi:
        try:
            data = json.load(fi)
            for job in data['jobs']:
                if job_status_to_read == 'all' or job_status_to_read == job['status']:
                    results.append(JobConfiguration(
                        job['status'],
                        job['class'], 
                        job['id'],               
                        job['name'],                        
                        job['description'], 
                        job['resource_config_file'], 
                        job['translation_config_file'],
                        job['month'], 
                        job['day'],
                        job['day_of_week'],
                        job['hour'],
                        job['minute']
                        ))
        except ValueError as e:
            logger.error("Failed to process job file: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return []
    return results

def get_configuration(**kwargs):
    """
    Return list of job configuration (JobConfiguration tuple).
    Return empty list on any errors.

    OPTION:
        'id': Job id to get.
            Note:
            'status' and 'job_class' options cannot be used with 'id' option.
        -----
        'status': Specify job status to get. 'active' or 'suspended'.
        'job_class': Specify job class to get. 'ResourceUploaderJob', 'TranslationUploaderJob' or 'AuxlirayJob'.
            Note:
            'id' cannot be used with 'status' or 'job_class'.
    """
    if 'id' in kwargs:
        return _find_configuration(kwargs['id'])
    else:
        return _get_configuration(**kwargs)

def _get_configuration(**kwargs):
    """
    OPTION:
        'status': Specify job status to get. 'active' or 'suspended'.
        'job_class': Specify job class to get. 'ResourceUploaderJob', 'TranslationUploaderJob' or 'AuxlirayJob'.
    """
    if not os.path.isfile(settings.JOB_FILE):
        logger.error("Job file not found: '{}'.".format(settings.JOB_FILE))
        return []

    results = []
    with open(settings.JOB_FILE) as fi:
        try:
            data = json.load(fi)
        except ValueError as e:
            logger.error("Failed to process job file: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return []
        else:
            for job in data['jobs']:
                if 'status' in kwargs:
                    if job['status'] != kwargs['status']:
                        continue
                if 'job_class' in kwargs:
                    if job['class'] != kwargs['job_class']:
                        continue
                    
                results.append(JobConfiguration(
                                job['status'],
                                job['class'], 
                                job['id'],               
                                job['name'],                        
                                job['description'], 
                                job['resource_config_file'], 
                                job['translation_config_file'],
                                job['month'], 
                                job['day'],
                                job['day_of_week'],
                                job['hour'],
                                job['minute']
                                ))
            return results

def _get_translation_uploader_job_configuration(job_status_to_read='all'):
    if not os.path.isfile(settings.JOB_FILE):
        logger.error("Job file not found: '{}'.".format(settings.JOB_FILE))
        return []

    results = []
    with open(settings.JOB_FILE) as fi:
        try:
            data = json.load(fi)
            for job in data['jobs']:
                if job_status_to_read == 'all' or job_status_to_read == job['status']:
                    if not job['class'] == 'TranslationUploaderJob':
                        continue
                    
                    results.append(JobConfiguration(
                        job['status'],
                        job['class'], 
                        job['id'],               
                        job['name'],                        
                        job['description'], 
                        job['resource_config_file'], 
                        job['translation_config_file'],
                        job['month'], 
                        job['day'],
                        job['day_of_week'],
                        job['hour'],
                        job['minute']
                        ))
        except ValueError as e:
            logger.error("Failed to process job file: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return []
    return results

def _find_configuration(job_id):
    """ 
    Return job configuration (JobConfiguration tuple) which matches given job id.
    Return None, otherwise.
    """
    if not os.path.isfile(settings.JOB_FILE):
        logger.error("Job file not found: '{}'.".format(settings.JOB_FILE))
        return None

    with open(settings.JOB_FILE) as fi:
        try:
            data = json.load(fi)
        except ValueError as e:
            logger.error("Failed to process job file: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return None
        else:
            for job in data['jobs']:
                if job['id'] != job_id:
                    continue
                    
                return JobConfiguration(
                        job['status'],
                        job['class'], 
                        job['id'],               
                        job['name'],                        
                        job['description'], 
                        job['resource_config_file'], 
                        job['translation_config_file'],
                        job['month'], 
                        job['day'],
                        job['day_of_week'],
                        job['hour'],
                        job['minute']
                        )
            else:
                logger.error("Failed to find job configuration for job id: '{}'.".format(job_id))
                return None

def find_paired_translation_uploader_job(resource_job_id):
    """
    Return 'paired' translation uploader job id for specified resource uploader job id.
    Return None when no such paird translation uploader job, or on any errors.
    """
    r = _find_configuration(resource_job_id)
    if not r:
        return None
    
    # Resource uploader and Translation Uploader are paired if they use identical resource and translation
    # configuration files.
    configurations = _get_configuration(job_class='TranslationUploaderJob')
    for c in configurations:
        if c.resource_config_filename == r.resource_config_filename and c.translation_config_filename == r.translation_config_filename:
            return c.id
    else:
        logger.error("Failed to find paired translation job configuration for resource job id: '{}'.".format(resource_job_id))
        return None



'''
    Job Summary

    This is lightweight information for a job.
'''

# Job Summary.
#
# keys                          values
# ----------------------------------------------------------------------
# status                        Status of a job. 'active' or 'suspended'.
# class_name                    Job class name. e.g. 'ResourceUploaderJob'.
# id                            Job ID.
# name                          Job name for display. e.g. 'RU bitbuckettest'.
# description                   One line job description texst string.
JobSummary = namedtuple("JobSummary", "status, class_name, id, name, description")

def _JobSummary_to_dict(o):
    return {
        'status': o.status,
        'class_name': o.class_name,
        'id': o.id,
        'name': o.name,
        'description': o.description,
        }

def get_summary(**kwargs):
    """
    Return job summary.

    OPTION
    ------
    job_id:         Specify job id to get summary of.
    """
    if 'job_id' in kwargs:
        c = _find_configuration(kwargs['job_id'])
        if c:
            return JobSummary(c.status, c.class_name, c.id, c.name, c.description)
        else:
            return None
    else:
        results = []
        cs = get_configuration()
        for c in cs:
            results.append(JobSummary(c.status, c.class_name, c.id, c.name, c.description))
        return results

'''
    Job Details

    Describes a job in detail.

    Job schedule is described as a string instead of separate date/time entries (e.g. month, day, hour...).
'''

# Job Details.
#
# keys                          values
# ----------------------------------------------------------------------
# status                        Status of a job. 'active' or 'suspended'.
# class_name                    Job class name. e.g. 'ResourceUploaderJob'.
# id                            Job ID.
# name                          Job name for display. e.g. 'RU bitbuckettest'.
# description                   One line job description texst string.
# resource_config_filename      Resource configuration file name.
# translation_config_filename   Translation configuration file name.
# job_cron_string               Job schedule as a cron string. 
JobDetails = namedtuple("JobDetails", "status, class_name, id, name, description, resource_config_filename, translation_config_filename, job_cron_string")

def _JobDetails_to_dict(o):
    return {
        'status': o.status,
        'class_name': o.class_name,
        'id': o.id,
        'name': o.name,
        'description': o.description,
        'resource_config_filename': o.resource_config_filename,
        'translation_config_filename': o.translation_config_filename,
        'job_cron_string': o.job_cron_string
        }

def get_details(job_id):
    """
    Return details for a job. 
    """
    c = get_configuration(id=job_id)
    if not c:
        logger.error("Failed to find job congifuration for job details. id: '{}'.".format(job_id))
        return None

    job_cron_string = "{} {} {} {} {}".format(c.month, c.day, c.day_of_week, c.hour, c.minute)
    return JobDetails(c.status, c.class_name, c.id, c.name, c.description, c.resource_config_filename, c.translation_config_filename, job_cron_string)



'''
    Job Sync Status

    Job Sync Status is obtained via resource/translation platform. 
    For resource repository, sync is a pull request submitted by TPA.
    For translation repository, sync is a occurrence of resource uploading.
'''
# Job sync status
#
# keys                          values
# ----------------------------------------------------------------------
# job_id                        Job ID string.
# job_class                     Job class string.
# date                          Date of sync occurred.
# sync_id                       Id which can identify the sync in platform.
# sync_url                      URL to platfrom where it shows sync results.
# sync_state                    State of sync.
JobSyncStatus = namedtuple('JobSyncStatus', 'job_id, job_class, date, sync_id, sync_url, sync_state')

def _JobSyncStatus_to_dict(o):
    return {'job_id': o.job_id, 'job_class': o.job_class, 'date': o.date, 'sync_id': o.sync_id, 'sync_url': o.sync_url, 'sync_state': o.sync_state}

def _get_latest_resource_sync_date(translation_platform, project_name, resource_repository_name, resource_paths):
    INITIAL_VALUE = '0000'
    results = INITIAL_VALUE
    for resource_path in resource_paths:
        stats  = translation.get_master_language_stats(platform=translation_platform, project_name=project_name, resource_repository_name=resource_repository_name, resource_path=resource_path)
        if stats:
            if stats.last_updated >= results:
                results = stats.last_updated
        else:
            logger.error("Failed to get resource details for platform: '{}', project: '{}', repository: '{}', resource: '{}'.".format(
                    translation_platform, project_name, resource_repository_name, resource_path))

    if results == INITIAL_VALUE:
        return None 
    else:
        # no sync information to add for now
        return results

def get_sync_status(**kwargs):
    """
        OPTION:
            - For any job, specify the job id.
                job_id:             Job id.

            - For resource uploader job, sync status is status of uploading resource files to
              Translation platform. Following optinos are mandatory.
                job_id                      Job id.
                job_class                   Job class strng ('ResourceUploaderJob').
                translation_platform:       Translation platform name.
                translation_project_name:   Translation project name.
                resource_repository_name:   Resource repository name.
                resources:                  List of resource path in the repository.

            - For translation uploader job, sync status is status of a PR which is the latest PR
              submitted by the job. Following options are mandatory.
                job_id                      Job id.
                job_class                   Job class strng ('TranslationUploaderJob').
                resource_platform:          Resource platform name.
                repository_owner:           Repository owner.
                repository_name:            Repository name.
    """
    if (kwargs['job_class'] == 'ResourceUploaderJob'):
        sync_date =  _get_latest_resource_sync_date(kwargs['translation_platform'], kwargs['translation_project_name'], kwargs['resource_repository_name'], kwargs['resources'])
        if sync_date:
            return JobSyncStatus(kwargs['job_id'], kwargs['job_class'], sync_date, None, None, None)
        else:
            return JobSyncStatus(kwargs['job_id'], kwargs['job_class'], 'N/A', None, None, None)
    elif (kwargs['job_class'] == 'TranslationUploaderJob'):
        pr_summary = resource.query_pullrequest(platform=kwargs['resource_platform'], repository_owner=kwargs['repository_owner'], repository_name=kwargs['repository_name'], limit=1)
        if pr_summary:
            return JobSyncStatus(kwargs['job_id'], kwargs['job_class'], pr_summary[0].date, pr_summary[0].number, pr_summary[0].url, pr_summary[0].state)
        else:
            return JobSyncStatus(kwargs['job_id'], kwargs['job_class'], 'N/A', None, None, None)
    if 'job_id' in kwargs:
        logger.error("get_sync_status(): NIY: 'job_id'.")
        return None 
    else:
        logger.error("Unknown combinatin of kwargs")
        return None

def execute(job_configuration):
    """ Execute a job. """
    if job_configuration.class_name == 'ResourceUploaderJob':
        destination = 'translation_repository'
    elif job_configuration.class_name == 'TranslationUploaderJob':
        destination = 'resource_repository'
    elif job_configuration.class_name == 'AuxiliaryJob':
        destination = None
    else:
        destination = None
    
    logger.info("Executing job. id: '{}' ('{}')".format(job_configuration.id, job_configuration.class_name))
    log_dir = create_log_dir(job_configuration.id)
    if log_dir:
        logger.info("Log dir: '{}'".format(log_dir))
    else: 
        logger.error("Aborted. Failed to create log dir: '{}".format(log_dir)) 
        return
    log_path = os.path.join(log_dir, 'tpa.log')
    err_path = os.path.join(log_dir, 'tpa.err')
    uploader_path = settings.SCHEDULER_UPLOADER
    resource_config_path = os.path.join(settings.CONFIG_RESOURCE_DIR, job_configuration.resource_config_filename)
    translation_config_path = os.path.join(settings.CONFIG_TRANSLATION_DIR, job_configuration.translation_config_filename)
    options = ''

    with open(log_path, 'w') as log, open(err_path, 'w') as err:
        if call(['python', uploader_path, destination, resource_config_path, translation_config_path, log_dir, options], stdout=log, stderr=err) == 0:
            logger.info("Job command succeeded. id: '{}' ('{}')\n".format(job_configuration.id, job_configuration.class_name))
        else:
            logger.error("Job command failed. id: '{}' ('{}')\n".format(job_configuration.id, job_configuration.class_name))

'''
    About Log

    Log directory structure
   
        settings.LOG_DIR/<execution datetime>/<job id>/

        e.g.
        settings.LOG_DIR = ~/my/logs
        execution datetime = 2016-06-06_14-17-30
        job id = ru-kiyoshiiwase-githubtest-1234
        log name = tpa.log
        ~/my/logs/2016-06-06_14-17-30/ru-kiyoshiiwase-githubtest-1234/tpa.log


        @@@  change ????

        tpa.log ---> log.txt ???
        tpa.err ---> err.txt ???

        add exec.json ??? for job exec summary in json ???
'''

def _setup_dir(path):
    if os.path.isdir(path):
        return True
    else:
        try:
            os.makedirs(path)
        except OSError as e:
            logger.error("Failed to create directory: '{}'. Reason: {}".format(path, e))
            return False
        else:
            if os.path.isdir(path):
                return True
            else:
                logger.error("Created directory does not exist: '{}'.".format(path))
                return False

def create_log_dir(job_id):
    """ Create a log directory for a job.
        Return path to the directory, or None on any errors.
    """
    base_dir = os.path.join(settings.LOG_DIR, '{}'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
    if _setup_dir(base_dir):
        sub_dir = os.path.join(base_dir, job_id)
        if _setup_dir(sub_dir):
            return sub_dir
        else:
            return None
    else:
        return None



'''
    Job Execution Status

    Job Execution Status is for *system maintaineers* and is compilation of log context produced by a TPA job.

'''
# Job excecution status
#
# keys                          values
# ----------------------------------------------------------------------
# job_id                        Job ID string.
# date                          Job execution date.
# status                        'SUCCESS', FAILURE' or 'UNKNOWN'.                        
#                               'SUCCESS' in only when all ExecStats in the execution log succeeded without any errors. 
# message                       Short display string to express results of execution.. e.g. url to a PR, error message, etc
# log_path                      Path to log file for the execution.
# err_path                      Path to error file for the execution.
JobExecStatus = namedtuple('JobExecStatus', 'job_id, date, status, message, log_path, err_path')

def _JobExecStatus_to_dict(o):
    return {'job_id': o.job_id, 'date': o.date, 'status': o.status, 'message': o.message, 'log_path': o.log_path, 'err_path': o.err_path}

def _collect_execstats(log_path):
    results = []
    if os.path.isfile(log_path):
        with open(log_path) as fi:
            lines = fi.readlines()
            for l in lines:
                if l.startswith('ExecStats='):
                    results.append(l[len("'ExecStats='") - 1:len(l) - 2])
    return results

def _conclude_exec_stats(execstats):
    """ Conclude if the job execution is success or not. """
    succeeded = 0
    failed = 0
    unknown = 0
    for x in execstats:
        try:
            d = json.loads(x)
        except ValueError as e:
            logger.error("Failed to load exec stats as json. Reason: '{}', execstats: '{}'.".format(e, x))
            continue
        else:
            if d['operation'] == 'ResourceUpload':
                if d['results'] ==  'SUCCESS':
                    succeeded += 1
                elif d['results'] ==  'FAILURE':
                    failed += 1
                else:
                    unknown += 1
            elif d['operation'] == 'TranslationUpload':
                if d['results'] ==  'SUCCESS':
                    succeeded += 1
                elif d['results'] ==  'FAILURE':
                    failed += 1 
                else:
                    unknown += 1
            else:
                logger.error("Unknown operation: '{}'. execstats: '{}'.".format(d['operation'], x))
                unknown += 1

    if failed >= 1:
        return "FAILURE - S:{} F:{} U:{}".format(succeeded, failed, unknown)
    else:
        if succeeded >= 1:
            if unknown == 0:
                return "SUCCESS - S:{} F:{} U:{}".format(succeeded, failed, unknown)
            else:
                return "CHECK LOG - S:{} F:{} U:{}".format(succeeded, failed, unknown)
        else:
            return "CHECK LOG - S:{} F:{} U:{}".format(succeeded, failed, unknown)

def _withdraw_exec_message(execstats):
    """ Constracut meaningful message out of exec stats. """
    job_type = None
    succeeded = 0
    failed = 0
    unknown = 0
    tu_message = None
    for x in execstats:
        try:
            d = json.loads(x)
        except ValueError as e:
            logger.error("Failed to load exec stats as json. Reason: '{}', execstats: '{}'.".format(e, x))
            continue
        else:
            if d['operation'] == 'ResourceUpload':
                job_type = 'RU'
                if d['results'] ==  'SUCCESS':
                    succeeded += 1
                    #if d['new_strings'] == '0' and d['del_strings'] == '0' and d['mod_strings'] == '0':
                elif d['results'] ==  'FAILURE':
                    failed += 1
                else:
                    unknown += 1
            elif d['operation'] == 'TranslationUpload':
                job_type = 'TU'
                if d['results'] ==  'SUCCESS':
                    succeeded += 1
                    url = d['pullrequest_url']
                    if url:
                        tu_message =  "<a href='{}'>Pull Request</a>".format(url)
                    else:
                        tu_message = d['reason']
                elif d['results'] ==  'FAILURE':
                    failed += 1
                    tu_message = d['reason']
                else:
                    unknown += 1
            else:
                logger.error("Unknown operation: '{}'. execstats: '{}'.".format(d['operation'], x))
                unknown += 1
   
    if job_type == 'RU':
        if succeeded == 0:
            return "No uplodads - S:{} F:{} U:{}".format(succeeded, failed, unknown)
        else:
            return "Uplodaded resource(s) - S:{} F:{} U:{}".format(succeeded, failed, unknown)
    elif job_type == 'TU':
        if not tu_message:
            return "CHECK LOG for exec stats."
        else:
            return tu_message
    else:
        return "CHECK LOG - Failed to analyze job and operation."

def _analyze_logs(log_path, err_path):
    """ Conclude execution status by analyzing two logs. """
    if log_path: 
        execstats = _collect_execstats(log_path)
        return {'status': _conclude_exec_stats(execstats), 'message': _withdraw_exec_message(execstats)}
    else:
        if err_path:
            return {'status': 'FAILURE', 'message': "Only err.log exists."}
        else:
            return {'status': 'UNKNOWN', 'message': "No logs found."}
            
def get_execution_status(job_id, limit=1):
    """ Collect log exection status for a job by going through all logs for the job. """
    results = []
    count = 0
    for x in sorted(os.listdir(settings.LOG_DIR), reverse=True): # directory x should be named after datetime. e.g. '2016-06-06_14-17-30'
        if count >= limit:
            break
        for y in sorted(os.listdir(os.path.join(settings.LOG_DIR, x))): # directory y is named after job id.
            if y and (y == job_id):
                log_path = None
                err_path = None
                current_dir = os.path.join(settings.LOG_DIR, x, y)
                for f in os.listdir(current_dir):
                    if f == 'tpa.log':
                        path = os.path.join(current_dir, f)
                        if os.path.getsize(path) >= 1:
                            log_path = path
                    elif f == 'tpa.err':
                        path = os.path.join(current_dir, f)
                        if os.path.getsize(path) >= 1:
                            err_path = path
                else:
                    pass # ignore other files.
                if count < limit:
                    d = _analyze_logs(log_path, err_path)
                    results.append(JobExecStatus(job_id, x, d['status'], d['message'], log_path, err_path))
                    count += 1
                else:
                    break 
    return results

def get_resource_slugs(translation_platform, translation_project_name, resource_repository_name, resources):
    """ Return list of {<resource path>: <resource slug>} dictionary. The resource slug is generated
        by the given parameters.
        This will not query translation repository to obtain existing resource slugs.
    """
    return translation.get_resource_slugs(translation_platform, translation_project_name, resource_repository_name, resources)

def get_translation_slugs(translation_platform, translation_project_name):
    """ Return list of {<slug>: <name of the slug>} dictionary by querying
        specified translation project.
    """
    return translation.get_translation_resource_slugs(translation_platform, translation_project_name)

