import os
import sys
import json
import requests
from requests.exceptions import RequestException, HTTPError

from core.plugins.results import succeeded_rest_api_call_results, failed_rest_api_call_results

def export_file(api_key, project_slug, params):
    url = 'https://api.crowdin.com/api/project/{}/export-file?&key={}'.format(project_slug, api_key)
    try:
        r = requests.post(url, params=params)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(str(e))
    else:
        return succeeded_rest_api_call_results(r)

def get_language_stats(api_key, project_slug, params):
    url = 'http://api.crowdin.com/api/project/{}/language-status?key={}'.format(project_slug, api_key)
    try:
        r = requests.post(url, params=params)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(str(e))
    else:
        return succeeded_rest_api_call_results(r) 

def update_file(api_key, project_slug, files, payload):
    """
    CAUTION: 'files' have to be opened while performing this operation.
    """
    url = 'https://api.crowdin.com/api/project/{}/update-file?key={}'.format(project_slug,api_key)
    try:
        r = requests.post(url, params=payload, files=files)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(str(e))
    else:
        return succeeded_rest_api_call_results(r) 

