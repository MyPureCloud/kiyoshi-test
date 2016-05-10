import sys, os
from shutil import copyfile
from ResourceConfigurationClass import ResourceConfiguration
from GitRepositoryClass import GitFileImport
from GithubRepositoryClass import GithubRepository
from ResourceValidatorClass import ResourceValidator
from TranslationRepositoryClass import TranslationBundle, Translation

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

class ResourceRepository:
    def __init__(self, config_path, log_dir):
        self._config_path = config_path
        self._log_dir = log_dir
        self._config = None
        self._local_repo_dir = str()
        self._batch_import_translations_starting_number = -1 
        self._batch_import_translations_ending_number = -1
        self._import_entries = []
        self._errors = 0

        self._load_config()
        self._repo = self._get_platform_repository()

    def _load_config(self):
        self._config = ResourceConfiguration()
        if not self._config.parse(self._config_path):
            raise ResourceRepositoryInitializationError("Failed to parse config: '{}'.".format(self._config_path))

    def _get_platform_repository(self):
        platform_name = self._config.get_repository_platform().lower()
        if platform_name == 'github': 
            return GithubRepository(
                    self._config.get_repository_url(),
                    self._config.get_repository_owner(),
                    self._config.get_repository_name(),
                    self._config.get_repository_branch()
                    )
        else:
            self._repo = None
            raise ResourceRepositoryInitializationError("BUG: Unknown repository platform: '{}'.\n".format(platform_name))

    def get_repository_name(self):
        return self._config.get_repository_name()

    def get_reviewers(self):
        return self._config.get_pullrequest_reviewers()

    def get_resource_bundle(self):
        resources = []
        n = self._config.get_resource_len()
        for i in range(0, n):
            resources.append(self._create_resource(self._config.get_repository_name(), i))
        return  ResourceBundle(self._repo, resources, self._log_dir)

    def _create_resource(self, repository_name, resource_index):
        r = Resource(
                repository_name,
                self._config.get_resource_path(resource_index),
                self._config.get_resource_filetype(resource_index),
                self._config.get_resource_language_code(resource_index),
                self._config.get_resource_translation(resource_index))
        return r


    def add_import_entry(self, translation_bundles):
        if len(translation_bundles) == 0: 
            return
        for bundle in translation_bundles:
            for translation in bundle:
                # ensure both translation path and local path are required in order to perfom importing a translation.
                #
                # if the translation path is not set (means it is not listed in resource config), it is considered as
                # resource repository is not ready for importing the translation.
                #
                # currently, translation's local_path is set only when translation is completed AND translation path is
                # set in resource config.
                if translation.resource_translation_path and translation.local_path:    
                    self._import_entries.append(GitFileImport(translation.resource_translation_path, translation.local_path))
                    sys.stdout.write("+'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.resource_translation_path))
                else:
                    # TODO --- diplaying download status might be more informative.
                    sys.stdout.write("-'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.resource_translation_path))
    def import_bundles(self, translation_bundles):
        self._add_import_entry(translation_bundles)
        if len(self._import_entries) == 0:
            sys.stderr.write("Nothing to import (_import_entries is empty).")
            return
        return repo.import_translation(self._import_entries)

    def submit_pullrequest(self, pullrequest):
        if platform_name == 'github': 
            pullrequest.title = self._config.get_pullrequest_title()
            pullrequest.description = self._config.get_pullrequest_description()
            # igonre reviewrs since github does not have such feature
            pullrequest.assignee = self._config.get_pullrequest_assignee()
        else:
            pullrequest.submitted = False
            sys.stderr.write("BUG: Unknown repository platform name: '{}'.\n".format(platform_name))
            return

        repo.submit_pullrequest(pullrequest)
        
