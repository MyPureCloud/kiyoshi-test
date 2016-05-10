import sys, copy

class TransifexRepository:
    def __init__(self):
        self.name = str()
        self.owner = str()
        self.platform = str()
        self.languages = []
        self._errors = 0

    def parse(self, value):
        for k, v in value.items():
            if k == 'name':
                self.name = v
            elif k == 'owner':
                self.owner = v
            elif k == 'platform':
                self.platform = v
            elif k == 'languages':
                self.languages = v.split(',')
            else:
                self._errors += 1
                sys.stderr.write("Unexpected key under repository: {}\n".format(k))

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

        if len(self.languages) == 0:
            sys.stderr.write("repository.languages is not defined.\n")

        if self._errors == 0:
            return True
        else:
            return False

class TransifexRepositories:
    def __init__(self):
        self.repository_entry = []
        self._errors = 0

    def parse(self, items):
        for item in items:
            for k1, v1 in item.items():
                if k1 == 'repository':
                    r = TransifexRepository()
                    if r.parse(v1):
                        self.repository_entry.append(r)
                    else:
                        self._errors += 1
                else:
                    self._errors += 1
                    sys.stderr.write("Unknown key under repositories: {}\n".format(k))

        return self._validate()

    def _validate(self):
        if len(self.repository_entry) < 1:
            self._errors += 1
            sys.stderr.write("No repository defined.\n")

        if self._errors == 0:
            return True
        else:
            return False

class TransifexProject:
    def __init__(self):
        self.platform = str()
        self.name = str()
        self.repositories = TransifexRepositories()
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
            elif k == 'reviewers':
                for i in v:
                    self.reviewer_entry.append(i)
            else:
                self._errors += 1
                sys.stderr.write("Unexpected key under project: {}\n".format(k))

        return self._validate()

    def _validate(self):
        if not self.platform:
            self._errors += 1
            sys.stderr.write("project.platform is not defined.\n")

        if not self.name:
            self._errors += 1
            sys.stderr.write("project.name is not defined.\n")

        if self._errors == 0:
            return True
        else:
            return False

class TransifexConfiguration:
    def __init__(self):
        self._project = TransifexProject()
        self._maintainer_entry = []
        self._errors = 0

    def parse(self, data):
        for entry in data:
            for k, v in entry.items():
                if k == 'project':
                    if not self._project.parse(v):
                        self._errors += 1
                elif k == 'maintainers':
                    for i in v:
                        self._maintainer_entry.append(i)
                else:
                    self._errors += 1
                    sys.stderr.write("Unexpected key: {}. Expected only project key.\n".format(k))

        # TODO --- check  ot to allow duplicated repository name 
        
        if self._errors == 0:
            return True
        else:
            return False

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
    
    def get_project_repository_language(self, repository_index):
        return copy.deepcopy(self._project.repositories.repository_entry[repository_index].languages)

    def get_project_reviewers(self):
        return copy.deepcopy(self._project.reviewer_entry)

    def get_maintainers(self):
        return copy.deepcopy(self._maintainer_entry)

