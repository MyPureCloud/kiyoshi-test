"""
This class is to parse a configuration file for translation repository.

Following is an example of expected configuration file format.

<TBW>
"""

import sys
import copy
import yaml

class RepositorySection:
    def __init__(self):
        self.name = str()
        self.owner = str()
        self.platform = str()
        self._errors = 0

    def parse(self, value):
        for k, v in value.items():
            if k == 'name':
                self.name = v
            elif k == 'owner':
                self.owner = v
            elif k == 'platform':
                self.platform = v
            else:
                self._errors += 1
                sys.stderr.write("Unexpected key '{}' in repository section.\n".format(k))

        return self._validate()

    def _validate(self):
        if not self.name:
            self._errors += 1
            sys.stderr.write("repository.name is not defined.\n")

        if not self.owner:
            self._errors += 1
            sys.stderr.write("repository.owner is not defined.\n")

        if not self.platform:
            self._errors += 1
            sys.stderr.write("repository.platform is not defined.\n")

        return self._errors == 0

class RepositoriesSection:
    def __init__(self):
        self.repository_entry = []
        self._errors = 0

    def parse(self, items):
        for item in items:
            for k1, v1 in item.items():
                if k1 == 'repository':
                    r = RepositorySection()
                    if r.parse(v1):
                        self.repository_entry.append(r)
                    else:
                        self._errors += 1
                else:
                    self._errors += 1
                    sys.stderr.write("Unknown key '{}' in repositories section.\n".format(k))

        return self._validate()

    def _validate(self):
        if len(self.repository_entry) < 1:
            self._errors += 1
            sys.stderr.write("No repositories.repository defined.\n")
            
        return self._errors == 0

class ProjectSection:
    def __init__(self):
        self.platform = str()
        self.name = str()
        self.repositories = RepositoriesSection()
        self.languages = []
        self.reviewer_entry = []
        self._errors = 0

    def parse(self, value):
        for k, v in value.items():
            if k == 'platform':
                self.platform = v
            elif k == 'name':
                self.name = v
            elif k == 'repositories':
                if not self.repositories.parse(v):
                    self._errors += 1
            elif k == 'languages':
                self.languages = [s.strip().rstrip() for s in v.split(',')]
            elif k == 'reviewers':
                for i in v:
                    self.reviewer_entry.append(i)
            else:
                self._errors += 1
                sys.stderr.write("Unexpected key '{}' in project section.\n".format(k))

        return self._validate()

    def _validate(self):
        if not self.platform:
            self._errors += 1
            sys.stderr.write("project.platform is not defined.\n")

        if not self.name:
            self._errors += 1
            sys.stderr.write("project.name is not defined.\n")

        return self._errors == 0

class TranslationPlatformConfiguration:
    def __init__(self):
        self._project = ProjectSection()
        self._errors = 0

    def parse(self, config_path):
        with open(config_path, "r") as stream:
            data = yaml.load_all(stream)
            return self._parse(data)

    def _parse(self, data):
        for entry in data:
            for k, v in entry.items():
                if k == 'project':
                    if not self._project.parse(v):
                        self._errors += 1
                else:
                    self._errors += 1
                    sys.stderr.write("Unexpected key '{}' in global section.\n".format(k))

        return self._errors == 0

    def get_project_name(self):
        return self._project.name

    def get_project_platform(self):
        return self._project.platform

    def get_project_repository_len(self):
        return len(self._project.repositories.repository_entry)

    def get_project_repository_name(self, repository_index):
        return self._project.repositories.repository_entry[repository_index].name

    def get_project_repository_owner(self, repository_index):
        return self._project.repositories.repository_entry[repository_index].owner

    def get_project_repository_platform(self, repository_index):
        return self._project.repositories.repository_entry[repository_index].platform
    
    def get_project_languages(self):
        return copy.deepcopy(self._project.languages)

    def get_project_reviewers(self):
        return copy.deepcopy(self._project.reviewer_entry)

