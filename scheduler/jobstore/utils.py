import os, sys
import json
import logging

import settings
from scheduler.jobs.test import TestJob
from scheduler.jobs.resource_uploader import ResourceUploaderJob
from scheduler.jobs.translation_uploader import TranslationUploaderJob 
import scheduler.logstore.utils as logstore

logger = logging.getLogger(__name__)

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
                    _update_job_with_latest_log(job)
                    jobs.append(job)

        except ValueError as e:
            logger.error("Failed to load: '{}', Reason: {}".format(settings.JOB_FILE, e))
            return jobs

    return jobs

