import sys
import os
import difflib
import filecmp
import re
import datetime
from shutil import copyfile
from sh import git, ErrorReturnCode

import commands as git

class GitRepository():
    def __init__(self, repository_url, repository_owner, repository_name, branch_name, creds=None):
        self._repository_url = repository_url
        self._repository_owner = repository_owner
        self._repository_name = repository_name
        self._repository_branch_name = branch_name
        self._local_repo_dir = os.path.join('./', self._repository_name)

        if creds:
            self._git_username = creds.get_username() 
            self._git_userpasswd = creds.get_userpasswd()
            self._git_useremail = creds.get_useremail()
            self._git_userfullname = creds.get_user_fullname()
            self._git_creds_set = True
        else:
            self._git_username = str() 
            self._git_userpasswd = str()
            self._git_useremail = str()
            self._git_userfullname = str()
            self._git_creds_set = False

    def get_user_name(self):
        return self._git_username

    def get_user_passwd(self):
        return self._git_userpasswd

    def get_repository_name(self):
        return self._repository_name

    def get_repository_owner(self):
        return self._repository_owner

    def get_repository_url(self):
        return self._repository_url

    def get_repository_branch_name(self):
        return self._repository_branch_name

    def get_local_resource_path(self, resource_path):
        return os.path.join(self._local_repo_dir, resource_path)

    def git_creds_set(self):
        return self._git_creds_set

    def set_git_creds(self, creds):
        self._git_username = creds.get_username() 
        self._git_userpasswd = creds.get_userpasswd()
        self._git_useremail = creds.get_useremail()
        self._git_userfullname = creds.get_user_fullname()
        self._git_creds_set = True

    def get_creds(self):
        creds = {}
        creds['username'] = self._git_username
        creds['userpasswd'] = self._git_userpasswd
        creds['useremail'] = self._git_useremail
        creds['userfullname'] = self._git_userfullname
        return creds

    def _pull(self):
        work_branch = self._repository_branch_name
        ret = git.get_current_branch_name(self._repository_name)
        if (not ret.succeeded) or (not ret.output):
            sys.stderr.write("Failed to get current branch name.\n")
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            sys.stderr.write("Failed to pull: '{}'.\n".format(self._repository_name))
            return False
        current_branch = ret.output

        if work_branch != current_branch:
            sys.stdout.write("Local repo branch: Exprected: '{}', Current: '{}'.\n".format(work_branch, current_branch))
            ret = git.checkout_branch(self._repository_name, work_branch)
            if ret.succeeded:
                sys.stdout.write("Switched branch: '{}'.\n".format(work_branch))
            else:
                sys.stderr.write("Failed to switch branch: '{}'.\n".format(work_branch))
                sys.stderr.write("Reason: '{}'.\n".format(ret.message))
                sys.stderr.write("Failed to pull: '{}'.\n".format(self._repository_name))
                return False

        sys.stdout.write("Start pulling...\n")
        ret =  git.pull(self._repository_name)
        if ret.succeeded:
            sys.stdout.write("Pulled: '{}' ('{}').\n".format(self._repository_name, work_branch))
            return True
        else:
            sys.stderr.write("Failed to pull: '{}' ('{}').\n".format(self._repository_name, work_branch))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

    def _clone(self, repository_url_with_creds_embedded):
        sys.stdout.write("Start cloning...\n")
        if repository_url_with_creds_embedded:
            url = repository_url_with_creds_embedded
        else:
            url = self._repository_url
        ret = git.clone_branch(url, self._repository_branch_name, self._git_username, self._git_userpasswd)
        if ret.succeeded:
            sys.stdout.write("Cloned: '{}' ('{}').\n".format(url, self._repository_branch_name))
            return True
        else:
            sys.stderr.write("Failed to clone: '{}' ('{}').\n".format(url, self._repository_branch_name))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

    def isfile(self, file_path):
        """ Return True if given file path exists in local repository.
        """
        path = os.path.join(self._local_repo_dir, file_path)
        return os.path.isfile(path)

    def clone(self, repository_url_with_creds_embedded=None):
        """ Clone if local repository exists. Pull, otherwise.
        """
        if os.path.isdir(self._local_repo_dir):
            sys.stdout.write("Local repository exists: {}\n".format(self._local_repo_dir))
            return  self._pull()
        else:
            return self._clone(repository_url_with_creds_embedded)

    def _update_translation(self, translation_import):
        orig_path = os.path.join(self._repository_name, translation_import['translation_path'])
        if not os.path.isfile(orig_path):
            sys.stderr.write("Expected translation file does not exist in local repository: '{}'.\n".format(orig_path))
            return False

        new_path = translation_import['local_path']
        if not os.path.isfile(new_path):
            sys.stderr.write("Updated traslation NOT found: '{}'.\n".format(new_path))
            return False

        if filecmp.cmp(orig_path, new_path):
            sys.stdout.write("Translation file does not contain any changes.\n")
            return False

        self._display_diff(orig_path, new_path)
        copyfile(new_path, orig_path)
        sys.stdout.write("Updated translation in local repository.\n")
        return True

    def update_files_in_new_branch(self, list_translation_import):
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
            sys.stdout.write("Importing '{}'...\n".format(t['local_path']))
            if not self._is_file_clean(t):
                sys.stderr.write("Skipped staging file. The file is dirty: '{}'.\n".format(t['translation_path'])) 
                continue
            if not self._update_translation(t):
                continue
            self._add_file(t['translation_path'], staged)

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
        ret = git.checkout_branch(self._repository_name, self._repository_branch_name)
        if ret.succeeded:
            return True
        else:
            sys.stderr.write("Failed to checkout branch: '{}'.\n".format(self._repository_branch_name))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

    def _checkout_feature_branch(self):
        new_branch_name = 'TPA_{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        ret = git.checkout_new_branch(self._repository_name, new_branch_name, self._repository_branch_name)
        if ret.succeeded:
            return new_branch_name
        else:
            sys.stderr.write("Failed to checkout feature branch: '{}'.\n".format(new_branch_name))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return None

    def _delete_local_branch(self, branch_name):
        ret = git.delete_local_branch(self._repository_name, branch_name)
        if ret.succeeded:
            return True
        else:
            sys.stderr.write("Failed to delete local branch: '{}'.\n".format(branch_name))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

    def _commit(self):
        if not (self._git_username and self._git_userpasswd):
            sys.stderr.write("BUG: git username and userpasswd need to be set before calling GitRepository._commit().\n")
            return False
 
        ret = git.set_config_username(self._repository_name, self._git_userfullname)
        if not ret.succeeded:
            sys.stderr.write("Failed to set git config username: '{}'.\n".format(self._git_userfullname))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

        ret = git.set_config_useremail(self._repository_name, self._git_useremail)
        if not ret.succeeded:
            sys.stderr.write("Failed to set git config useremail: '{}'.\n".format(self._git_useremail))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

        ret = git.commit(self._repository_name, "Translation updates.")
        if ret.succeeded:
            return True
        else:
            sys.stderr.write("Failed to commit.\n")
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

    def _add_file(self, translation_path, list_staged_path):
        ret = git.not_staged_for_commit(self._repository_name, translation_path)
        if not ret.succeeded:
            sys.stderr.write("Failed to check staged or not: {}.\n".format(translation_path))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return
        if not ret.output:
            # this is a bug since the changes have been ensured before translation file was copied to local repository.
            sys.stderr.write("Translation file is already staged: '{}'.\n".format(translation_path))
            return

        ret = git.add_file(self._repository_name, translation_path)
        if ret.succeeded:
            list_staged_path.append(translation_path)
        else:
            sys.stderr.write("Failed to add file: '{}'.\n".format(translation_path))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))

    def _is_file_clean(self, translation_import):
        ret = git.get_status_porcelain(self._repository_name)
        if not ret.succeeded:
            sys.stderr.write("Failed to get status: '{}'.\n".format(self._repository_name))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

        for line in ret.output:
            if translation_import['translation_path'] in line.strip().rstrip():
                return False
        return True

    def set_remote_url(self, url):
        ret = git.set_remote_url(self._repository_name, url)
        if ret.succeeded:
            return True
        else:
            sys.stderr.write("Failed to set remote url: '{}'\n".format(url))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

    def push_branch(self, branch_name):
        if not (self._git_username and self._git_userpasswd):
            sys.stderr.write("BUG: git username and userpasswd need to be set before calling GitRepository.push_branch().\n")
            return False

        ret = git.push_branch_set_upstream(self._repository_name, branch_name)
        if ret.succeeded:
            return True
        else:
            sys.stderr.write("Failed to push branch: '{}'\n".format(branch_name))
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False
        
    def _display_diff(self, file1, file2):
        with open(file1, 'r') as fi1, open(file2, 'r') as fi2:
            diff = difflib.unified_diff(fi1.readlines(), fi2.readlines())
            sys.stdout.write("-------- starting diff --------\n")
            for line in diff:
                sys.stdout.write(line)
            sys.stdout.write("-------- ending diff --------\n")

    def _revert_file_in_commit(self, branch_name, commit, file_path):
        revert_commit_message = "Reverted."
        ret = git.revert_commit(self._repository_name, commit, file_path, revert_commit_message)
        if not ret.succeeded:
            sys.stderr.write("Failed to revert commit '{}' for '{}'\n".format(commit, file_path))
            sys.stderr.write("Reason: '{}'\n".format(ret.message))
            return False

        # anything to commit ?
        #remaining_staged_files = self.get_staged_file(branch_name)
        #if len(remaining_staged_files) < 1:
        #    return True

        sys.stderr.write("@@@ Reverted commit: '{}'\n".format(commit))

        ret = git.reset_soft(self._repository_name, 'HEAD~1')
        if ret.succeeded:
            return True
        else:
            sys.stderr.write("Failed to reset to '{}'\n".format(file_path))
            sys.stderr.write("Reason: '{}'\n".format(ret.message))
            return False

    def _revert_files(self, branch_name, paths):
        errors = 0
        for path in paths:
            ret = git.get_commit(self._repository_name, path)
            if not ret.succeeded:
                errors += 1
                sys.stdout.write("Faild to get a commit for file: '{}'.\n".format(path))
                continue

            commits = ret.output
            if len(commits) == 1:
                if not self._revert_file_in_commit(branch_name, commits[0], path):
                    errors += 1
                else:
                    sys.stdout.write("Reverted: '{}'.\n".format(path))
            elif len(commits) == 0:
                errors += 1
                sys.stderr.write("Cannot find commit for: '{}'.\n".format(path))
            else:
                errors += 1
                sys.stderr.write("Too many commits for: '{}'.\n".format(path))
                sys.stderr.write("'{}'\n".format(commits))
        return errors

    def revert_files_in_branch(self, branch_name, list_of_file_to_revert):
        ret = git.get_current_branch_name(self._repository_name)
        if (not ret.succeeded) or (not ret.output):
            sys.stderr.write("Failed to get current branch name.\n")
            sys.stderr.write("Reason: '{}'.\n".format(ret.message))
            return False

        current_branch = ret.output
        branch_switched = False
        if current_branch != branch_name:
            ret = git.checkout_branch(self._repository_name, branch_name)
            if ret.succeeded:
                branch_switched = True
                sys.stdout.write("Switched branch: from '{}' to '{}'.\n".format(current_branch, branch_name))
            else:
                sys.stderr.write("Failed to switch branch: from '{}' to '{}'.\n".format(current_branch, branch_name))
                sys.stderr.write("Reason: '{}'.\n".format(ret.message))
                return False

        errors = self._revert_files(branch_name, list_of_file_to_revert)

        if branch_switched:
            ret = git.checkout_branch(self._repository_name, current_branch)
            if not ret.succeeded:
                sys.stderr.write("Failed to switch branch: from '{}' to '{}'\n".format(branch_name, current_branch))

        if errors == 0:
            return True
        else:
            return False


    def get_staged_file(self, branch_name):
        
        # FIXME --- never pick up resource file !!!

        # FIXME --- never pick up duplicates !!!

        ret = git.get_staged_file(self._repository_name, branch_name)
        if not ret.succeeded:
            sys.stderr.write("Failed to get staged file in branch: '{}'\n".format(branch_name))
        return ret.output

