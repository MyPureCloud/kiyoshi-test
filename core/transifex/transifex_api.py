import os, sys
import requests
from requests.exceptions import ConnectionError
from hashlib import md5

import settings
from core.TransifexCredsConfigurationClass import TransifexCredsConfiguration

def get_transifex_creds():
    if not os.path.isfile(settings.TRANSIFEX_CREDS_FILE):
        sys.stderr.write("File not found: {}.\n".format(settings.TRANSIFEX_CREDS_FILE))
        return None

    t = TransifexCredsConfiguration()
    if not t.parse(settings.TRANSIFEX_CREDS_FILE):
        sys.stderr.write("Failed to parse: {}\n".format(settings.TRANSIFEX_CREDS_FILE))
        return None
    else:
        return {'username': t.get_username(), 'userpasswd': t.get_userpasswd()}

def get_projects():
    creds = get_transifex_creds()
    if not creds:
        return None

    url = 'http://www.transifex.com/api/2/projects/'
    try:
        r =  requests.get(url, auth=(creds['username'], creds['userpasswd']))
    except ConnectionError as e:
        sys.stderr.write("{}\n".format(e))
        return None
    else:
        if not (r.status_code == 200 or r.status_code == 201):
            sys.stderr.write("status_code: {}\n".format(r.status_code))
            sys.stderr.write("{}\n".format(r.text))
            return None

        return r.text

def get_project_details(project_slug):
    creds = get_transifex_creds()
    if not creds:
        return None

    url = 'http://www.transifex.com/api/2/project/' + project_slug + '?details'
    try:
        r =  requests.get(url, auth=(creds['username'], creds['userpasswd']))
    except ConnectionError as e:
        sys.stderr.write("{}\n".format(e))
        return None
    else:
        if not (r.status_code == 200 or r.status_code == 201):
            sys.stderr.write("status_code: {}\n".format(r.status_code))
            sys.stderr.write("{}\n".format(r.text))
            return None

        return r.text

def get_resources(project_slug):
    creds = get_transifex_creds()
    if not creds:
        return None

    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resources'
    try:
        r =  requests.get(url, auth=(creds['username'], creds['userpasswd']))
    except ConnectionError as e:
        sys.stderr.write("{}\n".format(e))
        return None
    else:
        if not (r.status_code == 200 or r.status_code == 201):
            sys.stderr.write("status_code: {}\n".format(r.status_code))
            sys.stderr.write("{}\n".format(r.text))
            return None

        return r.text

def get_resource_details(project_slug, resource_slug):
    creds = get_transifex_creds()
    if not creds:
        return None

    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '?details'
    try:
        r =  requests.get(url, auth=(creds['username'], creds['userpasswd']))
    except ConnectionError as e:
        sys.stderr.write("{}\n".format(e))
        return None
    else:
        if not (r.status_code == 200 or r.status_code == 201):
            sys.stderr.write("status_code: {}\n".format(r.status_code))
            sys.stderr.write("{}\n".format(r.text))
            return None

        return r.text

def get_translation_strings(project_slug, resource_slug, language_code):
    creds = get_transifex_creds()
    if not creds:
        return None

    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/translation/' + language_code + '/strings'
    try:
        r =  requests.get(url, auth=(creds['username'], creds['userpasswd']))
    except ConnectionError as e:
        sys.stderr.write("{}\n".format(e))
        return None
    else:
        if not (r.status_code == 200 or r.status_code == 201):
            sys.stderr.write("status_code: {}\n".format(r.status_code))
            sys.stderr.write("{}\n".format(r.text))
            return None

        return r.text

def get_translation_strings_details(project_slug, resource_slug, language_code):
    creds = get_transifex_creds()
    if not creds:
        return None

    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/translation/' + language_code + '/strings?details'
    try:
        r =  requests.get(url, auth=(creds['username'], creds['userpasswd']))
    except ConnectionError as e:
        sys.stderr.write("{}\n".format(e))
        return None
    else:
        if not (r.status_code == 200 or r.status_code == 201):
            sys.stderr.write("status_code: {}\n".format(r.status_code))
            sys.stderr.write("{}\n".format(r.text))
            return None

        return r.text

def get_string_hash(source_string_key):
    return md5(':'.join([source_string_key, ""]).encode('utf-8')).hexdigest()

def get_source_string_details(project_slug, resource_slug, source_string_key):
    creds = get_transifex_creds()
    if not creds:
        return None

    string_hash = get_string_hash(source_string_key)
    url = 'http://www.transifex.com/api/2/project/' + project_slug + '/resource/' + resource_slug + '/source/' + string_hash 
    try:
        r =  requests.get(url, auth=(creds['username'], creds['userpasswd']))
    except ConnectionError as e:
        sys.stderr.write("{}\n".format(e))
        return None
    else:
        if not (r.status_code == 200 or r.status_code == 201):
            sys.stderr.write("status_code: {}\n".format(r.status_code))
            sys.stderr.write("{}\n".format(r.text))
            return None

        return r.text

