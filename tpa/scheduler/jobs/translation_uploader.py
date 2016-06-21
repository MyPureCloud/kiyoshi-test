import os, sys
from subprocess import call
import logging

import tpa.settings as settings
import tpa.scheduler.logstore.utils as logstore
from tpa.scheduler.jobs import job

logger = logging.getLogger(__name__)

class TranslationUploaderJob(job.Job):
    def __init__(self, job_dict):
        super(ResourceUploaderJob, self).__init__(job_dict)
        self.resource_config_filename = job_dict['resource_config_file']
        self.translation_config_filename = job_dict['translation_config_file']

        try:
            self.pullrequest_url = job_dict['pullrequest_url']
        except KeyError as e:
            self.pullrequest_url = None

    def run(self, *args, **kwargs):
        logger.info("Executing job: class='TranslationUploaderJob' name='{}' id='{}'".format(self.name, self.jid))
        destination = 'resource_repository'
        log_dir = logstore.create_log_dir(self)
        logger.info("Log dir: '{}'".format(log_dir))
        if not log_dir:
            return
        log_path = os.path.join(log_dir, 'tpa.log')
        err_path = os.path.join(log_dir, 'tpa.err')
        uploader_path = os.path.join(settings.CORE_DIR,  'uploader.py')

        with open(log_path, 'w') as log, open(err_path, 'w') as err:
            if call(['python', uploader_path, destination, settings.CONFIG_BASE_DIR, os.path.join(settings.CONFIG_RESOURCE_DIR, self.resource_config_filename), log_dir],  stdout=log, stderr=err) == 0:
                logger.info("Job status: Sucess: class='TranslationUploaderJob' name='{}' id='{}'\n".format(self.name, self.jid))
            else:
                logger.error("Job status: Fail: class='TranslationUploaderJob' name='{}' id='{}'\n".format(self.name, self.jid))

    def get_base_log_dir(self):
        return settings.LOG_TU_DIR 

    def get_log_dir_name(self):
        return os.path.splitext(os.path.basename(self.resource_config_filename))[0]

