import sys
import os
import requests
from requests.exceptions import RequestException, HTTPError
import json
from collections import OrderedDict

from core.common.results import succeeded_rest_api_call_results, failed_rest_api_call_results

def get_open_pullrequests(repository_owner, repository_name, creds):
    url = 'https://bitbucket.org/api/2.0/repositories/' + repository_owner + '/' + repository_name + '/pullrequests?state=OPEN'
    headers = {'Content-Type': 'application/json'}
    try:
        r = requests.get(url, auth=(creds['username'], creds['userpasswd']), headers=headers)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r) 

def submit_pullrequest(repository_owner, repository_name, feature_branch_name, destination_branch_name, pr_title, pr_description, pr_reviewers, creds):
    reviewers = []
    for s in pr_reviewers:
        reviewers.append({'username': s})

    payload = json.dumps({
        'source': {
            'branch': {
                'name': feature_branch_name
            },
            'repository': {
                'full_name': repository_owner + '/' + repository_name
            }
        },
        'destination': {
            'branch': {
                'name': destination_branch_name
            }
        },
        'title': pr_title,
        'description': pr_description,
        'reviewers': reviewers,
        'close_source_branch': 'true'}, ensure_ascii=False)

    headers = {'Content-Type': 'application/json'}
    url = 'https://bitbucket.org/api/2.0/repositories/' + repository_owner + '/' + repository_name + '/pullrequests'
    try:
        r = requests.post(url, auth=(creds['username'], creds['userpasswd']), headers=headers, data=payload)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r) 

