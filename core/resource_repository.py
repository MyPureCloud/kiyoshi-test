import sys, os
import abc
from collections import namedtuple
from shutil import copyfile

from ResourceValidatorClass import ResourceValidator

class Resource:
    def __init__(self, repository_name, resource_path, resource_filetype, resource_language_code, resource_translations):
        self.repository_name = repository_name
        self.resource_path = resource_path
        self.resource_filetype = resource_filetype
        self.resource_language_code = resource_language_code
        self.resource_translations = resource_translations
        # local
        self.local_path = str()

    def available(self):
        return self.local_path

class ResourceBundle:
    def __init__(self, platform_repository, resources, log_dir):
        self.platform_repo = platform_repository
        self._resources = resources
        self._log_dir = log_dir
        self._last_index = len(resources) - 1
        self._current_index = 0

    def __iter__(self):
        return self

    def next(self): # Python 3: def __next__(self)
        if self._current_index == 0:
            if not self.platform_repo.clone():
                raise StopIteration

        if self._current_index > self._last_index:
            raise StopIteration
        else:
            resource = self._resources[self._current_index]
            resource.local_path = self._prepare_local_resource(self._current_index)
            self._current_index += 1
            return resource

    def __len__(self):
        return len(self._resources)

    def _prepare_local_resource(self, resource_index):
        resource_path = self._resources[resource_index].resource_path
        local_resource_path = self.platform_repo.get_local_resource_path(resource_path)
        if not local_resource_path:
            sys.stderr.write("BUG: Faild to get local_resoruce_path.\n")
            return None

        if not os.path.isfile(local_resource_path):
            sys.stderr.write("Resource not found in local repo: '{}' ('{}').\n".format(local_resource_path, resource_path))
            return None

        v = ResourceValidator()
        if not v.validate(local_resource_path, self._resources[resource_index].resource_filetype):
            return None

        # create a copy of resource file in log dir as reference/evidence of uploaded file.
        upload_file_path = os.path.join(self._log_dir, str(resource_index) +  '_local_resource.file')
        if os.path.isfile(upload_file_path):
            os.remove(upload_file_path)
        copyfile(local_resource_path, upload_file_path)

        return upload_file_path

class ResourceRepository(object):
    """ Interface for subclass.
    """
    __metaclass__ = abc.ABCMeta
    def __init__(self):
        pass

    @abc.abstractmethod
    def get_resource_bundle(self):
        """ Return ResourceBundle for this resource repository.
        """
        sys.stderr.write("BUG: Abstract method ResourceRepository.get_resource_bundle() was called.\n")
        return None
    
    @abc.abstractmethod
    def import_bundles(self, translation_bundles):
        """ Return feature branch name in this resource repository if changes are made on files in
            this resource repository by importing translation files in TranslationBundle(s).
            Return None otherwise.
        """
        sys.stderr.write("BUG: Abstract method ResourceRepository.import_bundles() was called.\n")
        return None

    @abc.abstractmethod
    def submit_pullrequest(self, merge_branch_name, additional_reviewers=None):
        """ Submit pull request on remote repository in oder to merge specified feature branch.
            Specify additonal pull request reviewers who are not listed in resource config file.
            Retuns PullRequestResults.
        """
        sys.stderr.write("BUG: Abstract method ResourceRepository.submit_pullrequest() was called.\n")

