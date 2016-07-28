import sys, os, re, requests, json
from requests.exceptions import ConnectionError
from collections import OrderedDict

import settings
from GitCredsConfigurationClass import GitCredsConfiguration
from GitRepositoryClass import GitRepository, GitFileImport
from ResourceRepositoryClass import ResourceRepository

class BitbucketRepository(ResourceRepository, GitRepository):
    def __init__(self, config, log_dir):
        self._log_dir = log_dir
        ResourceRepository.__init__(self, config, log_dir)
        GitRepository.__init__(self, config.get_repository_url(), config.get_repository_owner(), config.get_repository_name(), config.get_repository_branch())

    def get_repository_name(self):
        return self.config.get_repository_name()

    def get_repository_platform(self):
        return self.config.get_repository_platform() 

    def get_repository_url(self):
        return self.config.get_repository_url()

    def get_local_resource_path(self, resource_path):
        return GitRepository.get_local_resource_path(self, resource_path)

    def _bitbucket_creds_set(self):
        return self.git_creds_set()

    def _set_bitbucket_creds(self):
        if not os.path.isfile(settings.BITBUCKET_CREDS_FILE):
            sys.stderr.write("File not found: {}.\n".format(settings.BITBUCKET_CREDS_FILE))
            return False

        t = GitCredsConfiguration()
        if not t.parse(settings.BITBUCKET_CREDS_FILE):
            sys.stderr.write("Failed to parse: {}\n".format(settings.BITBUCKET_CREDS_FILE))
            return False
        else:
            self.set_git_creds(t.get_username(), t.get_userpasswd(), t.get_useremail(), t.get_user_fullname())
            return True

    def isfile(self, file_path):
        return super(BitbucketRepository, self).isfile(file_path)

    def clone(self):
        return GitRepository.clone(self)

    def get_resource_bundle(self):
        return ResourceRepository.get_resource_bundle(self, self)

    def _import_translation(self, list_translation_import):
        if not self._bitbucket_creds_set():
            if not self._set_bitbucket_creds():
                sys.stderr.write("Failed to set git creds. Nothing was imported.\n")
                return None
        return GitRepository.import_translation(self, list_translation_import)

    def import_bundles(self, translation_bundles, threshold):
        ResourceRepository.add_import_entry(self, translation_bundles, threshold)
        if len(self._import_entries) == 0:
            sys.stderr.write("Nothing to import (_import_entries is empty).\n")
            return
        return self._import_translation(self._import_entries)

    def _set_remote_url(self):
        user_name = self.get_user_name()
        user_passwd = self.get_user_passwd()
        repository_owner = self.get_repository_owner()
        repository_name = self.get_repository_name()
        url = "https://{}:{}@bitbucket.org/{}/{}.git".format(user_name, user_passwd, repository_owner, repository_name)
        return self.set_remote_url(url)

    def submit_pullrequest(self, pullrequest):
        pullrequest.title = self.config.get_pullrequest_title()
        pullrequest.description = self.config.get_pullrequest_description()
        self._submit_pullrequest(pullrequest)

    def _submit_pullrequest(self, pullrequest):
        list_commited_files = []
        if not self._adjust_staged_translation(pullrequest.branch_name, list_commited_files):
            pullrequest.errors += 1
            pullrequest.submitted = False
            pullrequest.message = "Failed to adjust staged translation. PR NOT submitted."
            d = {
                "operation": "TranslationUpload",
                "results": "FAILURE",
                "reason": pullrequest.message,
                "status_code": None,
                "pullrequest_url": None
            }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            return

        if len(list_commited_files) == 0:
            pullrequest.errors = 0
            pullrequest.submitted = False
            pullrequest.message = "No staged files. PR NOT submitted."
            d = {
                "operation": "TranslationUpload",
                "results": "SUCCESS",
                "reason": pullrequest.message,
                "status_code": None,
                "pullrequest_url": None
            }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            return
        else:
            for ent in list_commited_files:
                sys.stdout.write("Committed: '{}'\n".format(ent))

        if not super(BitbucketRepository, self).push_branch(pullrequest.branch_name):
            pullrequest.errors += 1
            pullrequest.submitted = False
            pullrequest.message = "Failed to push feature branch. PR NOT submitted."
            d = {
                "operation": "TranslationUpload",
                "results": "FAILURE",
                "reason": pullrequest.message,
                "status_code": None,
                "pullrequest_url": None
            }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            return

        if not self._bitbucket_creds_set():
            if not self._set_bitbucket_creds():
                pullrequest.errors += 1
                pullrequest.submitted = False
                pullrequest.message = "Failed to read bitbucket creds file. PR NOT submitted."
                d = {
                    "operation": "TranslationUpload",
                    "results": "FAILURE",
                    "reason": pullrequest.message,
                    "status_code": None,
                    "pullrequest_url": None
                }
                sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
                return

        pullrequest_description = self._generate_pullrequest_description(pullrequest.description, list_commited_files)
        url = 'https://bitbucket.org/api/2.0/repositories/' + self._repository_owner + '/' + self._repository_name + '/pullrequests'
        reviewers = []
        for s in pullrequest.reviewers:
            reviewers.append({'username': s})
        payload = json.dumps({
            'source': {
                'branch': {
                    'name': pullrequest.branch_name
                },
                'repository': {
                    'full_name': self._repository_owner + '/' + self._repository_name
                }
            },
            'destination': {
                'branch': {
                    'name': self._repository_branch_name
                }
            },
            'title': pullrequest.title,
            'description': pullrequest_description,
            'reviewers': reviewers,
            'close_source_branch': 'true'}, ensure_ascii=False)
        headers = {'Content-Type': 'application/json'}
        try:
            r =  requests.post(url, auth=(self._git_username, self._git_userpasswd), headers=headers, data=payload)
        except ConnectionError as e:
            pullrequest.errors += 1
            pullrequest.submitted = False
            pullrequest.message = "Failed to submit PR. Reason: '{}'.".format(e)
            d = {
                "operation": "TranslationUpload",
                "results": "FAILURE",
                "reason": pullrequest.message,
                "status_code": r.status_code,
                "pullrequest_url": None
            }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            return
        else:
            pass

        pullrequest.status_code = r.status_code
        if not (r.status_code == 200 or r.status_code == 201):
            pullrequest.submitted = False
            pullrequest.message = "Failed to submit PR. Status code: '{}'.".format(r.status_code)
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text)
            d = {
                "operation": "TranslationUpload",
                "results": "FAILURE",
                "reason": pullrequest.message,
                "status_code": r.status_code,
                "pullrequest_url": None
            }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            return

        pullrequest.submitted = True
        try:
            j = json.loads(r.text, object_pairs_hook=OrderedDict)
        except ValueError as e:
            # PR was succeeded but cannot supply info.
            pullrequest.errors += 1
            pullrequest.message = "Submitted PR but failed to obtain PR details." 
            sys.stderr.write("Failed read pullrequest result as json. Reason: '{}'.\n".format(e))
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text)
            d = {
                "operation": "TranslationUpload",
                "results": "FAILURE",
                "reason": pullrequest.message,
                "status_code": None,
                "pullrequest_url": None
            }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            return
        else:
            pass

        pullrequest.errors = 0
        pullrequest.number = j['id']
        pullrequest.url = j['links']['html']['href']
        pullrequest.diff_url = j['links']['diff']['href']

        if pullrequest.url == None or pullrequest.diff_url == None or pullrequest.number == None:
            pullrequest.message = "Submitted PR but faild to obtain details due to missng entries." 
            sys.stderr.write("Failed to obtain url, diff_url or number from PR response.\n")
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text)
            d = {
                "operation": "TranslationUpload",
                "results": "SUCCESS",
                "reason": pullrequest.message,
                "status_code": r.status_code,
                "pullrequest_url": None
            }
            sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))
            return

        d = {
            "operation": "TranslationUpload",
            "results": "SUCCESS",
            "reason": pullrequest.message,
            "status_code": r.status_code,
            "pullrequest_url": pullrequest.url
        }
        sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))

    def _generate_pullrequest_description(self, pullrequest_description, list_commited_files):
        return '* ' + pullrequest_description + '\n\n* Translation Process Automation generated line (DO NOT EDIT): [' + ','.join(list_commited_files) + ']' 

    def _adjust_staged_translation(self, branch_name, list_commit_files):
        descriptions = []
        if not self._get_open_pullrequest_description(descriptions):
            return False

        staged = [] 
        super(BitbucketRepository, self).get_staged_file(branch_name, staged)
        if len(staged) == 0:
            return False

        undo = []
        for s in staged:
            keep = True
            for ent in descriptions:
                if s in ent:
                    undo.append(s)
                    keep = False
                    break
            if keep:
                list_commit_files.append(s)

        if len(undo) == 0:
            sys.stdout.write("No translation files in opened PRs.\n")
            return True
        else:
            sys.stdout.write("# of translation files in opened PRs: {}.\n".format(len(undo)))
            for ent in undo:
                sys.stdout.write("Open: {}\n".format(ent))

        return super(BitbucketRepository, self).revert_translation(branch_name, undo)

    def _get_pullrequest(self, url):
        headers = {'Content-Type': 'application/json'}
        try:
            r =  requests.get(url, auth=(self._git_username, self._git_userpasswd), headers=headers)
        except ConnectionError as e:
            return None
        else:
            if r.status_code != 200:
                sys.stderr.write(r.text)
                return None
            else:
                return r.text

    def _get_open_pullrequest_description(self, descriptions):
        if not self._bitbucket_creds_set():
            if not self._set_bitbucket_creds():
                return None

        success = True
        done = False
        url = 'https://bitbucket.org/api/2.0/repositories/' + self._repository_owner + '/' + self._repository_name + '/pullrequests?state=OPEN'

        while not done:
            pr = self._get_pullrequest(url)
            if not pr:
                success = False
                done = True
                break

            try:
                j = json.loads(pr, object_pairs_hook=OrderedDict)
            except ValueError as e:
                sys.stderr.write("{}\n".format(e))
                success = False
                done = True
                break
            else:
                n = j["pagelen"]
                if 'next' in j:
                    url = j['next']
                else:
                    done = True
                try:
                    for i in range (0, n):
                        descriptions.append(j['values'][i]['description'])
                except IndexError:
                    # this is raised when actual number of entries is fewer than pagelen.
                    # so, this is not success = False condition
                    done = True

        return success

