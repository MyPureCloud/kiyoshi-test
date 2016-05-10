import sys, os, json

class ResourceValidator:
    def __init__(self):
        pass

    def validate(self, resource_path, resource_file_type):
        if resource_file_type == 'json':
            return self._validate_json(resource_path)
        else:
            sys.stdout.write("Resource validation is NIY for {}.\n".format(resoruce_file_type))
            return True

    def _validate_json(self, resource_path):
        with open(resource_path, 'r') as f:
            try:
                j = json.load(f)
            except ValueError as e:
                sys.stderr.write("Failed to validate: {}. Reason: {}\n".format(resource_path, e))
                return False
            else:
                return True


