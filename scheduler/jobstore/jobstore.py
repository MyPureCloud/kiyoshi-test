import os
import sys
import json
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

import settings
from scheduler.jobs.test import TestJob
from scheduler.jobs.resource_uploader import ResourceUploaderJob
from scheduler.jobs.translation_uploader import TranslationUploaderJob 
import scheduler.logstore.logstore as logstore

# Job configuation.
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

def read_job_file(job_status_to_read='all'):
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


def collect_jobs_latest_7(job):
    jobs = []
    logs = logstore.collect_loginfo_latest_7(job)
    for log in logs:
        j = job.duplicate()
        j.update_loginfo(log)
        jobs.append(j)
    return jobs

def _create_job(job_dict):
    job = None
    if job_dict['class'] == 'TestJob':
        job = TestJob(job_dict)
    elif job_dict['class'] == 'ResourceUploaderJob':
        job = ResourceUploaderJob(job_dict)
    elif job_dict['class'] == 'TranslationUploaderJob':
        job = TranslationUploaderJob(job_dict)
    else:
        logger.error("Unknown job class: '{}'.".format(job_dict['class']))

    return job

def _update_job_with_latest_log(job):
    results = logstore.collect_loginfo_latest(job)
    if len(results) == 1:
        job.update_loginfo(results[0])
    else:
        job.update_loginfo(None)

def find_job_by_id(job_id):
    job = None
    with open(settings.JOB_FILE) as fi:
        try:
            job_data = json.load(fi)

            entries = job_data['jobs']
            for entry in entries:
                if not entry['id'] == job_id:
                    continue

                job = _create_job(entry)
                if job:
                    _update_job_with_latest_log(job)

        except ValueError as e:
            logger.error("Failed to load: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return job

    if not job:
        logger.error("Job not found: '{}' in '{}'.".format(job_id, settings.JOB_FILE))

    return job

def read_jobs(job_status_to_read='all'):
    jobs = []
    if not os.path.isfile(settings.JOB_FILE):
        logger.error("Job file not found: {}".format(settings.JOB_FILE))
        return jobs

    with open(settings.JOB_FILE) as fi:
        try:
            job_data = json.load(fi)

            entries = job_data['jobs']
            job = None
            for entry in entries:
                if job_status_to_read == 'all':
                    job = _create_job(entry)
                    if job:
                        _update_job_with_latest_log(job)
                        jobs.append(job)
                else:
                    if job_status_to_read == entry['status']:
                        job = _create_job(entry)
                        if job:
                            _update_job_with_latest_log(job)
                            jobs.append(job)
                    else:
                        pass
        except ValueError as e:
            logger.error("Failed to load: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return jobs

    return jobs

def read_active_jobs():
    return read_jobs(job_status_to_read='active')

def read_suspended_jobs():
    return read_jobs(job_status_to_read='suspended')

