import os
import json
import hashlib

from ....common.common import FatalError
from ....common.common import TpaLogger 
from ....common.common import GET 
from ....common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR, response_NOT_IMPLEMENTED
from ....common.common import gen_sha1_from_file_context
from .. import git_commands as git
from . import settings

BITBUCKET_API = 'https://bitbucket.org/api/2.0'

def _get_file_context(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ Return context of a file from local repository.
        NOTE: creds is not used.
    """
    try:
        repo_name = kwargs['repo_name']
        file_path = kwargs['file_path']
        gitdir = os.path.join(local_repo_root_dir, repo_name)
        if os.path.exists(gitdir) and os.path.isdir(gitdir):
            local_file_path = os.path.join(gitdir, file_path)
            if os.path.exists(local_file_path):
                sha1 = gen_sha1_from_file_context(local_file_path)
                with open(local_file_path, 'r') as fi:
                    context = fi.read()
                results = {'path': file_path, 'sha1': sha1, 'context': context}
                return response_OK(request_id, "Completed.", results, kafka)
            else:
                msg = "File '{}' not exist." .format(file_path)
                return response_BAD_REQUEST(request_id, msg, kafka)
        else:
            msg = "Repository '{}' not exist." .format(repo_name)
            return response_BAD_REQUEST(request_id, msg, kafka)
    except KeyError as e:
        msg = "Failed to access key in _get_file_context kwargs. '{}'".format(str(e))
        raise FatalError(msg)

def _update_file_context(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ Update specified file in local repository with given context.
        NOTE: creds is not used.
    """
    try:
        repo_name = kwargs['repo_name']
        file_path = kwargs['file_path']
        context = kwargs['context']
        gitdir = os.path.join(local_repo_root_dir, repo_name)
        if os.path.exists(gitdir) and os.path.isdir(gitdir):
            local_file_path = os.path.join(gitdir, file_path)
            if os.path.exists(local_file_path):
                j = json.dumps(context)    
                with open(local_file_path, 'w') as fi:
                    fi.write(j)
                sha1 = gen_sha1_from_file_context(local_file_path)
                results = {'path': file_path, 'sha1': sha1, 'context': j}
                return response_OK(request_id, "Completed.", results, kafka)
            else:
                msg = "File '{}' not exist." .format(file_path)
                return response_BAD_REQUEST(request_id, msg, kafka)
        else:
            msg = "Repository '{}' not exist." .format(repo_name)
            return response_BAD_REQUEST(request_id, msg, kafka)
    except KeyError as e:
        msg = "Failed to access key in _update_file_context kwargs. '{}'".format(str(e))
        raise FatalError(msg)

def _file_exists(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ Checks if specified file exists in local repository.
        NOTE: creds is not used.
    """
    try:
        repo_name = kwargs['repo_name']
        file_path = kwargs['file_path']
        gitdir = os.path.join(local_repo_root_dir, repo_name)
        if os.path.exists(gitdir) and os.path.isdir(gitdir):
            if os.path.exists(os.path.join(gitdir, file_path)):
                results = {'path': file_path, 'exists': 'true'}
                return response_OK(request_id, "Completed.", results, kafka)
            else:
                results = {'path': file_path, 'exists': 'false'}
                return response_OK(request_id, "Completed.", results, kafka)
        else:
            msg = "Repository '{}' not exist." .format(repo_name)
            return response_BAD_REQUEST(request_id, msg, kafka)
    except KeyError as e:
        msg = "Failed to access key in _file_exists kwargs. '{}'".format(str(e))
        raise FatalError(msg)

def _embed_creds_to_url(url, username, userpasswd):
    """ ASUMPTION
        url should be formed as https://bitbucket.org/.....
    """
    pos = url.find('https://bitbucket.org/')
    if pos == 0:
        return "{}{}:{}@{}".format(url[0:8], username, userpasswd, url[8:])
    else:
        msg = "Failed to embed creds to url. Unexpeced url format. '{}'".format(url)
        raise FatalError(msg)

def _clone(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ Clone repository if the repository does not exist loccally.
        NOP if the repository already exists.
    """
    # 
    # TODO --- impl timeout 
    #
    try:
        config = kwargs['config']
        gitdir = os.path.join(local_repo_root_dir, config['repository']['name'])
        url = config['repository']['url']
        url_with_creds = _embed_creds_to_url(config['repository']['url'], creds['username'], creds['userpasswd'])
        branch = config['repository']['branch']
    except KeyError as e:
        msg = "Failed to access key while obtaining repository info for clone. '{}'".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

        if os.path.exists(gitdir) and os.path.isdir(gitdir):
            msg = "Clone not performed. Repository already exists. '{}'".format(gitdir)
            return response_ACCEPTED(request_id, msg, gitdir, kafka)

    try:
        with TpaLogger(**kafka) as o:
            o.info("Cloning... '{}', Branch: '{}', dest: '{}'".format(url, branch, gitdir))
        git.clone(url_with_creds, branch, gitdir)
        msg = "Cloned. '{}', '{}, '{}'".format(url, branch, gitdir)
        return response_OK(request_id, msg, gitdir, kafka)
    except FatalError as e:
        return response_INTERNAL_SERVER_ERROR(request_id, str(e), kafka)

def _pull(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ Pull to local repository.
        If no such repository, clone the local repository.
    """
    # 
    # TODO --- impl timeout 
    #
    try:
        config = kwargs['config']
        repo_name = config['repository']['name']
    except KeyError as e:
        msg = "Failed to access key while obtaining repository info for pull. '{}'".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    # Assuming the directory is valid git directory.
    gitdir = os.path.join(local_repo_root_dir, repo_name)
    if not os.path.exists(gitdir) and not os.path.isdir(gitdir):
        with TpaLogger(**kafka) as o:
            o.info("Try cloning repository for pull. '{}', '{}'".format(repo_name, gitdir))
        res = _clone(request_id, creds, local_repo_root_dir, kafka, **kwargs)
        if res['status_code'] != 200:
            return res
        else:
            msg = "Pulled(cloned). '{}', '{}'".format(repo_name, gitdir)
            return response_OK(request_id, msg, gitdir, kafka)
    else:
        with TpaLogger(**kafka) as o:
            o.info("Pulling repository... '{}', '{}'".format(repo_name, gitdir))
        try:
            git.pull(gitdir)
            msg = "Pulled. '{}', '{}'".format(repo_name, gitdir)
            return response_OK(request_id, msg, gitdir, kafka)
        except FatalError as e:
            msg = "Failed to pull repository. '{}', '{}' {}".format(repo_name, gitdir, str(e))
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

def _fetch_pr_values(results, url, request_id, creds):
    """ Fecth pull request and put all 'value's  in 'results'. 
        Return subsequest page url, if it exists.
    """
    try:
        r = GET(url, request_id, auth=creds)
        for i in range (0, r["pagelen"]):
            results.append(r['values'][i])
        if 'next' in r:
            return r['next']
        else:
            return None
    except IndexError:
        # this is raised when actual number of entries is fewer than pagelen, meaning
        # there is no more PRs to fetch.
        return None 


def _get_open_pullrequest(request_id, creds, repository_owner, repository_name, kafka):
    """ Obtain open pull request information from Bitbucket.
        Limit number of pages to fetch from Bitbucket, which currently is 3.
    """
    lst = []
    try:
        url = os.path.join(BITBUCKET_API, 'repositories', repository_owner, repository_name, 'pullrequests?state=OPEN')
        next_url = _fetch_pr_values(lst, url, request_id, creds)
    except FatalError as e:
        msg = "Failed to get open pullrequests (first page). '{}'".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    LIMIT = 3
    current = 0
    while next_url and current < LIMIT:
        try:
            next_url = _fetch_pr_values(lst, url, request_id, creds)
            current += 1
        except FatalError as e:
            msg = "Failed to get open pullrequests (subsequest page). '{}'".format(str(e))
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    
    msg = "{} open pull requests.".format(len(lst))
    return response_OK(request_id, msg, lst, kafka) 

def _get_closed_pullrequest(request_id, creds, config, kafka):
    return response_NOT_IMPLEMENTED(request_id, "Getting closed pull request is not implemented.", kafka)

def _get_merged_pullrequest(request_id, creds, config, kafka):
    return response_NOT_IMPLEMENTED(request_id, "Getting closed pull request is not implemented.", kafka)

def _get_pullrequests_on_status(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ Obtain pull request information for a specified status from Bitbucket.
    """
    # 
    # TODO --- impl timeout 
    #
    try:
        config = kwargs['config']
        repo_owner = config['repository']['owner'] 
        repo_name = config['repository']['name']
        if kwargs['status'] == 'open':
            return _get_open_pullrequest(request_id, creds, repo_owner, repo_name, kafka)
        elif kwargs['status'] == 'closed':
            return _get_closed_pullrequest(request_id, creds, repo_owner, repo_name, kafka)
        elif kwargs['status'] == 'merged':
            return _get_merged_pullrequest(request_id, creds, repo_owner, repo_name, kafka)
        else:
            msg = "Unknown pullrequest subcommand: '{}'." .format(subcmd)
            return response_BAD_REQUEST(request_id, msg, kafka)
    except KeyError as e:
        msg = "Failed to access key in kwargs for pullrequest. '{}'".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

def _submit_pullrequest():
    """ Submit a pull request to Bitbucket wich changes in specified branch.
    """
    return response_NOT_IMPLEMENTED(request_id, "Submitting pull request is not implemented.", kafka)

commands = {
        'clone': _clone,
        'file_exists': _file_exists,
        'get_file_context': _get_file_context,
        'update_file_context': _update_file_context,
        'pull': _pull,
        'get_pullrequests_on_status': _get_pullrequests_on_status,
        'submit_pullrequest': _submit_pullrequest
        }

def _init_repo_dir(request_id):
    try:
        localdir = settings.local_repo_dir
        if os.path.exists(localdir) and os.path.isdir(localdir):
            return localdir
        else:
            os.makedirs(localdir)
            return localdir
    except KeyError as e:
        raise FatalError("Failed to access key in repo config file. '{}'".format(str(e)))
    except OSError as e:
        raise FatalError("Failed to create local repo dir. '{}' {}".format(localdir, str(e)))

def _get_creds(request_id):
    try:
        return {'userfullname': settings.creds['userfullname'],
            'username': settings.creds['username'],
            'userpasswd': settings.creds['userpasswd'],
            'useremail': settings.creds['useremail']}
    except KeyError as e:
        raise FatalError("Failed to access key in creds config file. '{}'".format(str(e)))

def get_carrier(request_id, **kwargs):
    kafka = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port'],
        'topic': settings.kafka['topic'],
        'key': 'default'}

    initialized = False
    try:
        local_repo_root_dir = _init_repo_dir(request_id)
        creds = _get_creds(request_id)
        initialized = True
    except FatalError as e:
        with TpaLogger(**kafka) as o:
            o.error("Failed to initialize carrier. {}".format(str(e)))

    def _dispatcher(request_id, command, **kwargs):
        if not initialized:
            msg = "Carrier is not operational due to initialization error."
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
        try:
            # request_id, creds, local_repo_root_dir are mandatory args for all commands.
            return commands[command](request_id, creds, local_repo_root_dir, kafka, **kwargs)
        except KeyError as e:
            msg = "Command not found in commands list. '{}'.".format(command)
            return response_BAD_REQUEST(request_id, msg, kafka)
    return _dispatcher


