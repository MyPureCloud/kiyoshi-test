import os, sys
import json
import logging
import tpa.settings as settings
from tpa.scheduler.jobs.test import TestJob
from tpa.scheduler.jobs.resource_uploader import ResourceUploaderJob
from tpa.scheduler.jobs.translation_uploader import TranslationUploaderJob 
import tpa.scheduler.logstore.utils as logstore

logger = logging.getLogger(__name__)

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

def _update_job_with_latest_exec_status(job):
    results = logstore.collect_loginfo_latest(job)
    if len(results) == 1:
        job.last_exec_status = results[0].status
        job.last_exec_datetime = results[0].datetime
    else:
        job.last_exec_status = 'n/a'
        job.last_exec_datetime = 'n/a'

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
                    _update_job_with_latest_exec_status(job)

        except ValueError as e:
            logger.error("Failed to load: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return job

    if not job:
        logger.error("Job not found: '{}' in '{}'.".format(job_id, settings.JBO_FILE))

    return job

def read_jobs():
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
                job = _create_job(entry)
                if job:
                    _update_job_with_latest_exec_status(job)
                    jobs.append(job)

        except ValueError as e:
            logger.error("Failed to load: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return jobs

    return jobs

