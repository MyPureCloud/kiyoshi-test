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
import core.repository as repository

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

    def post(self, resource_configuration_filename):
        config = urllib.unquote(resource_configuration_filename)
        try:
            j = json.loads(self.request.body)
        except ValueError as e:
            self.set_status(500)
            self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(e))
        else: 
            r = resource.update_configuration(config, j)
            if r:
                try:
                    s = json.dumps(resource.to_dict(r))
                except ValueError as e:
                    self.set_status(500)
                    self.finish("<html><body>Failed to json.dumps(). Reason: '{}'.</body></html>".format(e))
                else:
                    self.finish(s)
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to update resource configuration data.</body></html>")

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
    """ Return list of summary of projects in translation repository. """
    def get(self, arg): # translation platform name
        platform = urllib.unquote(arg)
        l = translation.get_platform_projects(platform)
        if l == None:
            self.set_status(400)
            self.finish("<html><body>Failed to obtain translation project listings for: '{}'.</body></html>".format(str(platform)))
        else:
            try:
                a = []
                for o in l:
                    a.append(translation.to_dict(o))
                j = json.dumps(a)
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(str(e)))
            else:
                self.finish(j)

class TranslationProjectDetailsHandler(tornado.web.RequestHandler):
    """ Return details of a project in translation repository. """
    def get(self, arg1, arg2):
        platform = urllib.unquote(arg1)
        pslug = urllib.unquote(arg2)
        d = translation.get_platform_project_details(platform, pslug)
        if d == None:
            self.set_status(400)
            self.finish("<html><body>Failed to obtain translation project details. Platform: '{}', Slug: '{}'.</body></html>".format(platform, pslug))
        else:
            try:
                j = json.dumps(translation.to_dict(d))
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(str(e)))
            else:
                self.finish(j)

class TranslationResourceDetailsHandler(tornado.web.RequestHandler):
    """ Return resource details for a resource in translation repository project. """
    def get(self, arg1, arg2, arg3):
        platform = urllib.unquote(arg1)
        pslug = urllib.unquote(arg2)
        rslug = urllib.unquote(arg3)
        d = translation.get_platform_project_resource_details(platform, pslug, rslug)
        if d == None:
            self.set_status(400)
            self.finish("<html><body>Failed to obtain translation project resource details. Platform: '{}', Pslug: '{}', Rslug: '{}'.</body></html>".format(platform, pslug, rslug))
        else:
            try:
                j = json.dumps(translation.to_dict(d))
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(str(e)))
            else:
                self.finish(j)

class TranslationTranslationStringsHandler(tornado.web.RequestHandler):
    """ Return list of translation strings for language of a resource in translation repository project. """
    def get(self, arg1, arg2, arg3, arg4):
        platform = urllib.unquote(arg1)
        pslug = urllib.unquote(arg2)
        rslug = urllib.unquote(arg3)
        lang = urllib.unquote(arg4)
        d = translation.get_platform_project_translation_strings(platform, pslug, rslug, lang)
        if d == None:
            self.set_status(400)
            self.finish("<html><body>Failed to obtain translation project translation strings. Platform: '{}', Pslug: '{}', Rslug: '{}', Lang: '{}'.</body></html>".format(platform, pslug, rslug, lang))
        else:
            try:
                l = []
                for x in d:
                    l.append(translation.to_dict(x))
                j = json.dumps(l)
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(str(e)))
            else:
                self.finish(j)

class TranslationSourceStringDetailsHandler(tornado.web.RequestHandler):
    """ Return details for a source string in translation repository project. """
    def get(self, arg1, arg2, arg3, arg4):
        platform = urllib.unquote(arg1)
        pslug = urllib.unquote(arg2)
        rslug = urllib.unquote(arg3)
        string_key = urllib.unquote(arg4)

        string_id = translation.get_platform_string_id(platform=platform, string_key=string_key)
        if string_id:
            d = translation.get_platform_project_source_string_details(platform, pslug, rslug, string_id)
            if d == None:
                self.set_status(400)
                self.finish("<html><body>Failed to obtain translation project source string details. Platform: '{}', Pslug: '{}', Rslug: '{}', StringKey: '{}'.</body></html>".format(platform, pslug, rslug, string_key))
            else:
                try:
                    j = json.dumps(translation.to_dict(d))
                except ValueError as e:
                    self.set_status(500)
                    self.finish("<html><body>Failed to json.load(). Reason: '{}'.</body></html>".format(str(e)))
                else:
                    self.finish(j)
        else:
            self.set_status(400)
            self.finish("<html><body>Failed to obtain sting id for source string details. Platform: '{}', Pslug: '{}', Rslug: '{}', StringKey: '{}'.</body></html>".format(platform, pslug, rslug, string_key))

class ListLocalRepositoriesHandler(tornado.web.RequestHandler):
    """ Return list of git directories under local repo directory. """
    def get(self):
        rootdir = repository.get_local_repository_directory()
        if rootdir == None:
            self.set_status(500)
            self.finish("<html><body>Local repository directory not found.</body></html>")
        else:
            l = [f for f in os.listdir(rootdir) if os.path.isdir(os.path.join(rootdir, f, '.git'))]
            try:
                j  = json.dumps(l)
            except ValueError as e:
                self.set_status(500)
                self.finish("<html><body>Failed to json.dumps(). Reason: '{}'.</body></html>".format(e))
            else:
                self.finish(j)

class ListLocalRepositoryFilesHandler(tornado.web.RequestHandler):
    """ Return list of specified directory in local repo directory. """
    def get(self, arg1, arg2): # arg1: repository name, arg2: relative path in the repository
        rootdir = repository.get_local_repository_directory()
        if rootdir == None:
            self.set_status(500)
            self.finish("<html><body>Local repository directory not found.</body></html>")
        else:
            fullpath = os.path.join(rootdir, urllib.unquote(arg1), urllib.unquote(arg2))   
            if os.path.isdir(fullpath):
                r = []
                for x in os.listdir(fullpath):
                    if os.path.isfile(os.path.join(fullpath, x)):
                        r.append({'type': 'file', 'name': x})
                    elif os.path.isdir(os.path.join(fullpath, x)):
                        r.append({'type': 'dir', 'name': x})
                    else:
                        logger.error("Skipped listing unknwon file type. Path: '{}'.".format(os.path.join(fullpath, x)))
                try:
                    j = json.dumps(r)
                except ValueError as e:
                    self.set_status(500)
                    self.finish("<html><body>Failed to json.dumps(). Reason: '{}'.</body></html>".format(e))
                else:
                    self.finish(j)
            else:
                self.set_status(500)
                self.finish("<html><body>Local directory not found. Path: '{}'.</body></html>".format(os.path.join(urllib.unquote(arg1), urllib.unquote(arg2))))

class ListLocalRepositoryBranchesHandler(tornado.web.RequestHandler):
    """ Return list of branch names for specified local repository. """
    def get(self, arg):
        rootdir = repository.get_local_repository_directory()
        if rootdir == None:
            self.set_status(500)
            self.finish("<html><body>Local repository directory not found.</body></html>")
        else:
            repo = os.path.join(rootdir, urllib.unquote(arg))   
            l = repository.get_local_repository_branches(repo)
            if l != None:
                try:
                    j = json.dumps(l)
                except ValueError as e:
                    self.set_status(500)
                    self.finish("<html><body>Failed to json.dumps(). Reason: '{}'.</body></html>".format(e))
                else:
                    self.finish(j)
            else:
                self.set_status(500)
                self.finish("<html><body>Failed to obtain local repository branches. Repository: '{}'.</body></html>".format(urllib.unquote(arg2)))

