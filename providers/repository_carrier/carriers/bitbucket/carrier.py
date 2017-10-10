import os
import json
import hashlib

from common.common import FatalError
from common.common import TpaLogger 
from common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR, response_NOT_FOUND
from common.common import gen_sha1_from_file_context
from .. import git_commands as git
import settings

def _get_file_context(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ NOTE: creds is not used. """
    try:
        repo_name = kwargs['repo_name']
        file_path = kwargs['file_path']
        gitdir = os.path.join(local_repo_root_dir, repo_name)
        if os.path.exists(gitdir) and os.path.isdir(gitdir):
            local_file_path = os.path.join(gitdir, file_path)
            if os.path.exists(local_file_path):
                sha1 = gen_sha1_from_file_context(local_file_path)
                with open(local_file_path, 'r') as fi:
                    #context = fi.readlines()  this makes list of strings
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
        msg = "Failed to access key in _get_file_contexts kwargs. '{}'".format(str(e))
        raise FatalError(msg)

def _file_exists(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ NOTE: creds is not used. """
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
    """ Clone repository if the repository does not exist.
        NOP if the repository already exists.
    """
    # 
    # TODO --- impl timeout 
    #
    try:
        config = kwargs['config']
        gitdir = os.path.join(local_repo_root_dir, config['repository']['name'])
        if os.path.exists(gitdir) and os.path.isdir(gitdir):
            msg = "Clone not performed. Repository already exists. '{}'".format(gitdir)
            return response_ACCEPTED(request_id, msg, '', kafka)
        url = config['repository']['url']
        url_with_creds = _embed_creds_to_url(config['repository']['url'], creds['username'], creds['userpasswd'])
        branch = config['repository']['branch']
        with TpaLogger(**kafka) as o:
            o.info("Cloning... '{}', Branch: '{}', dest: '{}'".format(url, branch, gitdir))
        git.clone(url_with_creds, branch, gitdir)
        msg = "Cloned. '{}', '{}, '{}'".format(url, branch, local_repo_root_dir)
        return response_OK(request_id, msg, '', kafka)
    except FatalError as e:
        return response_INTERNAL_SERVER_ERROR(request_id, str(e), kafka)

def _pull(request_id, creds, local_repo_root_dir, kafka, **kwargs):
    """ Pull a repository.
        If no such repository, clone, then pull it.
    """
    # 
    # TODO --- impl timeout 
    #
    try:
        config = kwargs['config']
        repo_name = config['repository']['name']
        gitdir = os.path.join(local_repo_root_dir, repo_name)
        if not os.path.exists(gitdir) and not os.path.isdir(gitdir):
            _clone(request_id, creds, local_repo_root_dir, **kwargs)    
        with TpaLogger(**kafka) as o:
            o.info("Pulling... '{}', '{}'".format(repo_name, gitdir))
        git.pull(gitdir)
        msg = "Pulled. '{}', '{}'".format(repo_name, gitdir)
        return response_OK(request_id, msg, '', kafka)
    except KeyError as e:
        msg = "Failed to access key in config. '{}'".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    except FatalError as e:
        return response_INTERNAL_SERVER_ERROR(request_id, str(e), kafka)

commands = {
        'clone': _clone,
        'file_exists': _file_exists,
        'get_file_context': _get_file_context,
        'pull': _pull
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


