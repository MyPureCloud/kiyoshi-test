import sys, os, re, requests, json
from requests.exceptions import ConnectionError
from collections import OrderedDict
from GitCredsConfigurationClass import GitCredsConfiguration
from GitRepositoryClass import GitRepository, GitFileImport

class BitbucketRepository(GitRepository):
    def __init__(self, repository_url, repository_owner, repository_name, branch_name):
        super(BitbucketRepository, self).__init__(repository_url, repository_owner, repository_name, branch_name)
        self._BITBUCKET_CREDS_FILE = 'bitbucket_creds.yaml'

    def get_repository_name(self):
        return super(BitbucketRepository, self).get_repository_name()

    def get_repository_owner(self):
        return super(BitbucketRepository, self).get_repository_owner()

    def get_repository_platform(self):
        return 'bitbucket' 

    def get_repository_url(self):
        return super(BitbucketRepository, self).get_repository_url()

    def get_current_branch_name(self):
        return super(BitbucketRepository, self).get_current_branch_name()

    def get_local_resource_path(self, resource_path):
        return super(BitbucketRepository, self).get_local_resource_path(resource_path)

    def _bitbucket_creds_set(self):
        return super(BitbucketRepository, self).git_creds_set()

    def _set_bitbucket_creds(self):
        if not os.path.isfile(self._BITBUCKET_CREDS_FILE):
            sys.stderr.write("Bitbucket creds config file NOT found: {}.\n".format(self._BITBUCKET_CREDS_FILE))
            return False

        t = GitCredsConfiguration()
        if not t.parse(self._BITBUCKET_CREDS_FILE):
            sys.stderr.write("Failed to parse Github creds config file: {}\n".format(self._BITBUCKET_CREDS_FILE))
            return False
        else:
            super(BitbucketRepository, self).set_git_creds(t.get_username(), t.get_userpasswd(), t.get_useremail(), t.get_user_fullname())
            return True

    def isfile(self, file_path):
        return super(BitbucketRepository, self).isfile(file_path)

    def clone(self):
        return super(BitbucketRepository, self).clone()

    def import_translation(self, list_translation_import):
        if not self._bitbucket_creds_set():
            if not self._set_bitbucket_creds():
                sys.stderr.write("Failed to set git creds. Nothing was imported.")
                return None
        return super(BitbucketRepository, self).import_translation(list_translation_import)

    def _set_remote_url(self):
        user_name = super(BitbucketRepository, self).get_user_name()
        user_passwd = super(BitbucketRepository, self).get_user_passwd()
        repository_owner = super(BitbucketRepository, self).get_repository_owner()
        repository_name = super(BitbucketRepository, self).get_repository_name()
        url = "https://{}:{}@bitbucket.org/{}/{}.git".format(user_name, user_passwd, repository_owner, repository_name)
        return super(BitbucketRepository, self).set_remote_url(url)

    def submit_pullrequest(self, pullrequest):
        list_commited_files = []
        if not self._adjust_staged_translation(pullrequest.branch_name, list_commited_files):
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
            for ent in list_commited_files:
                sys.stdout.write("Committed: '{}'\n".format(ent))

        if not super(BitbucketRepository, self).push_branch(pullrequest.branch_name):
            pullrequest.errors += 1
            pullrequest.submitted = False
            pullrequest.message = "Failed to push feature branch. PR NOT submitted."
            return

        if not self._bitbucket_creds_set():
            if not self._set_bitbucket_creds():
                pullrequest.errors += 1
                pullrequest.submitted = False
                pullrequest.message = "Failed to read bitbucket creds file. PR NOT submitted."
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

