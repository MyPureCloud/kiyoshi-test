import os, sys
import json
from subprocess import call
import logging

import settings
import scheduler.logstore.utils as logstore
from scheduler.jobs import job

logger = logging.getLogger(__name__)

class ResourceUploaderJob(job.Job):
    def __init__(self, job_dict):
        super(ResourceUploaderJob, self).__init__(job_dict)
        self.resource_config_filename = job_dict['resource_config_file']
        self.translation_config_filename = job_dict['translation_config_file']
        self.execstats = []

    def run(self, **kwargs):
        logger.info("Executing job: class='ResourceUploaderJob' name='{}' id='{}'".format(self.name, self.id))
        destination = 'translation_repository'
        log_dir = logstore.create_log_dir(self)
        logger.info("Log dir: '{}'".format(log_dir))
        if not log_dir:
            return
        log_path = os.path.join(log_dir, 'tpa.log')
        err_path = os.path.join(log_dir, 'tpa.err')
        uploader_path = settings.SCHEDULER_UPLOADER
        resource_config_path = os.path.join(settings.CONFIG_RESOURCE_DIR, self.resource_config_filename)
        translation_config_path = os.path.join(settings.CONFIG_TRANSLATION_DIR, self.translation_config_filename)

        options = ''

        with open(log_path, 'w') as log, open(err_path, 'w') as err:
            if call(['python', uploader_path, destination, resource_config_path, translation_config_path, log_dir, options],  stdout=log, stderr=err) == 0:
                logger.info("Job status: Sucess: class='ResourceUploaderJob' name='{}' id='{}'\n".format(self.name, self.id))
            else:
                logger.error("Job status: Fail: class='ResourceUploaderJob' name='{}' id='{}'\n".format(self.name, self.id))

    def duplicate(self):
        attr = super(ResourceUploaderJob, self).get_attributes()
        attr['resource_config_file'] = self.resource_config_filename
        attr['translation_config_file'] = self.translation_config_filename
        return ResourceUploaderJob(attr)

    def _update_execstats(self):
        self.execstats = []
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

    def get_base_log_dir(self):
        return settings.LOG_RU_DIR 

    def get_log_dir(self):
        return self.loginfo.log_dir

    def get_log_dir_name(self):
        return os.path.splitext(os.path.basename(self.resource_config_filename))[0]

    def get_exec_datetime(self):
        if not self.loginfo:
            return 'n/a'
        # temp
        return self.loginfo.datetime.replace('_', ' ') 

    def get_exec_status(self):
        for line in self.execstats:
            try:
                d = json.loads(line)
                if d['operation'] == 'ResourceUpload' and d['results'] ==  'SUCCESS':
                    return 'SUCCESS'
                elif d['operation'] == 'ResourceUpload' and d['results'] ==  'FAILURE':
                    return 'FAILURE'
                else:
                    pass
            except ValueError as e:
                pass
        return 'n/a'

    def get_exec_result_string(self):
        changed = 0
        as_is = 0
        failed = 0
        others = 0
        for line in self.execstats:
            try:
                d = json.loads(line)
                if d['operation'] == 'ResourceUpload' and d['results'] ==  'SUCCESS':
                    if d['new_strings'] == '0' and d['del_strings'] == '0' and d['mod_strings'] == '0':
                        as_is += 1
                    else:
                        #results.append('+{} -{} @{}: {}'.format(d['new_strings'], d['del_strings'], d['mod_strings'], d['resource_full_path']))
                        changed += 1
                elif d['operation'] == 'ResourceUpload' and d['results'] ==  'FAILURE':
                    #results.append('FAILURE: {}'.format(d['resource_full_path']))
                    failed += 1
                else:
                    #results.append('{}: {}'.format(d['results'], d['resource_full_path']))
                    others += 1
            except ValueError as e:
                pass
        if changed ==1:
            return 'Uploaded a resource.'
        elif changed >=2:
            return 'Uploaded resources.'
        else:
            return ''

