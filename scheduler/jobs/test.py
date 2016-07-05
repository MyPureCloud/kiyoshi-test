import os
import job

import settings

class TestJob(job.Job):
    def __init__(self, job_dict):
        super(TestJob, self).__init__(job_dict)

    def run(self, *args, **kwargs):
        print(self.name)

    def update_loginfo(self, loginfo):
        self.loginfo = loginfo

    def get_base_log_dir(self):
        return settings.LOG_AUX_DIR 

    def get_log_dir_name(self):
        return 'testjob'

    def get_exec_status(self):
        return 'NIY-status'

    def get_exec_datetime(self):
        return 'NIY-datetime'

    def get_exec_results(self):
        return 'NIY-results'

