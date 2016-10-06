import re
from sh import git, ErrorReturnCode

from core.common.results import succeeded_util_call_results, failed_util_call_results

def get_status_porcelain(git_dir):
    """ Return status in easy-to-parse format.
    """
    try:
        output = git('-C', git_dir, 'status', '--porcelain')
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(output) 

def get_current_branch_name(git_dir):
    """ Return current branch name (e.g. 'master').
    """
    try:
        output = git('-C', git_dir, 'rev-parse', '--abbrev-ref', 'HEAD')
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(output.strip().rstrip()) 

def checkout_branch(git_dir, branch_name):
    """ Checkout specified branch.
    """
    try:
        git('-C', git_dir, 'checkout', branch_name)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def pull(git_dir):
    """ Pull current branch.
    """
    try: 
        git('-C', git_dir, 'pull')
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def clone_branch(repository_url, branch_name, username, userpasswd):
    """ Clone specific branch of repository.
    """
    try:
        git('clone', repository_url, '-b', branch_name)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def checkout_branch(git_dir, branch_name):
    """ Checkout a branch.
    """
    try:
        git('-C', git_dir, 'checkout', branch_name)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def checkout_new_branch(git_dir, branch_name, base_branch_name=None):
    """ Checkout a new branch (from base branch, if specified).
    """
    try:
        if base_branch_name:
            git('-C', git_dir, 'checkout', '-b', branch_name, base_branch_name)
        else:
            git('-C', git_dir, 'checkout', '-b', branch_name)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def delete_local_branch(git_dir, branch_name):
    """ Delete a local branch.
    """
    try:
        git('-C', git_dir, 'branch', '-d', branch_name)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def set_config_username(git_dir, username):
    """ Set git username.
    """
    try:
        git('-C', git_dir, 'config', 'user.name', username)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def set_config_useremail(git_dir, useremail):
    """ Set git user email.
    """
    try:
        git('-C', git_dir, 'config', 'user.email', useremail)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def commit(git_dir, commit_message):
    """ Issue commit with commit message.
    """
    try:
        git('-C', git_dir, 'commit', '-m', commit_message)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def not_staged_for_commit(git_dir, file_path):
    """ Return True if specified file is not in index (the file is 
        modified but is not staged for commit).
    """
    try:
        output = git('-C', git_dir, 'status')
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        found = False
        regex = re.compile(r'modified:\s*{}'.format(file_path))
        for line in output:
            line = line.strip().rstrip()
            m = regex.search(line)
            if m:
                found = True
                break
        return succeeded_util_call_results(found) 

def add_file(git_dir, file_path):
    """ Add a file to index.
    """
    try:
        git('-C', git_dir, 'add', file_path)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def set_remote_url(git_dir, url):
    try:
        git('-C', git_dir, 'remote', 'set-url', 'origin', url)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def push_branch_set_upstream(git_dir, branch_name):
    """ Push new branch to remote.
    """
    try:
        # this will ask username/password
        git('-C', git_dir, 'push', '--set-upstream', 'origin', branch_name)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 
    return ret

def get_commit(git_dir, file_path):
    """ Return commit sha1(s) which contains specified file.
    """
    try:
        output = git('-C', git_dir, 'log', 'master..', '--pretty=format:%H', file_path)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        commits = []
        for s in output:
            # as output from sh contains VT100 escape sequences,
            # extract only sha1 out of it.
            c = '{}'.format(s).strip().rstrip()
            regex = re.compile(r'[a-z0-9]{40}')
            m = regex.search(c)
            if m:
                commits.append(m.group(0))
        return succeeded_util_call_results(commits) 

def revert_commit(git_dir, commit, file_path, revert_commit_message):
    """ Revert commit for specified file.
    """
    prev_commit = commit.rstrip() + '~1'
    try:
        git('-C', git_dir, 'checkout', prev_commit, file_path)
        git('-C', git_dir, 'commit', '-m', revert_commit_message)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def reset_soft(git_dir, to_commit):
    """ Reset index to specified commit (e.g. 'HEAD~2')
    """
    try:
        git('-C', git_dir, 'reset', '--soft', to_commit)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        return succeeded_util_call_results(None) 

def get_staged_file(git_dir, branch_name):
    """ Return staged file(s).
    """
    try:
        output = git('-C', git_dir, '--no-pager', 'log', '--name-status', '--oneline', 'HEAD..' + branch_name)
    except ErrorReturnCode as e:
        return failed_util_call_results(e)
    else:
        staged_files = []
        regex = re.compile(r'^M\s*(.+)$')
        for s in output:
            m = regex.match(s)
            if m:
                if not m.group(0) in staged_files:
                    staged_files.append(m.group(1))
        return succeeded_util_call_results(staged_files) 

