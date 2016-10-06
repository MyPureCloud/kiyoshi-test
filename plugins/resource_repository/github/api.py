import json
import requests
from requests.exceptions import RequestException, HTTPError

from core.common.results import succeeded_rest_api_call_results, failed_rest_api_call_results 

def submit_pullrequest(repository_owner, repository_name, feature_branch_name, destination_branch_name, pr_title, pr_description, creds=None):
    url = 'https://api.github.com/repos/' + repository_owner + '/' + repository_name + '/pulls'
    headers = {'Content-Type': 'application/json'}
    payload = json.dumps({
       'title': pr_title,
       'body': pr_description,
       'head': feature_branch_name,
       'base': destination_branch_name}, ensure_ascii=False)
    try:
        if creds:
            r = requests.post(url, auth=(creds['username'], creds['userpasswd']), headers=headers, data=payload)
        else:
            r = requests.post(url, headers=headers, data=payload)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r) 

def update_assignee(repository_owner, repository_name, issue_number, assignee, creds=None):
    url = 'https://api.github.com/repos/' + repository_owner + '/' + repository_name + '/issues/' + str(issue_number)
    payload = json.dumps({'assignee': assignee}, ensure_ascii=False)
    try:
        if creds:
            r = requests.post(url, auth=(creds['username'], creds['userpasswd']), data=payload)
        else:
            r = requests.post(url, data=payload)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r) 

def get_pullrequests(repository_owner, repository_name, creds=None):
    url = 'https://api.github.com/repos/' + repository_owner + '/' + repository_name + '/pulls'
    try:
        if creds:
            r = requests.get(url, auth=(creds['username'], creds['userpasswd']))
        else:
            r = requests.get(url)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r) 

