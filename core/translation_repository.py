import sys
import os
import abc

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

