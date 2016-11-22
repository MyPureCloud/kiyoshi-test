import os
import sys
import json
import requests
from requests.exceptions import RequestException, HTTPError

from core.plugins.results import succeeded_rest_api_call_results, failed_rest_api_call_results

def get_language_stats(project_slug=pslug, project_key=pkey):
    params = {'language': language_code, 'json': True}
    url = 'http://api.crowdin.com/api/project/{}/language-status?key={}'.format(project_slug, project_key)
    try:
        r = requests.post(url, params=params)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        sys.stderr.write("{}\n".format(e))
        return failed_rest_api_call_results(str(e))
    else:
        return succeeded_rest_api_call_results(r) 

def update_file(project_slug=pslug, crowdin_resource_path=cipath, import_file_path=path, project_key=pkey):
    url = 'https://api.crowdin.com/api/project/{}/update-file?key={}'.format(project_slug, project_key)
    payload = {'json': True}
    with open(import_file_path, 'r') as fi:
        files = {'files[{}]'.format(crowdin_resource_path): fi} 
        try:
            r = requests.post(url, params=payload, files=files)
            r.raise_for_status()
        except (RequestException, HTTPError) as e:
            return failed_rest_api_call_results(str(e))
        else:
            return succeeded_rest_api_call_results(r) 

def export_file(project_slug=pslug, crowdin_translation_path=cipath, language_code=lcode, project_key=pkey):
    payload = {'json': True}
    url = 'https://api.crowdin.com/api/project/{}/export-file?file={}&language={}&key={}'.format(project_slug, crowdin_translation_path, language_code, project_key)
    try:
        r = requests.post(url, params=payload)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(str(e))
    else:
        return succeeded_rest_api_call_results(r)

