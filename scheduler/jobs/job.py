import os, sys
import datetime
import abc
import uuid

class Job(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self, job_dict):
        self.status = job_dict['status'] 
        self.name = job_dict['name']
        self.description = job_dict['description']
        # like ru | tu | aux + _ + name (all small letters, no spaces) + _ +  uuid.uuid1().hex
        self.id = job_dict['id']
        self.class_name = job_dict['class']
        self.month = job_dict['month']
        self.day = job_dict['day']
        self.day_of_week = job_dict['day_of_week']
        self.hour = job_dict['hour']
        self.minute = job_dict['minute']
        self.loginfo = None

    def get_attributes(self):
        return {
            "status": self.status,
            "name": self.name,
            "description": self.description,
            "id": self.id,
            "class": self.class_name,
            "month": self.month,
            "day": self.day,
            "day_of_week": self.day_of_week,
            "hour": self.hour,
            "minute": self.minute,
            "loginfo": self.loginfo
            }

    @abc.abstractmethod
    def update_loginfo(self, loginfo):
        pass

    @abc.abstractmethod
    def get_base_log_dir(self):
        pass

    @abc.abstractmethod
    def get_exec_status(self):
        pass

    @abc.abstractmethod
    def get_log_dir_name(self):
        pass

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        pass

