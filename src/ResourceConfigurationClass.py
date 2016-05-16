import sys, yaml
from GithubConfigurationClass import GithubConfiguration

class ResourceConfiguration:
    def __init__(self):
        self._config = None
        self._errors = 0

    def parse(self, config_path):
        self._config = GithubConfiguration()
        with open(config_path, "r") as stream:
            data = yaml.load_all(stream)
            if not self._config.parse(data):
                self._errors += 1

        if self._errors == 0:
            return True
        else:
            return False

    def get_repository_platform(self):
        return self._config.get_repository_platform()

    def get_repository_name(self):
        return self._config.get_repository_name()

    def get_repository_owner(self):
        return self._config.get_repository_owner()

    def get_repository_platform(self):
        return self._config.get_repository_platform()

    def get_repository_url(self):
        return self._config.get_repository_url()

    def get_repository_branch(self):
        return self._config.get_repository_branch()

    def get_resource_len(self):
        return self._config.get_resource_len()

    def get_resource_path(self, resource_index):
        return self._config.get_resource_path(resource_index)

    def get_resource_filetype(self, resource_index):
        return self._config.get_resource_filetype(resource_index)

    def get_resource_language_code(self, resource_index):
        return self._config.get_resource_language_code(resource_index)

    def get_resource_translation_len(self, resource_index):
        return self._config.get_resource_translation_len(index)

    def get_resource_translation(self, resource_index):
        return self._config.get_resource_translation(resource_index)

    def get_pullrequest_title(self):
        return self._config.get_pullrequest_title()

    def get_pullrequest_description(self):
        return self._config.get_pullrequest_description()

    # for github
    def get_pullrequest_assignee(self):
        return self._config.get_pullrequest_assignee()

    def get_pullrequest_reviewers(self):
        return self._config.get_pullrequest_reviewers()

    def get_maintainers(self):
        return self._config.get_maintainer()

