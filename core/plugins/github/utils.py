import sys
import json
from collections import OrderedDict

from core.plugins.results import succeeded_util_call_results, failed_util_call_results
import api as github

def get_pullrequest_details(pullrequest_response_text):
    """ Return pullrequest number, url and diff url in dictionary.
    """
    try:
        j = json.loads(pullrequest_response_text, object_pairs_hook=OrderedDict)
    except ValueError as e:
        return failed_util_call_results(e)

    for ent in j.items():
        if ent[0] == 'html_url':
            pr_url = ent[1]
        elif ent[0] == 'diff_url':
            pr_diff_url =  ent[1]
        elif ent[0] == 'number':
            pr_number = ent[1]

    if pr_url == None or pr_diff_url == None or pr_number == None:
        return failed_util_call_results("Failed to obtain url, diff_url or number from pullrequest response.")

    return succeeded_util_call_results({'number': pr_number, 'pr_url': pr_url, 'pr_diff_url': pr_diff_url})

def _get_open_pullrequests_descriptions(repository_owner, repository_name, pr_title, creds=None):
    ret = github.get_pullrequests(repository_owner, repository_name, creds)
    if not ret.succeeded:
        return failed_util_call_results(ret.message)

    descriptions = []
    try:
        j = json.loads(ret.response.text, object_pairs_hook=OrderedDict)
    except ValueError as e:
        return failed_util_call_results(e)
    else:
        for pr in j:
            if pr['state'] == 'open':
                if pr['title'] == pr_title:
                    descriptions.append(pr['body'])

    return succeeded_util_call_results(descriptions)

def get_file_paths_in_open_pullrequests(repository_owner, repository_name, pr_title, creds=None):
    # NIY --- return list of files path, instead of list of descriptions 
    return _get_open_pullrequests_descriptions(repository_owner, repository_name, pr_title, creds=None)

def get_pullrequests(repository_owner, repository_name, author, creds=None):
    ret = github.query_issues(repository_owner, repository_name, author, creds)
    if not ret.succeeded:
        return failed_util_call_results(ret.message)

    results = []
    try:
        j = json.loads(ret.response.text, object_pairs_hook=OrderedDict)
    except ValueError as e:
        return failed_util_call_results(e)
    else:
        for pr in j:
            if pr['state'] == 'open':
                if pr['title'] == pr_title:
                    results.append(pr['body'])

    return succeeded_util_call_results(results)

