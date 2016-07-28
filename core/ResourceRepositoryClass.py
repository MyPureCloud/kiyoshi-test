import sys, os, abc
from shutil import copyfile
from ResourceConfigurationClass import ResourceConfiguration
from ResourceValidatorClass import ResourceValidator
from TranslationRepositoryClass import TranslationBundle, Translation
from GitRepositoryClass import GitFileImport

class ResourceRepositoryInitializationError(Exception):
    def __init__(self, message):
        super(ResourceRepositoryInitializationError, self).__init__(message)

class PullRequest:
    def __init__(self):
        # used for request
        self.branch_name = str()
        self.title= str()
        self.description = str()
        self.reviewers = []
        self.assignee = str()
        # used for response 
        self.errors = 0
        self.submitted = False
        self.message = str()
        self.status_code = None
        self.number = None
        self.url = None
        self.diff_url = None

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
    __metaclass__ = abc.ABCMeta
    def __init__(self, config, log_dir):
        self.config = config
        self._log_dir = log_dir
        self._local_repo_dir = str()
        self._import_entries = []

    def get_resource_bundle(self, child_repo):
        resources = []
        n = self.config.get_resource_len()
        for i in range(0, n):
            resources.append(self._create_resource(self.config.get_repository_name(), i))
        return  ResourceBundle(child_repo, resources, self._log_dir)

    def _create_resource(self, repository_name, resource_index):
        r = Resource(
                repository_name,
                self.config.get_resource_path(resource_index),
                self.config.get_resource_filetype(resource_index),
                self.config.get_resource_language_code(resource_index),
                self.config.get_resource_translation(resource_index))
        return r

    def add_import_entry(self, translation_bundles, options):
        if options['all_lang_per_resource']:
            self._add_import_entry_with_all_languages(translation_bundles)
        else:
            self._add_import_entry(translation_bundles)

    def _add_import_entry(self, translation_bundles):
        if len(translation_bundles) == 0: 
            return
        for bundle in translation_bundles:
            sys.stdout.write("Handling bundle (threshold: any_lang_per_resource)...\n")
            for translation in bundle:
                # ensure both translation path and local path are required in order to perfom importing a translation.
                #
                # if the translation_path is not set (means it is not listed in resource config), it is considered as
                # resource repository is not ready for importing the translation.
                #
                # currently, translation's local_path is set only when translation is completed AND translation path is
                # set in resource config.
                if translation.translation_path and translation.local_path:    
                    self._import_entries.append(GitFileImport(translation.translation_path, translation.local_path))
                    sys.stdout.write("+'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.translation_path))
                else:
                    # TODO --- diplaying download status might be more informative.
                    sys.stdout.write("-'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.translation_path))

    def _add_import_entry_with_all_languages(self, translation_bundles):
        if len(translation_bundles) == 0:
            return
        for bundle in translation_bundles:
            sys.stdout.write("Handling bundle (threshold: all_lang_per_resource)...\n")
            incompleted_translation = 0
            candidates = []
            for translation in bundle:
                # ensure both translation path and local path are required in order to perfom importing a translation.
                #
                # if the translation_path is not set (means it is not listed in resource config), it is considered as
                # resource repository is not ready for importing the translation.
                #
                # currently, translation's local_path is set only when translation is completed AND translation path is
                # set in resource config.
                if translation.translation_path:
                    if translation.local_path:
                        candidates.append(GitFileImport(translation.translation_path, translation.local_path))
                        sys.stdout.write("+'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.translation_path))
                    else:
                        incompleted_translation += 1
                else:
                    # TODO --- diplaying download status might be more informative.
                    sys.stdout.write("-'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.translation_path))

            if incompleted_translation == 0 and len(candidates) >= 1:
                for candidate in candidates:
                    self._import_entries.append(candidate)

    @abc.abstractmethod
    def import_bundles(self, translation_bundles, threshold):
        sys.stderr.write("BUG: Abstract method ResourceRepository.import_bundles() was called.\n")
        return None

    @abc.abstractmethod
    def submit_pullrequest(self, pullrequest):
        sys.stderr.write("BUG: Abstract method ResourceRepository.submit_pullrequest() was called.\n")

