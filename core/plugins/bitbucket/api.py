import requests
from requests.exceptions import RequestException, HTTPError

from core.plugins.results import succeeded_rest_api_call_results, failed_rest_api_call_results

def get_pullrequests(creds, **kwargs):
    """
    Query pull requests.
    Specify repository_owner, repository_name and query_string for the very first query.
    Or, specify pull request URL via use_url to query a specific pull request (e.g. to query 'next' pull request page).

    Mandatory Parameters
    -------------------------------------------------
    repository_owner        Owner of the repository
    repository_name         Name of the repository
    query_string            Query string (e.g. '&state=OPEN')

        --- or ---
    use_url                 Request URL
    """
    try:
        if 'use_url' in kwargs:
            url = kwargs['use_url']
        else:
            url = 'https://bitbucket.org/api/2.0/repositories/' + kwargs['repository_owner'] + '/' + kwargs['repository_name'] + '/pullrequests' + kwargs['query_string']
        headers = {'Content-Type': 'application/json'}
        r = requests.get(url, auth=(creds['username'], creds['userpasswd']), headers=headers)
        r.raise_for_status()
    except KeyError as e:
        return failed_rest_api_call_results(str(e))
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(str(e))
    else:
        return succeeded_rest_api_call_results(r) 

def post_pullrequest(creds, repository_owner, repository_name, payload):
    headers = {'Content-Type': 'application/json'}
    url = 'https://bitbucket.org/api/2.0/repositories/' + repository_owner + '/' + repository_name + '/pullrequests'
    try:
        r = requests.post(url, auth=(creds['username'], creds['userpasswd']), headers=headers, data=payload)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r) 

