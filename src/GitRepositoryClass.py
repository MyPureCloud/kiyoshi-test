import sys, os, difflib, filecmp, re, datetime, abc
from shutil import copyfile
from sh import git, ErrorReturnCode

class GitFileImport:
    def __init__(self, repo_file_path=str(), import_file_path=str()):
        self.repo_file_path = repo_file_path
        self.import_path = import_file_path
    
class GitRepository(object):
    __metaclass__ = abc.ABCMeta
    def __init__(self, repository_url, repository_owner, repository_name, branch_name):
        self._repository_url = repository_url
        self._repository_owner = repository_owner
        self._repository_name = repository_name
        self._repository_branch_name = branch_name
        self._local_repo_dir = os.path.join('./', self._repository_name)
        self._GITHUB_CREDS_FILE = 'github_creds.yaml'
        self._git_username = str()
        self._git_userpasswd = str()
        self._git_useremail = str()
        self._git_user_fullname = str()
        self._git_creds_set = False
        self._errors = 0

    def get_repository_name(self):
        return self._repository_name

    def get_repository_owner(self):
        return self._repository_owner

    @abc.abstractmethod
    def get_repository_platform(self):
        sys.stderr.write("Abstract method GitRepository.get_repository_platrom() was called.\n")
        return 'git' 

    def get_repository_url(self):
        return self._repository_url

    def get_current_branch_name(self):
        try:
            output = git('-C', self._repository_name, 'rev-parse', '--abbrev-ref', 'HEAD')
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return None
        else:
            return output.strip().rstrip()

    def get_local_resource_path(self, resource_path):
        return os.path.join(self._local_repo_dir, resource_path)

    def git_creds_set(self):
        return self._git_creds_set

    def set_git_creds(self, user_name, user_passwd, uesr_email, user_fullname):
        self._git_username = user_name
        self._git_userpasswd = user_passwd
        self._git_useremail = user_email
        self._git_user_fullname = user_fullname
        self._git_creds_set = True

    def _pull(self):
        work_branch = self._repository_branch_name
        current_branch = self.get_current_branch_name()
        if not current_branch:
            return False
        if work_branch != current_branch:
            sys.stdout.write("Local repo branch: Exprected: {}, Current: {}.\n".format(work_branch, current_branch))
            try:
                git('-C', self._repository_name, 'checkout', work_branch)
            except ErrorReturnCode as e:
                self._errors += 1
                sys.stderr.write("{}\n".format(str(e)))
                return False
            else:
                sys.stdout.write("Checked out branch: {}.\n".format(work_branch))

        try: 
            git('-C', self._repository_name, 'pull')
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            sys.stdout.write("Pulled: {} {}\n".format(self._repository_branch_name, self._repository_url))
            return True

    def _clone(self):
        try:
            git('clone', self._repository_url, '-b', self._repository_branch_name)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("Failed to clone repo.\n")
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            sys.stdout.write("Cloned: {} {}\n".format(self._repository_branch_name, self._repository_url))
            return True

    def isfile(self, file_path):
        path = os.path.join(self._local_repo_dir, file_path)
        return os.path.isfile(path)

    def clone(self):
        if os.path.isdir(self._local_repo_dir):
            return  self._pull()
        else:
            return self._clone()

    def import_translation(self, list_translation_import):
        """ Returns feature branch name in local repository when importing files in 
            the given 'list_translation_import' makes any updates to the repository,
            or None othewise.
        """
        staged = []
        feature_branch_name = self._checkout_feature_branch()
        if not feature_branch_name:
            return None

        # try staging translation as much as possible b/c good ones can be PRed.
        for t in list_translation_import:
            sys.stdout.write("Importing {}...\n".format(t.import_path))
            if not self._is_translation_clean(t):
                sys.stderr.write("Skipped. The file is dirty.\n") 
                continue
            if not self._update_translation(t):
                continue
            self._stage_translation(t.translation_path, staged)

        if len(staged) == 0:
            self._checkout_work_branch()
            self._delete_local_branch(feature_branch_name)
            return None

        if not self._commit():
            self._undo_staged_translation(staged)
            return None

        if not self._checkout_work_branch():
            return None

        return feature_branch_name

    def _undo_staged_translation(self, list_of_staged_translation):
        print("@@@ NIY: _undo_staged_translation")
        pass

    def _checkout_work_branch(self):
        return self._checkout_branch(self._repository_branch_name)

    def _checkout_branch(self, branch_name):
        try:
            git('-C', self._repository_name, 'checkout',  branch_name)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            return True

    def _checkout_feature_branch(self):
        branch_name = 'TPA_{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        try:
            git('-C', self._repository_name, 'checkout', '-b', branch_name, self._repository_branch_name)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return None
        else:
            return branch_name

    def _delete_local_branch(self, branch_name):
        try:
            git('-C', self._repository_name, 'branch', '-d', branch_name)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            return True

    def _commit(self):
        if not (self._github_username and self._github_userpasswd):
            if not self._set_github_creds():
                return False
 
        try:
            git('-C', self._repository_name, 'config', 'user.name', self._github_user_fullname)
            git('-C', self._repository_name, 'config', 'user.email', self._github_useremail)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("Failed to set git username or useremail. Reason: {}\n".format(str(e)))
            return False
        else:
            pass

        try:
            git('-C', self._repository_name, 'commit', '-m', 'Translation updates.')
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            return True

    def _not_staged_for_commit(self, file_path):
        try:
            output = git('-C', self._repository_name, 'status')
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            found = False
            regex = re.compile(r'modified:\s*{}'.format(file_path))
            for line in output:
                line = line.strip().rstrip()
                m = regex.search(line)
                if m:
                    found = True
                    break
            return found

    def _stage(self, file_path):
        try:
            git('-C', self._repository_name, 'add', file_path)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("Failed to stage file: {}.\n".format(file_path))
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            sys.stdout.write("Staged translation in local repository.\n")
            return True

    def _stage_translation(self, translation_path, list_staged_path):
        work_branch = self._repository_branch_name
        current_branch = self.get_current_branch_name()
        if not current_branch:
            return
        if not work_branch != current_branch:
            # this is a bug since correct branch should be set when the repository is cloned/pulled.
            self._errors += 1
            sys.stderr.write("Local repo branch: Exprected: {}, Current: {}.\n".format(work_branch, current_branch))
            return

        if not self._not_staged_for_commit(translation_path):
            # this is a bug since the changes have been ensured before translation file was copied to local repository.
            self._errors += 1
            sys.stderr.write("Translation file is not listed as 'not stated for commit': {}.\n".format(translation_path))
            return

        if self._stage(translation_path):
            list_staged_path.append(translation_path)

    def _is_translation_clean(self, translation_import_obj):
        try:
            output = git('-C', self._repository_name, 'status', '--porcelain')
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}".format(str(e)))
            return False
        else:
            found = False
            for line in output:
                if translation_import_obj.translation_path in line.strip().rstrip():
                    self._errors += 1
                    sys.stderr.write("{}\n".format(line.strip().rstrip()))
                    found = True
                    break
            
            if not found:
                return True
            else:
                return False

    def set_remote_url(self, url):
        try:
            git('-C', self._repository_name, 'remote', 'set-url', 'origin', url)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            return True

    def push_branch(self, branch_name):
        if not (self._github_username and self._github_userpasswd):
            if not self._set_github_creds():
                sys.stderr.write("Failed to push feature branch b/c setting github creds failed.\n")
                return False

        if not self._set_remote_url():
            sys.stderr.write("Failed to push feature branch b/c setting remote url failed.\n")
            return False

        try:
            # this will ask username/password
            git('-C', self._repository_name, 'push', '--set-upstream', 'origin', branch_name)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            return True

    def update_translation(self, translation_import_obj):
        orig_path = os.path.join(self._repository_name, translation_import_obj.translation_path)
        if not os.path.isfile(orig_path):
            self._errors += 1
            sys.stderr.write("Expected translation file does not exist in local repository: {}\n".format(orig_path))
            return False

        new_path = translation_import_obj.import_path
        if not os.path.isfile(orig_path):
            self._errors += 1
            sys.stderr.write("Updated traslation NOT found: {}\n".format(new_path))
            return False

        if filecmp.cmp(orig_path, new_path):
            sys.stdout.write("Translation file does not contain any changes.\n")
            return False

        self._display_diff(orig_path, new_path)

        copyfile(new_path, orig_path)
        sys.stdout.write("Updated translation in local repository.\n")

        return True

    def display_diff(self, file1, file2):
        with open(file1, 'r') as fi1, open(file2, 'r') as fi2:
            diff = difflib.unified_diff(fi1.readlines(), fi2.readlines())
            sys.stdout.write("-------- starting diff --------\n")
            for line in diff:
                sys.stdout.write(line)
            sys.stdout.write("-------- ending diff --------\n")

    @abc.abstractmethod
    def submit_pullrequest(self, github_pullrequest_obj):
        sys.stderr.write("Abstract method GitRepository.submit_pullrequest() was called.\n")

    def _get_commit(self, file_path):
        try:
            output = git('-C', self._repository_name, 'log', 'master..', '--pretty=format:%H', file_path)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return None
        else:
            commit = []
            for s in output:
                # as output from sh contains VT100 escape sequences,
                # extract only sha1 out of it.
                c = '{}'.format(s).strip().rstrip()
                regex = re.compile(r'[a-z0-9]{40}')
                m = regex.search(c)
                if m:
                    commit.append(m.group(0))
            return commit

    def revert_translation(self, branch_name, list_of_file_to_revert):
        current_branch = self.get_current_branch_name()
        if not current_branch:
            return False
        branch_switched = False
        if current_branch != branch_name:
            try:
                git('-C', self._repository_name, 'checkout', branch_name)
            except ErrorReturnCode as e:
                self._errors += 1
                sys.stderr.write("{}\n".format(str(e)))
                return False
            else:
                branch_switched = True
                pass

        errors = 0
        for s in list_of_file_to_revert:
            commit = self._get_commit(s)
            if not commit:
                # FIXME --- this is actually error condition.
                continue
            else:
                if len(commit) == 0:
                    errors += 1
                    sys.stderr.write("Cannot find commit for: {}.\n".format(s))
                if len(commit) == 1:
                    if not self._revert_commit(commit, s):
                        errors += 1
                    else:
                        sys.stdout.write("Reverted: {}.\n".format(s))
                else:
                    errors += 1
                    sys.stderr.write("Cannot revert commit. File in multiple commits: {}.\n".format(s))
                    sys.stderr.write("'{}'\n".format(commit))

        if branch_switched:
            try:
                git('-C', self._repository_name, 'checkout', current_branch)
            except ErrorReturnCode as e:
                errors += 1
                sys.stderr.write("{}\n".format(str(e)))
            else:
                pass
        
        if errors == 0:
            return True
        else:
            self._errors += errors
            return False

    def _revert_commit(self, commit, file_path):
        try:
            git('-C', self._repository_name, 'checkout', commit, file_path)
        except ErrorReturnCode as e:
            sys.stderr.write("{}\n".format(str(e)))
            return False
        else:
            return True 

    # TODO --- return list
    def get_staged_file(self, branch_name, list_staged):
        
        # FIXME --- never pick up resource file !!!

        # FIXME --- never pick up duplicates !!!

        try:
            output = git('-C', self._repository_name, '--no-pager', 'log', '--name-status', '--oneline', 'HEAD..' + branch_name)
        except ErrorReturnCode as e:
            self._errors += 1
            sys.stderr.write("{}\n".format(str(e)))
            return
        else:
            regex = re.compile(r'^M\s*(.+)$')
            for s in output:
                m = regex.match(s)
                if m:
                    if not m.group(0) in list_staged:
                        list_staged.append(m.group(1))

