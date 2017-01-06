import json
import requests
from requests.exceptions import RequestException, HTTPError

from core.plugins.results import succeeded_rest_api_call_results, failed_rest_api_call_results 

def post_pullrequest(creds, repository_owner, repository_name, payload):
    headers = {'Content-Type': 'application/json'}
    url = 'https://api.github.com/repos/' + repository_owner + '/' + repository_name + '/pulls'
    try:
        r = requests.post(url, auth=(creds['username'], creds['userpasswd']), headers=headers, data=payload)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r) 

# not using
#def update_assignee(repository_owner, repository_name, issue_number, assignee, creds=None):
#    url = 'https://api.github.com/repos/' + repository_owner + '/' + repository_name + '/issues/' + str(issue_number)
#    payload = json.dumps({'assignee': assignee}, ensure_ascii=False)
#    try:
#        if creds:
#            r = requests.post(url, auth=(creds['username'], creds['userpasswd']), data=payload)
#        else:
#            r = requests.post(url, data=payload)
#        r.raise_for_status()
#    except (RequestException, HTTPError) as e:
#        return failed_rest_api_call_results(e)
#    else:
#        return succeeded_rest_api_call_results(r) 

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

def search_issues(repository_owner, repository_name, author_username, creds=None):
    url = 'https://api.github.com/search/issues?q=author:' + author_username + '+repo:' + repository_owner + '/' + repository_name
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

def post_review_request(creds, repository_owner, repository_name, pull_request_number, payload):
    url = 'https://api.github.com/repos/' + repository_owner + '/' + repository_name + '/pulls/' + str(pull_request_number) + '/requested_reviewers'
    # 2017-01-06 Accept header is required while the API is in review period.
    headers = {'Accept': 'application/vnd.github.black-cat-preview+json'}
    try:
        r = requests.post(url, auth=(creds['username'], creds['userpasswd']), headers=headers, data=payload)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r) 

