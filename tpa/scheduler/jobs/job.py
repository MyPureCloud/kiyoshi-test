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
        
        try:
            self.last_exec_status = job_dict['last_exec_status']
            self.last_exec_datetime = job_dict['last_exec_datetime']
        except KeyError as e:
            self.last_exec_status = None
            self.last_exec_datetime = None 

    @abc.abstractmethod
    def get_base_log_dir(self):
        pass

    @abc.abstractmethod
    def get_log_dir_name(self):
        pass

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        pass

