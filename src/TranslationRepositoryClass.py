import sys, os
from TranslationConfigurationClass import TranslationConfiguration
from TransifexRepositoryClass import TransifexRepository
#from ResourceRepositoryClass import Resource

class TranslationRepositoryInitializationError(Exception):
    def __init__(self, message):
        super(TranslationRepositoryInitializationError, self).__init__(message)

class Translation:
    def __init__(self, resource, language_code):
        # TODO --- make this 'resorce' independent. currently it is pretty much Github.
        self.resource = resource
        self.language_code = language_code # which is defined in translation config.
        self.local_path = str()

        # translation path for the language (self.language_code) which is listed in resouce config file.
        # None if resouce config does not list translation path for the language.
        for translation in self.resource.resource_translations:
            if self.language_code == translation.language_code:
                self.resource_translation_path = translation.path
                break
        else:
            self.resource_translation_path = None

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
            # download translation if it is listed in resource config.
            translation = self._translations[self._current_index]
            found = False
            for k in translation.resource.resource_translations:
                if translation.language_code == k.language_code:
                    found = True
                    break
            
            if found:
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
        download = self.platform_repo.download_translation(translation.resource.repository_name, translation.resource.resource_path, translation.language_code)
        if download.errors == 0:
            if download.path:
                translation.local_path = download.path
                return 
            else:
                sys.stdout.write("{}: {}\n".format(translation.language_code, download.status))
                translation.local_path = None
        else:
            sys.stderr.write("{} Failed to download. Status code: {}\n".format(translation.language_code, download.status))
            translation.local_path = None

class TranslationRepository:
    def __init__(self, config_path, log_dir):
        self._config_path = config_path
        self._log_dir = log_dir
        self._config = None

        self._load_config()

    def _load_config(self):
        self._config = TranslationConfiguration()
        if not self._config.parse(self._config_path):
            raise TranslationRepositoryInitializationError("Failed to parse config: {}".format(self._config_path))

    def get_reviewers(self):
        return self._config.get_project_reviewers()

    def _find_target_repository_index(self, resource_repo_name):
        n = self._config.get_project_repository_len()
        for i in range(0, n):
            if resource_repo_name == self._config.get_project_repository_name(i):
                return i
        else:
            return -1 

    def _get_platform_repository(self):
        # TODO --- find it from plugin
        return TransifexRepository(self._config.get_project_name(), self._log_dir)

    def get_translation_bundle(self, resource):
        repo = self._get_platform_repository()
        if not repo:
            return None

        repo_index = self._find_target_repository_index(resource.repository_name)
        if repo_index == -1:
            sys.stderr.write("BUG: Failed to find target repository index.\n")
            return None

        translations = []
        for lang_code in self._config.get_project_repository_language(repo_index):
            translations.append(Translation(resource, lang_code.strip().rstrip()))

        return TranslationBundle(repo, translations, self._log_dir)

    def import_resource(self, resource):
        # TODO --- load repo as plugin
        repo = TransifexRepository(self._config.get_project_name(), self._log_dir)

        # TODO --- make TreansifexRepository accept generic resource context as a param
        return repo.import_resource(resource.repository_name, resource.resource_path, resource.local_path)

