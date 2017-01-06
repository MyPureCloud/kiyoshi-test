import os
import difflib
import filecmp
import re
import datetime
from shutil import copyfile
from sh import git, ErrorReturnCode

import logging
logger = logging.getLogger('tpa')

import settings
import commands as git

class GitRepository():
    def __init__(self, repository_url, repository_owner, repository_name, branch_name, creds=None):
        self._repository_url = repository_url
        self._repository_owner = repository_owner
        self._repository_name = repository_name
        self._repository_branch_name = branch_name
        self._local_repo_dir = os.path.join(settings.LOCAL_REPO_DIR, self._repository_name)

        if creds:
            self._git_username = creds.username 
            self._git_userpasswd = creds.userpasswd
            self._git_useremail = creds.useremail
            self._git_userfullname = creds.userfullname
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
        self._git_username = creds.username 
        self._git_userpasswd = creds.userpasswd
        self._git_useremail = creds.useremail
        self._git_userfullname = creds.user_fullname
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
        ret = git.get_current_branch_name(self._local_repo_dir)
        if (not ret.succeeded) or (not ret.output):
            logger.error("Failed to get current branch name. Reason: '{}'.".format(ret.message))
            logger.error("Failed to pull: '{}'.".format(self._repository_name))
            return False
        current_branch = ret.output

        if work_branch != current_branch:
            logger.info("Local repo branch: Exprected: '{}', Current: '{}'.".format(work_branch, current_branch))
            ret = git.checkout_branch(self._local_repo_dir, work_branch)
            if ret.succeeded:
                logger.info("Switched branch: '{}'.".format(work_branch))
            else:
                logger.error("Failed to switch branch: '{}'. Reason: '{}'.".format(work_branch, ret.message))
                logger.error("Failed to pull: '{}'.".format(self._repository_name))
                return False

        logger.info("Start pulling...")
        ret =  git.pull(self._local_repo_dir)
        if ret.succeeded:
            logger.info("Pulled: '{}' ('{}').".format(self._repository_name, work_branch))
            return True
        else:
            logger.error("Failed to pull: '{}' ('{}'). Reason: '{}'.".format(self._repository_name, work_branch, ret.message))
            return False

    def _clone(self, repository_url_with_creds_embedded):
        logger.info("Start cloning...")
        if repository_url_with_creds_embedded:
            url = repository_url_with_creds_embedded
        else:
            url = self._repository_url
        ret = git.clone_branch(url, self._repository_branch_name, self._git_username, self._git_userpasswd, self._local_repo_dir)
        if ret.succeeded:
            logger.info("Cloned: '{}' ('{}').".format(url, self._repository_branch_name))
            return True
        else:
            logger.error("Failed to clone: '{}' ('{}'). Reason: '{}'.".format(url, self._repository_branch_name, ret.message))
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
            logger.info("Local repository exists: {}.".format(self._local_repo_dir))
            return  self._pull()
        else:
            return self._clone(repository_url_with_creds_embedded)

    def _update_translation(self, translation_import):
        orig_path = os.path.join(self._local_repo_dir, translation_import['translation_path'])
        if not os.path.isfile(orig_path):
            logger.error("Expected translation file does not exist in local repository: '{}'.".format(orig_path))
            return False

        new_path = translation_import['local_path']
        if not os.path.isfile(new_path):
            logger.error("Updated traslation NOT found: '{}'.".format(new_path))
            return False

        if filecmp.cmp(orig_path, new_path):
            logger.info("Translation file does not contain any changes.")
            return False

        self._display_diff(orig_path, new_path)
        copyfile(new_path, orig_path)
        logger.info("Updated translation in local repository.")
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
            logger.info("Importing '{}'...".format(t['local_path']))
            if not self._is_file_clean(t):
                logger.error("Skipped staging file. The file is dirty: '{}'.".format(t['translation_path'])) 
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
        ret = git.checkout_branch(self._local_repo_dir, self._repository_branch_name)
        if ret.succeeded:
            return True
        else:
            logger.error("Failed to checkout branch: '{}'. Reason: '{}'.".format(self._repository_branch_name, ret.message))
            return False

    def _checkout_feature_branch(self):
        new_branch_name = 'TPA_{}'.format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        ret = git.checkout_new_branch(self._local_repo_dir, new_branch_name, self._repository_branch_name)
        if ret.succeeded:
            return new_branch_name
        else:
            logger.error("Failed to checkout feature branch: '{}'. Reason: '{}'.".format(new_branch_name, ret.message))
            return None

    def _delete_local_branch(self, branch_name):
        ret = git.delete_local_branch(self._local_repo_dir, branch_name)
        if ret.succeeded:
            return True
        else:
            logger.error("Failed to delete local branch: '{}'. Reason: '{}'.".format(branch_name, ret.message))
            return False

    def _commit(self):
        if not (self._git_username and self._git_userpasswd):
            logger.error("BUG: git username and userpasswd need to be set before calling GitRepository._commit().")
            return False
 
        ret = git.set_config_username(self._local_repo_dir, self._git_userfullname)
        if not ret.succeeded:
            logger.error("Failed to set git config username: '{}'. Reason: '{}'".format(self._git_userfullname, ret.message))
            return False

        ret = git.set_config_useremail(self._local_repo_dir, self._git_useremail)
        if not ret.succeeded:
            logger.error("Failed to set git config useremail: '{}'. Reason: '{}'.".format(self._git_useremail, ret.message))
            return False

        ret = git.commit(self._local_repo_dir, "Translation updates.")
        if ret.succeeded:
            return True
        else:
            logger.error("Failed to commit. Reason: '{}'.".format(ret.message))
            return False

    def _add_file(self, translation_path, list_staged_path):
        ret = git.not_staged_for_commit(self._local_repo_dir, translation_path)
        if not ret.succeeded:
            logger.error("Failed to check staged or not: {}. Reason: '{}'.".format(translation_path, ret.message))
            return
        if not ret.output:
            # this is a bug since the changes have been ensured before translation file was copied to local repository.
            logger.error("Translation file is already staged: '{}'.".format(translation_path))
            return

        ret = git.add_file(self._local_repo_dir, translation_path)
        if ret.succeeded:
            list_staged_path.append(translation_path)
        else:
            logger.error("Failed to add file: '{}'. Reason: '{}'.".format(translation_path, ret.message))

    def _is_file_clean(self, translation_import):
        ret = git.get_status_porcelain(self._local_repo_dir)
        if not ret.succeeded:
            logger.error("Failed to get status: '{}'. Reason: '{}'.".format(self._repository_name, ret.message))
            return False

        for line in ret.output:
            if translation_import['translation_path'] in line.strip().rstrip():
                return False
        return True

    def set_remote_url(self, url):
        ret = git.set_remote_url(self._local_repo_dir, url)
        if ret.succeeded:
            return True
        else:
            logger.error("Failed to set remote url: '{}'. Reason: '{}'.".format(url, ret.message))
            return False

    def push_branch(self, branch_name):
        if not (self._git_username and self._git_userpasswd):
            logger.error("BUG: git username and userpasswd need to be set before calling GitRepository.push_branch().")
            return False

        ret = git.push_branch_set_upstream(self._local_repo_dir, branch_name)
        if ret.succeeded:
            return True
        else:
            logger.error("Failed to push branch: '{}'. Reason: '{}'.".format(branch_name, ret.message))
            return False
        
    def _display_diff(self, file1, file2):
        with open(file1, 'r') as fi1, open(file2, 'r') as fi2:
            diff = difflib.unified_diff(fi1.readlines(), fi2.readlines())
            logger.info("-------- starting diff --------")
            for line in diff:
                logger.info(line.rstrip('\n'))
            logger.info("-------- ending diff --------")

    def _revert_file_in_commit(self, branch_name, commit, file_path):
        revert_commit_message = "Reverted."
        ret = git.revert_commit(self._local_repo_dir, commit, file_path, revert_commit_message)
        if not ret.succeeded:
            logger.error("Failed to revert commit '{}' for '{}'. Reason: '{}'.".format(commit, file_path, ret.message))
            return False

        # anything to commit ?
        #remaining_staged_files = self.get_staged_file(branch_name)
        #if len(remaining_staged_files) < 1:
        #    return True

        logger.error("@@@ Reverted commit: '{}'.".format(commit))

        ret = git.reset_soft(self._local_repo_dir, 'HEAD~1')
        if ret.succeeded:
            return True
        else:
            logger.error("Failed to reset to '{}'. Reason: '{}'.".format(file_path, ret.message))
            return False

    def _revert_files(self, branch_name, paths):
        errors = 0
        for path in paths:
            ret = git.get_commit(self._local_repo_dir, path)
            if not ret.succeeded:
                errors += 1
                logger.info("Faild to get a commit for file: '{}'.".format(path))
                continue

            commits = ret.output
            if len(commits) == 1:
                if not self._revert_file_in_commit(branch_name, commits[0], path):
                    errors += 1
                else:
                    logger.info("Reverted: '{}'.".format(path))
            elif len(commits) == 0:
                errors += 1
                logger.error("Cannot find commit for: '{}'.".format(path))
            else:
                errors += 1
                logger.error("Too many commits for: '{}'. Commits: '{}'.".format(path, commits))
        return errors

    def revert_files_in_branch(self, branch_name, list_of_file_to_revert):
        ret = git.get_current_branch_name(self._local_repo_dir)
        if (not ret.succeeded) or (not ret.output):
            logger.error("Failed to get current branch name. Reason: '{}'.".format(ret.message))
            return False

        current_branch = ret.output
        branch_switched = False
        if current_branch != branch_name:
            ret = git.checkout_branch(self._local_repo_dir, branch_name)
            if ret.succeeded:
                branch_switched = True
                logger.info("Switched branch: from '{}' to '{}'.".format(current_branch, branch_name))
            else:
                logger.error("Failed to switch branch: from '{}' to '{}'. Reason: '{}'.".format(current_branch, branch_name, ret.message))
                return False

        errors = self._revert_files(branch_name, list_of_file_to_revert)

        if branch_switched:
            ret = git.checkout_branch(self._local_repo_dir, current_branch)
            if not ret.succeeded:
                logger.error("Failed to switch branch: from '{}' to '{}'.".format(branch_name, current_branch))

        if errors == 0:
            return True
        else:
            return False


    def get_staged_file(self, branch_name):
        
        # FIXME --- never pick up resource file !!!

        # FIXME --- never pick up duplicates !!!

        ret = git.get_staged_file(self._local_repo_dir, branch_name)
        if not ret.succeeded:
            logger.error("Failed to get staged file in branch: '{}'.".format(branch_name))
        return ret.output

