import os
import job

import tpa.settings as settings

class TestJob(job.Job):
    def __init__(self, job_dict):
        super(TestJob, self).__init__(job_dict)

    def run(self, *args, **kwargs):
        print(self.name)

    def get_base_log_dir(self):
        return settings.LOG_AUX_DIR 

    def get_log_dir_name(self):
        return 'testjob'
