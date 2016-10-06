import sys
import os
import copy
import yaml
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

"""
Parse resource configuration file in following foramt.

repository:
    name: myrepo 
    owner: kiyoshiiwase
    platform: github
    url: 'https://github.com/kiyoshiiwase/myrepo.git' 
    branch: master
    resources:
        - resource:
            path: app/locales/en-us.json
            filetype: json
            language_code: en-US
            translations:
                - ja: app/locales/ja.json
        - resource:
            path: src/strings/en/localizable.json
            filetype: json
            language_code: en-US
            translations:
                #- de: src/strings/de/localizalb.json
                - zh-CN: src/strings/zh-cn/localizalb.json
    pullrequest:
        title: Translation Updates
        reviewers:
            # reviewer entiries are optional. Can be a blank line for no reviewers.
            - kiyoshiiwase
    # options is optional.
    options:
        - hold_pullrequest_until_all_languages_completes: true
"""

# Translation
#
# keys          values
# -----------------------------------
# language_code     Language code for the translation file. e.g. 'es-MX'
# path              Path to the translation file in repository. e.g. src/strings/en-MX/localizable.json
Translation = namedtuple('Translation', 'language_code, path')

# Resource
#
# keys          values
# -----------------------------------
# path          Path to a resouce file in repository. e.g. 'src/strings/en-US.json'
# filetype      File type string for the resource file. e.g. 'json'
# language_code     Language code for the resouce file. e.g. 'en-US'
# translations      List of Translation tuples for translation files.
Resource = namedtuple('Resoruce', 'path, filetype, language_code, translations')

# PullRequest
# keys          values
# -----------------------------------
# title         One line text string for a pull request title.
# reviewers     List of reviewers.
PullRequest = namedtuple('PullRequest', 'titie, reviewers')

# Option
#
# keys          values
# -----------------------------------
# name          Name of option. 
# value         Value of the option. 
Option = namedtuple('Option', 'name, value')

# Represents a Resource Configuration file.
#
# keys          values
# -----------------------------------
# filename                  Resource file name
# path                      Resource file path
# parsed                    True when the resource file is successfully parsed, False otherwise.
# --- configuration file context ----
# repository_name           Resource repository name.
# repository_owner          Resource repository owner of the platform (e.g. inindca)
# repository_platform       Resource repository platform name (e.g. Bitbucket).
# repository_url            URL to the repository.
# repository_branch         Branch of the repository (e.g. master).
# repository_resource_len   Number of resource files defined in the resource file.
# resources                 List of Resource tuples
# pullrequest               A PullRequest tule
# options                   List of Option tuples.
ResourceConfiguration = namedtuple('ResourceConfiguration', 'filename, path, parsed, repository_name, repository_owner, repository_platform, repository_url, repository_branch, repository_resource_len, resources, pullrequest, options')

def _succeeded_translations(config, resource_idx):
    translations = config.get_resource_translation(resource_idx)
    results = []
    for translation in translations:
        results.append(Translation(translation.language_code, translation.path))
    return results

def _succeeded_resources(config):
    results = []
    for i in range(0, config.get_resource_len()):
        translations = _succeeded_translations(config, i)
        results.append(Resource(
            config.get_resource_path(i),
            config.get_resource_filetype(i),
            config.get_resource_language_code(i),
            translations
            ))
    return results

def _failed_pullrequest():
    return PullRequest('N/A', [])

def _succeeded_pullrequest(config):
    return PullRequest(
        config.get_pullrequest_title(),
        config.get_pullrequest_reviewers()
        )

def _succeeded_options(config):
    options = config.get_options()
    results = []
    for option in options:
        results.append(Option(option['name'], option['value']))
    return results

def _failed_configuration(config_path):
    return ResourceConfiguration(
        os.path.basename(config_path),
        config_path,
        False,
        'N/A',
        'N/A',
        'N/A',
        'N/A',
        'N/A',
        'N/A',
        [],
        _failed_pullrequest(),
        []
        )

def _succeeded_configuration(config):
    config_path = config.get_configuration_file_path()
    return ResourceConfiguration(
        os.path.basename(config_path),
        config_path,
        True,
        config.get_repository_name(),
        config.get_repository_owner(),
        config.get_repository_platform(),
        config.get_repository_url(),
        config.get_repository_branch(),
        config.get_resource_len(),
        _succeeded_resources(config),
        _succeeded_pullrequest(config),
        _succeeded_options(config)
        )

def parse_resource_configuration_file(config_path):
    """ Returns ResourceConfiguration tuple by reading a resouce configuration file.
        When parsing goes properly, .parsed is set to True, or False othewise.
    """
    if not os.path.isfile(config_path):
        logger.error("Resource config file not found: '{}'.".format(config_path))
        return _failed_configuration(config_path)

    config = ResourcePlatformConfiguration()
    if not config.parse(config_path):
        return _failed_configuration(config_path)
    
    return _succeeded_configuration(config) 

class PullRequestSection:
    def __init__(self):
        self.title = str()
        self.reviewer_entry = []
        self._errors = 0

    def parse(self, key, value):
        for k0, v0 in value.items():
            if k0 == "title":
                self.title = v0
            elif k0 == "reviewers":
                # Number of reviewer can be zero.
                # So, so this section can be empty.
                if v0:
                    for i in v0:
                        self.reviewer_entry.append(i)
            else:
                self._errors += 1
                sys.stderr.write("Unexpected key '{}' in pullrequest section.\n".format(k0))

        return self._validate()

    def _validate(self):
        if not self.title:
            self._errors += 1
            sys.stderr.write("pullrequest.title not defined.\n")

        # reviewers are not required

        return self._errors == 0

class TranslationSection:
    def __init__(self):
        self.language_code = str()
        self.path = str()

    def parse(self, key, value):
        self.language_code = key
        self.path = value
        return self._validate()

    def _validate(self):
        # TODO --- ensure langage code is valid and file exsits.
        return True

class ResourceSection:
    def __init__(self):
        self.path = str()
        self.filetype = str()
        self.language_code = str()
        self.translation_entry = []
        self._errors = 0

    def parse(self, key, value):
        for k0, v0 in value.items():
            if k0 == "path":
                self.path = v0
            elif k0 == "filetype":
                self.filetype = v0
            elif k0 == "language_code":
                self.language_code = v0
            elif k0 == "translations":
                # number of translations entries can be zero.
                # so, this can be empty.
                if v0:
                    for i in v0:
                        for k1, v1 in i.items():
                            t = TranslationSection()
                            if t.parse(k1, v1):
                                self.translation_entry.append(t)
                            else:
                                self._errors += 1
            else:
                self._errors += 1
                sys.stderr.write("Unexpected key '{}' in resource section.\n".format(k0))

        return self._validate()

    def _validate(self):
        if not self.path:
            self._errors += 1
            sys.stderr.write("resource.path not defined.\n")

        if not self.filetype:
            self._errors += 1
            sys.stderr.write("resource.filetype not defined.\n")

        if not self.language_code:
            self._errors += 1
            sys.stderr.write("resource.language_code not defined.\n")

        # translation enties are not required.

        return self._errors == 0

class ResourcesSection:
    def __init__(self):
        self.resource_entry = []
        self._errors = 0

    def parse(self, items):
        for item in items:
            for k1, v1 in item.items():
                if k1 == "resource":
                    r = ResourceSection()
                    if r.parse(k1, v1):
                        self.resource_entry.append(r)
                    else:
                        self._errors += 1
                else:
                    self._errors += 1
                    sys.stderr.write("Unexpected key '{}' in resources section.\n".format(k))

        return self._validate()

    def _validate(self):
        if len(self.resource_entry) < 1:
            self._errors += 1
            sys.stderr.write("No resource defined.\n")

        return self._errors == 0

class RepositorySection:
    def __init__(self):
        self.owner = str()
        self.platform = str()
        self.name = str()
        self.url = str()
        self.branch = str()
        self.resources = ResourcesSection()
        self.pullrequest = PullRequestSection()
        self.option_entry = []
        self._errors = 0

    def parse(self, value):
        for k, v in value.items():
            if k == "platform":
                self.platform = v
            elif k == "owner":
                self.owner = v
            elif k == "name":
                self.name = v
            elif k == "url":
                self.url = v
            elif k == "branch":
                self.branch = v
            elif k == "resources":
                if not self.resources.parse(v):
                    self._errors += 1
            elif k == "pullrequest":
                if not self.pullrequest.parse(k, v):
                    self._errors += 1
            elif k == "options":
                # Number of options can be zero.
                # So, so this section can be empty.
                if v:
                    for i in v:
                        for k1, v1 in i.items():
                            self.option_entry.append({'name': k1, 'value': v1})
            else:
                self._errors += 1
                sys.stderr.write("Unexpected key '{}' in repository section.\n".format(k))

        return self._validate()

    def _validate(self):
        if not self.platform:
            self._errors += 1
            sys.stderr.write("repository.platform is not defined.\n")

        if not self.name:
            self._errors += 1
            sys.stderr.write("repository.name is not defined.\n")

        if not self.owner:
            self._errors += 1
            sys.stderr.write("repository.owner is not defined.\n")

        if not self.url:
            self._errors += 1
            sys.stderr.write("repository.url is not defined.\n")

        if not self.branch:
            self._errors += 1
            sys.stderr.write("repository.branch is not defined.\n")

        return self._errors == 0

class ResourcePlatformConfiguration:
    def __init__(self):
        self._config_path = None
        self._repository_section = RepositorySection()
        self._errors = 0

    def parse(self, config_path):
        self._config_path = config_path
        with open(config_path, "r") as stream:
            data = yaml.load_all(stream)
            return self._parse(data)

    def _parse(self, data):
        for entry in data:
            for k, v in entry.items():
                if k == 'repository':
                    if not self._repository_section.parse(v):
                        self._errors += 1
                else:
                    self._errors += 1
                    sys.stderr.write("Unexpected key '{}' in global section.\n".format(k))

        return self._errors == 0

    def get_configuration_file_path(self):
        return self._config_path

    def get_repository_platform(self):
        return self._repository_section.platform

    def get_repository_name(self):
        return self._repository_section.name

    def get_repository_owner(self):
        return self._repository_section.owner

    def get_repository_url(self):
        return self._repository_section.url

    def get_repository_branch(self):
        return self._repository_section.branch

    def get_resource_len(self):
        return len(self._repository_section.resources.resource_entry)

    def get_resource_path(self, resource_index):
        return self._repository_section.resources.resource_entry[resource_index].path

    def get_resource_filetype(self, resource_index):
        return self._repository_section.resources.resource_entry[resource_index].filetype

    def get_resource_language_code(self, resource_index):
        return self._repository_section.resources.resource_entry[resource_index].language_code

    def get_resource_translation_len(self, resource_index):
        return len(self._repository_section.resources.resource_entry[resource_index].tranalation_entry)

    def get_resource_translation(self, resource_index):
        return copy.deepcopy(self._repository_section.resources.resource_entry[resource_index].translation_entry)

    def get_pullrequest_title(self):
        return self._repository_section.pullrequest.title

    def get_pullrequest_reviewers(self):
        return copy.deepcopy(self._repository_section.pullrequest.reviewer_entry)

    def get_options(self):
        return copy.deepcopy(self._repository_section.option_entry)

