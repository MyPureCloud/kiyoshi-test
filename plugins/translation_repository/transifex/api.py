import requests
from requests.exceptions import RequestException, HTTPError
from hashlib import md5
from collections import namedtuple

from core.common.results import succeeded_rest_api_call_results, failed_rest_api_call_results 

TransifexApiCreds = namedtuple('TransifexApiCreds', 'username, userpasswd')

def get_projects(creds):
    url = 'http://www.transifex.com/api/2/projects/'
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def get_project_details(project_slug, creds):
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '?details'
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def get_resources(project_slug, creds):
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resources'
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def get_resource_details(project_slug, resource_slug, creds):
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '?details'
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def get_translation_strings(project_slug, resource_slug, language_code, creds):
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/translation/' + language_code + '/strings'
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def get_translation_strings_details(project_slug, resource_slug, language_code, creds):
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/translation/' + language_code + '/strings?details'
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def get_string_hash(source_string_key):
    return md5(':'.join([source_string_key, ""]).encode('utf-8')).hexdigest()

def get_source_string_details(project_slug, resource_slug, source_string_key, creds):
    string_hash = get_string_hash(source_string_key)
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/source/' + string_hash 
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def get_language_stats(project_slug, resource_slug, language_code, creds):
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/stats/' + language_code + '/'
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def get_translation_reviewed(project_slug, resource_slug, language_code, creds):
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/translation/' + language_code + '/?mode=reviewed'
    try:
        r = requests.get(url, auth=(creds.username, creds.userpasswd))
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

def put_resource(project_slug, resource_slug, import_file_path, repository_name, resource_path, creds):
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/content/'
    headers = {'Content-type': 'multipart/form-data'}
    files = {'file': (import_file_path, open(import_file_path, 'rb'), 'multipart/form-data', {'Expires': '0'})}
    try:
        r = requests.put(url, auth=(creds.username, creds.userpasswd), files=files)
        r.raise_for_status()
    except (RequestException, HTTPError) as e:
        return failed_rest_api_call_results(e)
    else:
        return succeeded_rest_api_call_results(r)

