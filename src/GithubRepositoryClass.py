import sys, os, re, requests, json
from requests.exceptions import ConnectionError
from collections import OrderedDict
from GitCredsConfigurationClass import GitCredsConfiguration
from GitRepositoryClass import GitRepository, GitFileImport
from ResourceRepositoryClass import ResourceRepository

class GithubRepository(ResourceRepository, GitRepository):
    def __init__(self, config, log_dir):
        self._GITHUB_CREDS_FILE = 'github_creds.yaml'
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

    def _github_creds_set(self):
        return self.git_creds_set()

    def _set_github_creds(self):
        if not os.path.isfile(self._GITHUB_CREDS_FILE):
            sys.stderr.write("Github creds config file NOT found: {}.\n".format(self._GITHUB_CREDS_FILE))
            return False

        t = GitCredsConfiguration()
        if not t.parse(self._GITHUB_CREDS_FILE):
            sys.stderr.write("Failed to parse Github creds config file: {}\n".format(self._GITHUB_CREDS_FILE))
            return False
        else:
            self.set_git_creds(t.get_username(), t.get_userpasswd(), t.get_useremail(), t.get_user_fullname())
            return True

    def isfile(self, file_path):
        return GitRepository.isfile(self, file_path)

    def clone(self):
        return GitRepository.clone(self)

    def _import_translation(self, list_translation_import):
        if not self._github_creds_set():
            if not self._set_github_creds():
                sys.stderr.write("Failed to set git creds. Nothing was imported.\n")
                return None
        return GitRepository.import_translation(self, list_translation_import)

    def _set_remote_url(self):
        user_name = self.get_user_name()
        user_passwd = self.get_user_passwd()
        repository_owner = self.get_repository_owner()
        repository_name = self.get_repository_name()
        url = "https://{}:{}@github.com/{}/{}.git".format(user_name, user_passwd, repository_owner, repository_name)
        return self.set_remote_url(url)

    def submit_pullrequest(self, pullrequest):
        pullrequest.title = self.config.get_pullrequest_title()
        pullrequest.description = self.config.get_pullrequest_description()
        pullrequest.assignee = self.config.get_pullrequest_assignee()
        self._submit_pullrequest(pullrequest)

    def _submit_pullrequest(self, pullrequest):
        list_commited_files = []
        if not self._adjust_staged_translation(pullrequest.branch_name, pullrequest.title, list_commited_files):
            pullrequest.errors += 1
            pullrequest.submitted = False
            pullrequest.message = "Failed to adjust staged translation. PR NOT submitted."
            return

        if len(list_commited_files) == 0:
            pullrequest.errors = 0
            pullrequest.submitted = False
            pullrequest.message = "No staged files. PR NOT submitted."
            return
        else:
            sys.stdout.write("Updated files...\n")
            for ent in list_commited_files:
                sys.stdout.write("- '{}'\n".format(ent))

        if not GitRepository.push_branch(self, pullrequest.branch_name):
            pullrequest.errors += 1
            pullrequest.submitted = False
            pullrequest.message = "Failed to push feature branch. PR NOT submitted."
            return

        if not self._github_creds_set():
            if not self._set_github_creds():
                pullrequest.errors += 1
                pullrequest.submitted = False
                pullrequest.message = "Failed read Github creds file. PR NOT submitted."
                return

        pullrequest_description = self._generate_pullrequest_description(pullrequest.description, list_commited_files)
        url = 'https://api.github.com/repos/' + self._repository_owner + '/' + self._repository_name + '/pulls'
        payload = json.dumps({
           'title': pullrequest.title,
           'body': pullrequest_description,
           'head': pullrequest.branch_name,
           'base': self._repository_branch_name}, ensure_ascii=False)
        try:
            r =  requests.post(url, auth=(self._git_username, self._git_userpasswd), data=payload)
        except ConnectionError as e:
            pullrequest.errors += 1
            pullrequest.submitted = False
            pullrequest.message = "Failed to submit PR. Reason: '{}'.".format(e)
            return
        else:
            pass

        pullrequest.status_code = r.status_code
        if not (r.status_code == 200 or r.status_code == 201):
            pullrequest.submitted = False
            pullrequest.message = "Failed to submit PR. Status code: '{}'.".format(r.status_code)
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text)
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
            return
        else:
            pass

        pullrequest.errors = 0
        for ent in j.items():
            if ent[0] == 'url':
                pullrequest.url = ent[1]
            elif ent[0] == 'diff_url':
                pullrequest.diff_url =  ent[1]
            elif ent[0] == 'number':
                pullrequest.number = ent[1]

        if pullrequest.url == None or pullrequest.diff_url == None or pullrequest.number == None:
            pullrequest.message = "Submitted PR but faild to obtain details due to missng entries." 
            sys.stderr.write("Failed to obtain url, diff_url or number from PR response.\n")
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text)
            return

        if pullrequest.assignee:
            if self._update_assignee(pullrequest.number, pullrequest.assignee):
                pullrequest.message = "Submitted PR and updated assignee." 
            else:
                pullrequest.message = "Submitted PR with no assignee." 
        else:
            pullrequest.message = "Submitted PR with no assignee." 

    def _update_assignee(self, issue_number, assignee):
        url = 'https://api.github.com/repos/' + self._repository_owner + '/' + self._repository_name + '/issues/' + str(issue_number)
        payload = json.dumps({'assignee': assignee}, ensure_ascii=False)
        try:
            r =  requests.patch(url, auth=(self._git_username, self._git_userpasswd), data=payload)
        except ConnectionError as e:
            sys.stderr.write("Failed to update assignee ({}). Reason: {}\n".format(assignee, e))
            return False
        else:
            if r.status_code == 200 or r.status_code == 201:
                return True
            else:
                sys.stderr.write("Failed to update assignee ({}). Status code: {}\n".format(assignee, r.status_code)) 
                sys.stderr.write("Response context...\n")
                sys.stderr.write(r.text)
                return False

    def _generate_pullrequest_description(self, pullrequest_description, list_commited_files):
        return '* ' + pullrequest_description + '\n\n* Translation Process Automation generated line (DO NOT EDIT): [' + ','.join(list_commited_files) + ']' 

    def _adjust_staged_translation(self, branch_name, pr_title, list_commit_files):
        open_pullrequest_description = []
        if not self._get_open_pullrequest_description(pr_title, open_pullrequest_description):
            return False

        staged = [] 
        GitRepository.get_staged_file(self, branch_name, staged)
        if len(staged) == 0:
            return False

        undo = []
        for s in staged:
            keep = True
            for ent in open_pullrequest_description:
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

        return GitRepository.revert_translation(self, branch_name, undo)

    def _get_pullrequest(self):
        if not self._github_creds_set():
            if not self._set_github_creds():
                return None

        url = 'https://api.github.com/repos/' + self._repository_owner + '/' + self._repository_name + '/pulls'
        try:
            r =  requests.get(url)
        except ConnectionError as e:
            return None
        else:
            if r.status_code != 200:
                self._errors += 1
                sys.stderr.write(r.text)
                return None
            else:
                return r.text

    def _get_open_pullrequest_description(self, pr_title, list_of_open_pullrequest_description):
        pr = self._get_pullrequest()
        if not pr:
            return False

        try:
            j = json.loads(pr, object_pairs_hook=OrderedDict)
        except ValueError as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(e))
            return False
        else:
            for pr in j:
                if pr['state'] == 'open':
                    if pr['title'] == pr_title:
                        list_of_open_pullrequest_description.append(pr['body'])
            else:
                return True


    def get_resource_bundle(self):
        return ResourceRepository.get_resource_bundle(self, self)

    def import_bundles(self, translation_bundles):
        ResourceRepository.add_import_entry(self, translation_bundles)
        if len(self._import_entries) == 0:
            sys.stderr.write("Nothing to import (_import_entries is empty).\n")
            return
        return self._import_translation(self._import_entries)

