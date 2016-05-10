import sys, copy

class GithubPullRequest:
    def __init__(self):
        self.title = str()
        self.description = str()
        self.assignee = str()
        self.reviewer_entry = []
        self._errors = 0

    def parse(self, key, value):
        for k0, v0 in value.items():
            if k0 == "title":
                self.title = v0
            elif k0 == "description":
                self.description = v0
            elif k0 == "assignee":
                self.assignee = v0
            elif k0 == "reviewers":
                for i in v0:
                    self.reviewer_entry.append(i)
            else:
                self._errors += 1
                sys.stderr.write("Unknown key: {} under pullrequest.\n".format(k0))

        return self._validate()

    def _validate(self):
        if not self.title:
            self._errors += 1
            sys.stderr.write("pullrequest.title not defined.\n")

        if not self.description:
            self._errors += 1
            sys.stderr.write("pullrequest.description not defined.\n")

        # reviewers are not used for now

        # no assignee is fine

        if self._errors == 0:
            return True
        else:
            return False

class GithubTranslation:
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

class GithubResource:
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
                if v0:
                    for i in v0:
                        for k1, v1 in i.items():
                            t = GithubTranslation()
                            if t.parse(k1, v1):
                                self.translation_entry.append(t)
                            else:
                                self._errors += 1
            else:
                self._errors += 1
                sys.stderr.write("Unknown key: {} under resource.\n".format(k0))

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

        if self._errors == 0:
            return True
        else:
            return False

class GithubResources:
    def __init__(self):
        self.resource_entry = []
        self._errors = 0

    def parse(self, items):
        for item in items:
            for k1, v1 in item.items():
                if k1 == "resource":
                    r = GithubResource()
                    if r.parse(k1, v1):
                        self.resource_entry.append(r)
                    else:
                        self._errors += 1
                else:
                    self._errors += 1
                    sys.stderr.write("Unknown key under resources: {}\n".format(k))

        return self._validate()

    def _validate(self):
        if len(self.resource_entry) < 1:
            self._errors += 1
            sys.stderr.write("No resource defined.\n")

        if self._errors == 0:
            return True
        else:
            return False

class GithubRepository:
    def __init__(self):
        self.owner = str()
        self.platform = str()
        self.name = str()
        self.url = str()
        self.branch = str()
        self.resources = GithubResources()
        self.pullrequest = GithubPullRequest()
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
            else:
                self._errors += 1
                sys.stderr.write("Unexpected key under repository: {}\n".format(k))

        return self._validate()

    def _validate(self):
        if not self.platform:
            self._errors += 1

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

        if self._errors == 0:
            return True
        else:
            return False

class GithubConfiguration:
    def __init__(self):
        self._repository = GithubRepository()
        self._maintainer_entry = []
        self._errors = 0

    def parse(self, data):
        for entry in data:
            for k, v in entry.items():
                if k == 'repository':
                    if not self._repository.parse(v):
                        self._errors += 1
                elif k == 'maintainers':
                    for i in v:
                        self._maintainer_entry.append(i)
                else:
                    self._errors += 1
                    sys.stderr.write("Unexpected key: {}. Expected only repository key.\n".format(k))

        if self._errors == 0:
            return True
        else:
            return False

    def get_repository_platform(self):
        return self._repository.platform

    def get_repository_name(self):
        return self._repository.name

    def get_repository_owner(self):
        return self._repository.owner

    def get_repository_url(self):
        return self._repository.url

    def get_repository_branch(self):
        return self._repository.branch

    def get_resource_len(self):
        return len(self._repository.resources.resource_entry)

    def get_resource_path(self, resource_index):
        return self._repository.resources.resource_entry[resource_index].path

    def get_resource_filetype(self, resource_index):
        return self._repository.resources.resource_entry[resource_index].filetype

    def get_resource_language_code(self, resource_index):
        return self._repository.resources.resource_entry[resource_index].language_code

    def get_resource_translation_len(self, resource_index):
        return len(self._repository.resources.resource_entry[resource_index].tranalation_entry)

    def get_resource_translation(self, resource_index):
        return copy.deepcopy(self._repository.resources.resource_entry[resource_index].translation_entry)

    def get_pullrequest_title(self):
        return self._repository.pullrequest.title

    def get_pullrequest_description(self):
        return self._repository.pullrequest.description

    def get_pullrequest_assignee(self):
        return self._repository.pullrequest.assignee

    def get_pullrequest_reviewers(self):
        return copy.deepcopy(self._repository.pullrequest.reviewer_entry)

    def get_maintainer(self):
        return copy.deepcopy(self._maintainer_entry)
