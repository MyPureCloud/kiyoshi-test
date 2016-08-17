import os, sys
import json
from subprocess import call
import logging

import settings
import scheduler.logstore.logstore as logstore
from scheduler.jobs import job

logger = logging.getLogger(__name__)

class TranslationUploaderJob(job.Job):
    def __init__(self, job_dict):
        super(TranslationUploaderJob, self).__init__(job_dict)
        self.resource_config_filename = job_dict['resource_config_file']
        self.translation_config_filename = job_dict['translation_config_file']
        self.execstats = []

        try:
            self.pullrequest_url = job_dict['pullrequest_url']
        except KeyError as e:
            self.pullrequest_url = None

    def run(self, **kwargs):
        logger.info("Executing job: class='TranslationUploaderJob' name='{}' id='{}'".format(self.name, self.id))
        destination = 'resource_repository'
        log_dir = logstore.create_log_dir(self)
        logger.info("Log dir: '{}'".format(log_dir))
        if not log_dir:
            return
        log_path = os.path.join(log_dir, 'tpa.log')
        err_path = os.path.join(log_dir, 'tpa.err')
        resource_config_path = os.path.join(settings.CONFIG_RESOURCE_DIR, self.resource_config_filename)
        translation_config_path = os.path.join(settings.CONFIG_TRANSLATION_DIR, self.translation_config_filename)
        uploader_path = settings.SCHEDULER_UPLOADER

        options = 'ANY_LANG_PER_RESOURCE'
        if 'all_lang_per_resource' in kwargs:
            if kwargs['all_lang_per_resource']:
                options = 'ALL_LANG_PER_RESOURCE'
            else:
                pass 
        else:
            if settings.SUBMIT_PULLREQUEST_WHEN_ALL_LANGUAGES_COMPLETED_FOR_RESOURCE:
                options = 'ALL_LANG_PER_RESOURCE'
            else:
                pass 

        with open(log_path, 'w') as log, open(err_path, 'w') as err:
            if call(['python', uploader_path, destination, resource_config_path, translation_config_path, log_dir, options],  stdout=log, stderr=err) == 0:
                logger.info("Job status: Sucess: class='TranslationUploaderJob' name='{}' id='{}'\n".format(self.name, self.id))
            else:
                logger.error("Job status: Fail: class='TranslationUploaderJob' name='{}' id='{}'\n".format(self.name, self.id))

    def duplicate(self):
        attr = super(TranslationUploaderJob, self).get_attributes()
        attr['resource_config_file'] = self.resource_config_filename
        attr['translation_config_file'] = self.translation_config_filename
        return TranslationUploaderJob(attr)

    def get_base_log_dir(self):
        return settings.LOG_TU_DIR 

    def get_log_dir(self):
        return self.loginfo.log_dir

    def get_log_dir_name(self):
        return os.path.splitext(os.path.basename(self.resource_config_filename))[0]

    def _update_execstats(self):
        if self.loginfo:
            if os.path.isfile(self.loginfo.log_path):
                with open(self.loginfo.log_path) as fi:
                    lines = fi.readlines()
                    for line in lines:
                        if line.startswith('ExecStats='):
                            self.execstats.append(line[len("'ExecStats='") - 1:len(line) - 2])
        else:
            pass

    def update_loginfo(self, loginfo):
        self.loginfo = loginfo
        self._update_execstats()

    def get_exec_datetime(self):
        if not self.loginfo:
            return 'n/a'
        # temp
        return self.loginfo.datetime.replace('_', ' ') 

    def get_exec_status(self):
        for line in self.execstats:
            try:
                d = json.loads(line)
                if d['operation'] == 'TranslationUpload' and d['results'] ==  'SUCCESS':
                    return 'SUCCESS'
                elif d['operation'] == 'TranslationUpload' and d['results'] ==  'FAILURE':
                    return 'FAILURE'
                else:
                    pass
            except ValueError as e:
                pass
        return 'n/a'

    def get_exec_result_string(self):
        for line in self.execstats:
            try:
                d = json.loads(line)
                if d['operation'] == 'TranslationUpload' and d['results'] ==  'SUCCESS':
                    url = d['pullrequest_url']
                    if url:
                        return "<a href='{}'>Pull Request</a>".format(url)
                    else:
                        return d['reason']
                elif d['operation'] == 'TranslationUpload' and d['results'] ==  'FAILURE':
                    reason = d['reason']
                else:
                    pass
            except ValueError as e:
                pass
        return "n/a"

