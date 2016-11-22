import sys
import os
import abc
from shutil import copyfile
import json

from core.resource import ResourceConfiguration
from core.translation import TranslationConfiguration

'''
    Resource Validator

    TODO --- move this somewhere
'''
class ResourceValidator:
    def __init__(self):
        pass

    def validate(self, resource_path, resource_file_type):
        if resource_file_type == 'json':
            return self._validate_json(resource_path)
        else:
            sys.stdout.write("No resource validator for {}.\n".format(resource_file_type))
            return True

    def _validate_json(self, resource_path):
        with open(resource_path, 'r') as f:
            try:
                j = json.load(f)
            except ValueError as e:
                sys.stderr.write("Failed to validate: {}. Reason: {}\n".format(resource_path, e))
                return False
            else:
                return True




'''
    Resource Repository


'''
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


'''
    Translation Repository


'''
class Translation:
    def __init__(self, repository_name, resource_path, translation_path, language_code):
        self.repository_name = repository_name
        self.resource_path = resource_path
        self.translation_path = translation_path
        self.language_code = language_code
        self.local_path = str()

        # TODO --- add download status (can be used to display Translation in TranslationBundle)

class TranslationBundle:
    def __init__(self, platform_repository, translations, log_dir):
        self.platform_repo = platform_repository
        self._translations = translations
        self._log_dir = log_dir
        self._last_index = len(translations) - 1
        self._current_index = 0

    def __iter__(self):
        return self

    def next(self): # Python 3: def __next__(self)
        if self._current_index > self._last_index:
            raise StopIteration
        else:
            translation = self._translations[self._current_index]
            if translation.translation_path:
                translation.local_paths = self._prepare_local_translations(self._current_index)
            else:
                #sys.stdout.write("'{}': Not listed in resource config. Skipped.\n".format(translation.language_code))
                pass
            self._current_index += 1
            return translation

    def __len__(self):
        return len(self._translations)

    def _prepare_local_translations(self, translation_index):
        translation = self._translations[translation_index]
        download = self.platform_repo.download_translation(translation.repository_name, translation.resource_path, translation.language_code)
        if download.errors == 0:
            if download.path:
                translation.local_path = download.path
                return 
            else:
                translation.local_path = None
        else:
            sys.stderr.write("{} Failed to download. Status code: {}\n".format(translation.language_code, download.status))
            translation.local_path = None

class TranslationRepository(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self, config, log_dir):
        self.config = config
        self._log_dir = log_dir

    def get_reviewers(self):
        return self.config.get_project_reviewers()

    def find_target_repository_index(self, resource_repo_name):
        n = self.config.get_project_repository_len()
        for i in range(0, n):
            if resource_repo_name == self.config.get_project_repository_name(i):
                return i
        else:
            return -1 

    @abc.abstractmethod
    def get_translation_bundle(self, resource):
        sys.stderr.write("BUG: Abstract method TranslationRepository.get_translation_bundle() was called.\n")
        return None

    @abc.abstractmethod
    def import_resource(self, resource):
        sys.stderr.write("BUG: Abstract method TranslationRepository.import_resource() was called.\n")
        return False

    @abc.abstractmethod
    def get_stats_project(self):
        sys.stderr.write("BUG: Abstract method TranslationRepository.get_stats_project() was called.\n")
        return False

