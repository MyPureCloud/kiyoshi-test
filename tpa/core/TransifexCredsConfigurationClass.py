import sys, yaml

class TransifexCredsConfiguration:
    def __init__(self):
        self._user_name = str()
        self._user_passwd = str()
        self._user_email = str()
        self._project_slug_prefix = str()
        self._resource_slug_prefix = str()

    def parse(self, config_path):
        with open(config_path, "r") as stream:
            data = yaml.load_all(stream)
            return self._parse(data)

    def _parse(self, data):
        errors = 0
        for entry in data:
            for k, v in entry.items():
                if k == 'user_name':
                    self._user_name = v
                elif k == 'user_passwd':
                    self._user_passwd = v
                elif k == 'user_email':
                    self._user_email = v
                elif k == 'project_slug_prefix':
                    self._project_slug_prefix = v
                elif k == 'resource_slug_prefix':
                    self._resource_slug_prefix = v
                else:
                    errors += 1
                    sys.stderr.write("Unexpected key: {}.\n".format(k))

        if not self._user_name:
            errors += 1
            sys.stderr.write("Missing user_name.")
            
        if not self._user_passwd:
            errors += 1
            sys.stderr.write("Missing user_passwd.")

        if not self._user_email:
            errors += 1
            sys.stderr.write("Missing user_email.")

        if errors == 0:
            return True
        else:
            return False

    def get_username(self):
        return self._user_name

    def get_userpasswd(self):
        return self._user_passwd

    def get_useremail(self):
        return self._user_email

    def get_project_slug_prefix(self):
        return self._project_slug_prefix

    def get_resource_slug_prefix(self):
        return self._resource_slug_prefix

