'''
    API Handlers
'''

import os
import json
import urllib
import tornado.web

import logging
logger = logging.getLogger(__name__)

import core.project as project
import core.job as job
import core.resource as resource
import core.translation as translation

class JobExecutionHandler(tornado.web.RequestHandler):
    def post(self, param):
        job_id = urllib.unquote(param)
        c = job.get_configuration(id=job_id)
        if c:
            job.execute(c)
        else:
            logger.error("Faild to get configuration for job. id: '{}'.".format(job_id))

class JobResourceSlugsHandler(tornado.web.RequestHandler):
    """ 
    Returns resource/slug information for given job.
    The job has to be resource uploader job.
    """
    def get(self, param):
        job_id = urllib.unquote(param)
        j = job.get_details(job_id)
        if j.class_name == 'ResourceUploaderJob':
            r = resource.get_details(j.resource_config_filename)
            if r:
                resources = []
                for res in r.resources:
                    resources.append(res.path)
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to get resource details from '{}'.</body></html>".format(j.resource_config_filename))
            t = translation.get_details(j.translation_config_filename)
            if t:
                results = job.get_resource_slugs(t.platform, t.project_name, r.name, resources)
                if results:
                    try:
                        data = json.dumps(results) # results is list of dictionary.
                    except ValueError as e:
                        self.set_status(500)
                        self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
                    else:
                        self.finish(data)
                else:
                    self.set_status(500)
                    self.finish("<html><body>Failed to get resource slugs. Project: '{}', Resource: '{}'.</body></html>".format(t.project_name, r.name))
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to get translation details from '{}'.</body></html>".format(j.translation_config_filename))
        else:
            self.set_status(500)
            self.finish("<html><body>Sync Resource Slugs is not applicable to this job: '{} ({})'.</body></html>".format(job_id, j.class_name))

class JobTranslationSlugsHandler(tornado.web.RequestHandler):
    """ 
    Returns slug/name information for given job.
    The job has to be resource uploader job.
    """
    def get(self, param):
        job_id = urllib.unquote(param)
        j = job.get_details(job_id)
        if j.class_name == 'ResourceUploaderJob':
            r = resource.get_details(j.resource_config_filename)
            if r:
                resources = []
                for res in r.resources:
                    resources.append(res.path)
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to get resource details from '{}'.</body></html>".format(j.resource_config_filename))
            t = translation.get_details(j.translation_config_filename)
            if t:
                results = job.get_translation_slugs(t.platform, t.project_name)
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to get translation details from '{}'.</body></html>".format(j.translation_config_filename))
        else:
            self.set_status(500)
            self.finish("<html><body>Sync Resource Slugs is not applicable to this job: '{} ({})'.</body></html>".format(job_id, j.class_name))

        if results:
            try:
                data = json.dumps(results) # results is list of dictionary.
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
            else:
                self.finish(data)

class JobTranslationStatusHandler(tornado.web.RequestHandler):
    """ Translation status for a job. """
    def get(self, param):
        job_id = urllib.unquote(param)
        results = job.get_translation_status(job_id)
        try:
            data = json.dumps(results)
        except ValueError as e:
            self.set_status(500)
            self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
        else:
            self.finish(data)

class JobSyncStatusHandler(tornado.web.RequestHandler):
    """ 
    Sync status for a job.
    Currently, sync status is only applicable to resource uploader job or translation uploader job.
    """
    def get(self, param):
        job_id = urllib.unquote(param)
        j = job.get_details(job_id)
        if j.class_name == 'ResourceUploaderJob':
            # get resource repository name from resource configuration because translation configuration can contain
            # multiple resource repositories.
            r = resource.get_details(j.resource_config_filename)
            if r:
                resources = []
                for res in r.resources:
                    resources.append(res.path)
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to get resource details from '{}'.</body></html>".format(j.resource_config_filename))
            t = translation.get_details(j.translation_config_filename)
            if t:
                results = job.get_sync_status(job_id=job_id, job_class=j.class_name, translation_platform=t.platform, translation_project_name=t.project_name, resource_repository_name=r.name, resources=resources)
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to get translation details from '{}'.</body></html>".format(j.translation_config_filename))
        elif j.class_name == 'TranslationUploaderJob':
            r = resource.get_details(j.resource_config_filename)
            if r:
                results = job.get_sync_status(job_id=job_id, job_class=j.class_name, resource_platform=r.platform, repository_owner=r.owner, repository_name=r.name)
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to get resource details from '{}'.</body></html>".format(j.resource_config_filename))
        else:
            self.set_status(500)
            self.finish("<html><body>Sync status is not applicable to this job: '{} ({})'.</body></html>".format(job_id, j.class_name))

        if results:
            try:
                data = json.dumps(job.to_dict(results))
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
            else:
                self.finish(data)

class JobExecStatusHandler(tornado.web.RequestHandler):
    """ 
    Exec status for a job.
    """
    def get(self, param):
        job_id = urllib.unquote(param)
        c = job.get_configuration(job_id=job_id)
        if not c:
            self.set_status(500)
            self.finish("<html><body>Failed to get resource configuration for: '{}'.</body></html>".format(job_id))
       
        lists = job.get_execution_status(job_id)
        if lists:
            temp = []
            for l in lists:
                temp.append(job.to_dict(l))

            try:
                results = json.dumps(temp)
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
            else:
                self.finish(results)
        else:
            self.finish('{}')

class JobResourceDetailsHandler(tornado.web.RequestHandler):
    """ Details of resource for a job.
        The job should be ResourceUploaderJob.
    """
    def get(self, param):
        job_id = urllib.unquote(param)
        j = job.get_details(job_id)
        if j.class_name != 'ResourceUploaderJob':
            self.set_status(500)
            self.finish("<html><body>API resource/details is not applicable for this type of job: '{}'.</body></html>".format(j.class_name))
        results = resource.get_details(j.resource_config_filename)
        if not results:
            self.set_status(500)
            self.finish("<html><body>Failed to get resource details from: '{}'.</body></html>".format(j.resource_config_filename))
        try:
            data = json.dumps(resource.to_dict(results))
        except ValueError as e:
            self.set_status(500)
            self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
        else:
            self.finish(data)

class JobDetailsHandler(tornado.web.RequestHandler):
    """ Details for a job. """
    def get(self, param):
        job_id = urllib.unquote(param)
        results = job.get_details(job_id)
        try:
            data = json.dumps(job.to_dict(results))
        except ValueError as e:
            self.set_status(500)
            self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
        else:
            self.finish(data)

class JobSummaryHandler(tornado.web.RequestHandler):
    """ Summary for a job. """
    def get(self, param):
        job_id = urllib.unquote(param)
        results = job.get_summary(job_id=job_id)
        try:
            data = json.dumps(job.to_dict(results))
        except ValueError as e:
            self.set_status(500)
            self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
        else:
            self.finish(data)

class ListJobSummaryHandler(tornado.web.RequestHandler):
    """ List of summary for jobs. """
    def get(self):
        data = job.get_summary()
        l = []
        for d in data:
            l.append(job.to_dict(d))
        
        try:
            j  = json.dumps(l)
        except ValueError as e:
            self.set_status(500)
            self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
        else:
            self.finish(j)

class ProjectTranslationStatusHandler(tornado.web.RequestHandler):
    """ Translation status for each language. """
    def get(self, param):
        project_id = urllib.unquote(param)
        list_status = project.get_translation_status(project_id)
        if list_status:
            results = []
            for status in list_status:
                results.append(project.to_dict(status))
            try:
                data = json.dumps(results)
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
            else:
                self.finish(data)
        else:
            self.set_status(500)
            self.finish("<html><body>Failed to get translation status for id: '{}'.</body></html>".format(project_id))
            

class ProjectResourceDetailsHandler(tornado.web.RequestHandler):
    """ Details of resources for a prject. """
    def get(self, param):
        project_id = urllib.unquote(param)
        p = project.get_details(id=project_id)
        if p:
            for job_id in p.jobs:
                j = job.get_details(job_id)
                if j.class_name == 'ResourceUploaderJob':
                    results = resource.get_details(j.resource_config_filename)
                    try:
                        data = json.dumps(resource.to_dict(results))
                    except ValueError as e:
                        self.set_status(500)
                        self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
                    else:
                        self.finish(data)
                        break
        else:
            self.set_status(500)
            self.finish("<html><body>Failed to get project resource details for id: '{}'.</body></html>".format(project_id))

class ProjectDetailsHandler(tornado.web.RequestHandler):
    """ Details for a project. """
    def get(self, param):
        project_id = urllib.unquote(param)
        p = project.get_details(id=project_id)
        if p:
            try:
                data = json.dumps(project.to_dict(p))
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
            else:
                self.finish(data)
        else:
            self.set_status(500)
            self.finish("<html><body>Failed to get project details for id: '{}'.</body></html>".format(project_id))

class ListProjectSummaryHandler(tornado.web.RequestHandler):
    """ List of projects. """ 
    def get(self):
        results = []
        projects = project.get_summary()
        if projects:
            for p in projects:
                results.append(project.to_dict(p))
            try:
                data = json.dumps(results)
            except ValueError as e:
                self.set_status(500)
                message = "Failed to load prjoect summary as json. Reason: '{}'.".format(e)
                logger.error(message)
                self.finish("<html><body>{}</body></html>".format(message))
            else:
                self.finish(data)
        else:
            self.set_status(500)
            self.finish("<html><body>Failed to get list of project summary.</body></html>")

class LogContextHandler(tornado.web.RequestHandler):
    """ Raw context of a text log. """
    def get(self, param):
        log_path = urllib.unquote(param)
        if os.path.isfile(log_path):
            with open(log_path) as fi:
                lines = fi.readlines()
                try:
                    data = json.dumps(lines)
                except ValueError as e:
                    self.set_status(500)
                    self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
                else:
                    self.finish(data)
        else:
            self.set_status(500)
            self.finish("<html><body>Failed to get log context. File not found: '{}'.</body></html>".format(log_path))

# NOT USING now but keep it for a while
class ConfigurationHandler(tornado.web.RequestHandler):
    """ Raw context of a configuration file. """
    def get(self, job_id, key): # key is attribute name of resource or translation configuration file in job configuration file.
        lists = job.get_configuration(job_id=job_id)
        if lists:
            try:
                v = getattr(lists[0], key)
            except AttributeError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to get a value in configuration. job_id: '{}', key: '{}'.</body></html>".format(job_id, key))
            else:
                if key == 'resource_config_filename':
                    c = resource.get_configuration(filename=v)
                    try:
                        data = json.dumps(resource.to_dict(c))
                    except ValueError as e:
                        self.set_status(500)
                        self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
                    else:
                        self.finish(data)
                elif key == 'translation_config_filename':
                    translation.get_configuration(filename=v)
                    try:
                        data = json.dumps(translation.to_dict(c))
                    except ValueError as e:
                        self.set_status(500)
                        self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
                    else:
                        self.finish(data)
                else:
                    self.set_status(500)
                    self.finish("<html><body>Unknown key for a configuration entry. job_id: '{}', key: '{}'.</body></html>".format(job_id, key))
        else:
            self.set_status(500)
            self.finish("<html><body>Failed to get job configuration for: '{}'.</body></html>".format(job_id))

class ResourceConfigurationHandler(tornado.web.RequestHandler):
    """ Raw context of a resource configuration file. """
    def get(self, param): # resource config filename
        filename = urllib.unquote(param)
        c = resource.get_configuration(filename=filename)
        if c:
            try:
                data = json.dumps(resource.to_dict(c))
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
            else:
                self.finish(data)
        else:
            self.set_status(500)
            self.finish("<html><body>Failed to get resource configuration file context. filename '{}'.</body></html>".format(filename))

class TranslationConfigurationHandler(tornado.web.RequestHandler):
    """ Raw context of a translation configuration file. """
    def get(self, param): # translation config filename
        filename = urllib.unquote(param)
        c = translation.get_configuration(filename=filename)
        if c:
            try:
                data = json.dumps(translation.to_dict(c))
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
            else:
                self.finish(data)
        else:
            self.set_status(500)
            self.finish("<html><body>Failed to get translation configuration file context. filename '{}'.</body></html>".format(filename))

class ListTranslationProjectsHandler(tornado.web.RequestHandler):
#    def get(self):
#        creds = tpa.get_transifex_creds()
#        ret = transifex.query_projects(creds)
#        if ret.succeeded:
#            projects = ret.output
#        else:
#            logger.error("query_projects() failed. Reason: '{}'".format(ret.message))
#            projects = []
#        self.render('transifex_projects.html', projects=projects)
    pass

class TranslationProjectDetailsHandler(tornado.web.RequestHandler):
#    def get(self, param):
#        s = urllib.unquote(param)
#        platform_type = s.split(':')[0] # not used
#        project_slug = s.split(':')[1]
#
#        creds = tpa.get_transifex_creds()
#        ret = transifex.query_project(creds, project_slug)
#        if ret.succeeded:
#            project = ret.output
#            resources = []
#            for resource in project.resources:
#                ret = transifex.query_resource(creds, project_slug, resource.slug)
#                if ret.succeeded:
#                    resources.append(ret.output)
#            project_and_resources = {'project': project, 'resources': resources}
#        else:
#            logger.error("query_project() failed. Reason: '{}'".format(ret.message))
#            project_and_resources = {'project': None, 'resources': None}
#        self.render('transifex_project.html', data=project_and_resources)
    pass

class TranslationResourceDetailsHandler(tornado.web.RequestHandler):
#    def get(self, param):
#        s = urllib.unquote(param)
#        project_slug = s.split(':')[0]
#        resource_slug = s.split(':')[1]
#        project_name = s.split(':')[2]
#        resource_name = s.split(':')[3]
#        creds = tpa.get_transifex_creds()
#        ret = transifex.query_source_strings_details(creds, project_slug, resource_slug)
#        if ret.succeeded:
#            strings = ret.output
#        else:
#            logger.error("query_source_strings_detail() failed. Reason: '{}'".format(ret.message))
#            strings = []
#        self.render('transifex_resource.html', project_name=project_name, resource_name=resource_name, strings=strings)
    pass

class TranslationTranslationDetailsHandler(tornado.web.RequestHandler):
    pass

