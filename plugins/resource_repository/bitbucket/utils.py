import sys
import os
import re
import json
from collections import OrderedDict

from core.common.results import succeeded_util_call_results, failed_util_call_results
import api as bitbucket

#def _set_remote_url(self):
#    user_name = self.get_user_name()
#    user_passwd = self.get_user_passwd()
#    repository_owner = self.get_repository_owner()
#   repository_name = self.get_repository_name()
#    url = "https://{}:{}@bitbucket.org/{}/{}.git".format(user_name, user_passwd, repository_owner, repository_name)
#    return self.set_remote_url(url)

def _get_open_pullrequests_descriptions(repository_owner, repository_name, pr_title, creds):
    """ Return list of opened PRs description.
    """

    # FIXME --- use pr_title to pin point specific pr.

    descriptions = []
    done = False
    while not done:
        ret = bitbucket.get_open_pullrequests(repository_owner, repository_name, creds)
        if not ret.succeeded:
            return failed_util_call_results(ret.message)
        
        pr = ret.response.text
        try:
            j = json.loads(pr, object_pairs_hook=OrderedDict)
        except ValueError as e:
            return failed_util_call_results(e)
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

    return succeeded_util_call_results(descriptions)

def get_file_paths_in_open_pullrequests(repository_owner, repository_name, pr_title, creds=None):
    # NIY --- return list of files path, instead of list of descriptions 
    return _get_open_pullrequests_descriptions(repository_owner, repository_name, pr_title, creds)

def get_pullrequest_details(pullrequest_response_text):
    """ Return pullrequest number, url and diff url in dictionary.
    """
    try:
        j = json.loads(pullrequest_response_text, object_pairs_hook=OrderedDict)
    except ValueError as e:
        return failed_util_call_results(e)

    pr_number = j['id']
    pr_url = j['links']['html']['href']
    pr_diff_url = j['links']['diff']['href']

    if pr_url == None or pr_diff_url == None or pr_number == None:
        return failed_util_call_results("Failed to obtain url, diff_url or number from pullrequest response.")

    return succeeded_util_call_results({'number': pr_number, 'pr_url': pr_url, 'pr_diff_url': pr_diff_url})

