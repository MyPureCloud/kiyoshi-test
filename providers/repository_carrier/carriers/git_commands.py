from sh import git, ErrorReturnCode

from common.common import FatalError

def clone(repository_url, branch_name, destdir):
    try:
        git('clone', repository_url, '-b', branch_name, destdir)
    except ErrorReturnCode as e:
        raise FatalError("Failed to clone repository. '{}' '{}' '{}'.".format(repository_url, branch_name, str(e)))

def pull(gitdir):
    try: 
        git('-C', gitdir, 'pull')
    except ErrorReturnCode as e:
        raise FatalError("Failed to pull repository. '{}'  {}.".format(gitdir, str(e)))

