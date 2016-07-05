import os, sys, datetime
import json
import logging
import settings

logger = logging.getLogger(__name__)


class LogInfo:
    def __init__(self):
        self.datetime = None
        self.config_name = None
        self.log_dir = None
        self.log_path = None
        self.log_size = -1
        self.err_path = None
        self.err_size = -1

def create_log_dir(job):
    if job.class_name == 'ResourceUploaderJob':
        base_log_dir= settings.LOG_RU_DIR
    elif job.class_name == 'TranslationUploaderJob':
        base_log_dir= settings.LOG_TU_DIR
    else:
        base_log_dir= settings.LOG_AUX_DIR
    return _create_log_dir(base_log_dir, job.get_log_dir_name())

def _create_log_dir(base_log_dir, log_dir_name):
    """ create a log directory for a job.
        log directory structure is very specific as shown below.
        
        e.g.
        logs/ru/2016-06-06_14-17-30/kiyoshiiwase-githubtest
        
            logs/ru                     base logdir which is defined in settings.
                                        logs/ru is for resource uploader job.
                                        logs/tu is for translation uploader job.
                                        logs/aux is any other jobs.
        
            2016-06-06_14-17-30     date time of the job is executed.
            
            kiyoshiiwase-githubtest     log directory name.
                                        for resource/translation uploader jobs,
                                        this is resource config file name.
    """

    dir1 = os.path.join(base_log_dir, '{}'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
    if not os.path.isdir(dir1):
        try:
            os.makedirs(dir1)
        except OSError as e:
            sys.stderr.write("Failed to create log directory: '{}'. Reason: '{}'.\n".format(dir1, e))
            return None

    dir2 = os.path.join(dir1, log_dir_name)
    if not os.path.isdir(dir2):
        try:
            os.makedirs(dir2)
        except OSError as e:
            sys.stderr.write("Failed to create log directory: '{}'. Reason: '{}'.\n".format(dir2, e))
            return None

    if os.path.isdir(dir2):
        return dir2
    else:
        sys.stderr.write("Log directory not found: '{}'.\n".format(dir2))
        return None

def collect_loginfo_all_ru():
    return _collect_loginfo(settings.LOG_RU_DIR, 100)

def collect_loginfo_all_tu():
    return _collect_loginfo(settings.LOG_TU_DIR, 100)

def collect_loginfo_latest(job):
    return _collect_loginfo(job.get_base_log_dir(), 1, job.get_log_dir_name())

def collect_loginfo_latest_7(job):
    return _collect_loginfo(job.get_base_log_dir(), 7, job.get_log_dir_name())

def _collect_loginfo(logdir, limit, config_dir_name=None):
    """ collect info from each log directory, put them in array with
        newer date ones first.
    """
    items = []

    # log directory structure
    # e.g.
    # logs/ru/2016-06-06_14-17-30/kiyoshiiwase-githubtest/tpa.log
    # logdir |     datetime      |      config name      | log name

    count = 0
    for datetime_dir in sorted(os.listdir(logdir), reverse=True): # 2016-06-06_14-17-30
        for configname_dir in sorted(os.listdir(os.path.join(logdir, datetime_dir))):
            if (config_dir_name != None) and (config_dir_name != configname_dir):
                continue
            loginfo = LogInfo()
            loginfo.datetime = datetime_dir
            loginfo.config_name = configname_dir
            loginfo.log_dir = os.path.join(logdir, datetime_dir, configname_dir)
            for logname in os.listdir(loginfo.log_dir):
                if logname == 'tpa.log':
                    loginfo.log_path = os.path.join(loginfo.log_dir, logname)
                    loginfo.log_size = os.path.getsize(loginfo.log_path)
                elif logname == 'tpa.err':
                    loginfo.err_path = os.path.join(loginfo.log_dir, logname)
                    loginfo.err_size = os.path.getsize(loginfo.err_path)
                else:
                    pass
            if count < limit:
                items.append(loginfo)
                count += 1

    return items

