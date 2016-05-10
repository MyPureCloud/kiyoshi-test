import sys, os, re, requests, json
from requests.exceptions import ConnectionError
from collections import OrderedDict
from GithubCredsConfigurationClass import GithubCredsConfiguration
from GitRepositoryClass import GitRepository, GitFileImport
#from ResourceRepositoryClass import PullRequest

class GithubRepository(GitRepository):
    def __init__(self, repository_url, repository_owner, repository_name, branch_name):
        super(GithubRepository, self).__init__(repository_url, repository_owner, repository_name, branch_name)
        self._GITHUB_CREDS_FILE = 'github_creds.yaml'

    def get_repository_name(self):
        return super(GithubRepository, self).get_repository_name()

    def get_repository_owner(self):
        return super(GithubRepository, self).get_repository_owner()

    def get_repository_platform(self):
        return 'github' 

    def get_repository_url(self):
        return super(GithubRepository, self).get_repository_url()

    def get_current_branch_name(self):
        return super(GithubRepository, self).get_current_branch_name()

    def get_local_resource_path(self, resource_path):
        return super(GithubRepository, self).get_local_resource_path(resource_path)

    def _github_creds_set(self):
        return super(GitRepsitory, self).get_creds_set()

    def _set_github_creds(self):
        if not os.path.isfile(self._GITHUB_CREDS_FILE):
            sys.stderr.write("Github creds config file NOT found: {}.\n".format(self._GITHUB_CREDS_FILE))
            return False

        t = GithubCredsConfiguration()
        if not t.parse(self._GITHUB_CREDS_FILE):
            sys.stderr.write("Failed to parse Github creds config file: {}\n".format(self._GITHUB_CREDS_FILE))
            return False
        else:
            super(GithubRepository, self).set_git_creds(t.get_username(), t.get_userpasswd(), t.get_useremail(), t.get_user_fullname())
            return True

    def isfile(self, file_path):
        return super(GithubRepository, self).isfile(file_path)

    def clone(self):
        return super(GithubRepository, self).clone()

    def import_translation(self, list_translation_import):
        return super(GithubRepository, self).import_translation(list_translation_import)

    def _set_remote_url(self):
        user_name = super(GithubRepository, self).get_uesr_name()
        user_passwd = super(GithubRepository, self).get_uesr_passwd()
        repository_owner = super(GithubRepository, self).get_repository_owner()
        repository_name = super(GithubRepository, self).get_repository_name()
        url = "https://{}:{}@github.com/{}/{}.git".format(user_name, user_passwd, repository_owner, repository_name)
        return super(GithubRepository, self).set_remote_url(url)

    def submit_pullrequest(self, pullrequest):
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

        if not super(GithubRepository, self).push_branch(pullrequest.branch_name):
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
           'body': pullrequest.description,
           'head': pullrequest.branch_name,
           'base': self._repository_branch_name}, ensure_ascii=False)
        try:
            r =  requests.post(url, auth=(self._github_username, self._github_userpasswd), data=payload)
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

    def submit_pullrequestORIG(self, github_pullrequest_obj):
        feature_branch_name = github_pullrequest_obj.branch_name
        pullrequest_title = github_pullrequest_obj.title

        list_commited_files = []
        if not self._adjust_staged_translation(feature_branch_name, pullrequest_title, list_commited_files):
            github_pullrequest_obj.errors += 1
            github_pullrequest_obj.message = "Failed to adjust staged translation. PR NOT submitted."
            return

        if len(list_commited_files) == 0:
            github_pullrequest_obj.errors = 0
            github_pullrequest_obj.submitted = False
            github_pullrequest_obj.message = "No staged files. PR NOT submitted."
            return
        else:
            sys.stdout.write("Updated files...\n")
            for ent in list_commited_files:
                sys.stdout.write("- {}\n".format(ent))

        if not super(GithubRepository, self).push_branch(feature_branch_name):
            github_pullrequest_obj.errors += 1
            github_pullrequest_obj.submitted = False
            github_pullrequest_obj.message = "Failed to push feature branch. PR NOT submitted."
            return

        if not self._github_creds_set():
            if not self._set_github_creds():
                github_pullrequest_obj.errors += 1
                github_pullrequest_obj.submitted = False
                github_pullrequest_obj.message = "Failed read Github creds file. PR NOT submitted."
                return

        pullrequest_description = self._generate_pullrequest_description(github_pullrequest_obj.description, list_commited_files)
        url = 'https://api.github.com/repos/' + self._repository_owner + '/' + self._repository_name + '/pulls'
        payload = json.dumps({
           'title': pullrequest_title,
           'body': pullrequest_description,
           'head': feature_branch_name,
           'base': self._repository_branch_name}, ensure_ascii=False)
        try:
            r =  requests.post(url, auth=(self._github_username, self._github_userpasswd), data=payload)
        except ConnectionError as e:
            github_pullrequest_obj.errors += 1
            github_pullrequest_obj.submitted = False
            github_pullrequest_obj.message = "Failed to submit PR. Reason: {}".format(e)
            return
        else:
            pass

        github_pullrequest_obj.status_code = r.status_code
        if not (r.status_code == 200 or r.status_code == 201):
            github_pullrequest_obj.submitted = False
            github_pullrequest_obj.message = "Failed to submit PR. Status code: {}".format(r.status_code)
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text)
            return

        github_pullrequest_obj.submitted = True
        try:
            j = json.loads(r.text, object_pairs_hook=OrderedDict)
        except ValueError as e:
            # PR was succeeded but cannot supply info.
            github_pullrequest_obj.errors += 1
            github_pullrequest_obj.message = "Submitted PR but failed to obtain PR details." 
            sys.stderr.write("Failed read pullrequest result as json. Reason: {}\n".format(e))
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text)
            return
        else:
            pass

        github_pullrequest_obj.errors = 0
        for ent in j.items():
            if ent[0] == 'url':
                github_pullrequest_obj.url = ent[1]
            elif ent[0] == 'diff_url':
                github_pullrequest_obj.diff_url =  ent[1]
            elif ent[0] == 'number':
                github_pullrequest_obj.number = ent[1]

        if github_pullrequest_obj.url == None or github_pullrequest_obj.diff_url == None or github_pullrequest_obj.number == None:
            github_pullrequest_obj.message = "Submitted PR but faild to obtain details due to missng entries." 
            sys.stderr.write("Failed to obtain url, diff_url or number from PR response.\n")
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text)
            return

        if github_pullrequest_obj.assignee:
            if self._update_assignee(github_pullrequest_obj.number, github_pullrequest_obj.assignee):
                github_pullrequest_obj.message = "Submitted PR and updated assignee." 
            else:
                github_pullrequest_obj.message = "Submitted PR with no assignee." 
        else:
            github_pullrequest_obj.message = "Submitted PR with no assignee." 

    def _update_assignee(self, issue_number, assignee):
        url = 'https://api.github.com/repos/' + self._repository_owner + '/' + self._repository_name + '/issues/' + str(issue_number)
        payload = json.dumps({'assignee': assignee}, ensure_ascii=False)
        try:
            r =  requests.patch(url, auth=(self._github_username, self._github_userpasswd), data=payload)
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
        super(GithubRepository, self).get_staged_file(branch_name, staged)
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
                sys.stdout.write("- {}\n".format(ent))

        return super(GithubRepository, self).revert_translation(branch_name, undo)

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

