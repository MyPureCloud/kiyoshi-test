import os
import re
import json
from collections import OrderedDict

import logging
logger = logging.getLogger('tpa')

import api as bitbucket

#def _set_remote_url(self):
#    user_name = self.get_user_name()
#    user_passwd = self.get_user_passwd()
#    repository_owner = self.get_repository_owner()
#   repository_name = self.get_repository_name()
#    url = "https://{}:{}@bitbucket.org/{}/{}.git".format(user_name, user_passwd, repository_owner, repository_name)
#    return self.set_remote_url(url)

def _extract_pullrequest_info(query_pr_response_text, limit):
    try:
        j = json.loads(query_pr_response_text, object_pairs_hook=OrderedDict)
    except ValueError as e:
        logger.error("Failed to extract Pull Request information. Reason: '{}'.".format(str(e)))
        return {'succeeded': False}
    else:
        try:
            l = []
            n = 0
            for x in j['values']:
                if n >= limit:
                    next_url = None
                    break
                else:
                    l.append({
                        'state': x['state'],
                        'number': x['id'],
                        'title': x['title'],
                        'description': x['description'],
                        'submitter': x['author']['username'],
                        'date': x['created_on'],
                        'pr_url': x['links']['self'],
                        'pr_diff"url': x['links']['diff']
                        })
                    n += 1
            else:
                if 'next' in j:
                    next_url = j['next']
                else:
                    next_url = None
        except KeyError as e:
            logger.error("Failed to extract Pull Request information. Resson: '{}'.".format(str(e)))
            return {'succeeded': False}
        else:
            if n == 0:
                logger.info("Nothing is extracted from Pull Request query response. Response: '{}'.".format(j))
            
            return {'succeeded': True, 'num_extracted': n, 'next_url': next_url, 'results': l}

def _get_pullrequests(creds, repository_owner, repository_name, query, limit):
    logger.info("Number of pull requests to query: '{}'.".format(limit))

    # very first attempt
    ret = bitbucket.get_pullrequests(creds, repository_owner=repository_owner, repository_name=repository_name, query_string=query)
    if not ret.succeeded:
        logger.error("Failed to obtain Pull Request information (first page). Reason: '{}'.".format(ret.message))
        return None

    d = _extract_pullrequest_info(ret.response.text, limit)
    if not d['succeeded']: # error while extacting pull request info.
        return None

    if d['num_extracted'] == 0: # seems no pull requests have been issued.
        return []

    if d['num_extracted'] >= limit: # enough pull requests obtained.
        return d['results']

    # subsequent attempts
    l = d['results']
    n = d['num_extracted']
    while n < limit:
        if not d['next_url']: # no more pull requests to query
            return l
        else:
            ret = bitbucket.get_pullrequests(creds, use_url=d['next_url'])
            if ret.succeeded:
                d = _extract_pullrequest_info(ret.response.text, limit-n)
                if d['succeeded']:
                    if d['num_extracted'] >= 1:
                        l.extend(d['results'])
                        n = n + d['num_extracted']
                    else: # there is no pull request info in the page.
                        return l
                else: # this is error case but return pull request info we already obtained.
                    return l
            else:
                logger.error("Failed to obtain Pull Request information (2nd+ page). Reason: '{}'.".format(ret.message))
                return l

    return l

def get_pullrequests(creds, repository_owner, repository_name, pullrequest_state_strings, limit):
    """
    Return list of pull request information as follows. The list is empty when no pull requests are found.
    Or, return None on any errors.

        state               State of the Pull Request.
        number              Pull Request number.
        title               Title of the Pull Request.
        description         Pull Request description.
        submitter           Username who submitted the Pull Request.
        date                Pull Request submission date.
        pr_url              URL to the Pull Request page.
        pr_diff_url         URL to the Pull Request (diff) page.

    pullrequest_state_strings is a list of none or any combination of 'OPEN', 'MERGED' and 'DECLINED'.
    limit is to specify number of pull requests to query.
    """
    if len(pullrequest_state_strings) >= 1:
        query = '?' + '+'.join('state=' + s for s in pullrequest_state_strings)
    else:
        query = '?state=OPEN+state=MERGED+state=DECLINED'
    return _get_pullrequests(creds, repository_owner, repository_name, query, limit)

def _prep_pr_payload(**kwargs):
    try:
        owner = kwargs['repository_owner']
        repo = kwargs['repository_name']
        target = kwargs['feature_branch_name']
        dest = kwargs['destination_branch_name']
        title = kwargs['pr_title']
        desc = kwargs['pr_description']

        reviewers = []
        if 'pr_reviewers' in kwargs:
            for s in kwargs['pr_reviewers']:
                reviewers.append({'username': s})
        if len(reviewers) >= 1:
            payload = json.dumps({
                'source': {
                    'branch': {'name': target},
                    'repository': {'full_name': owner + '/' + repo}
                },
                'destination': {
                    'branch': {'name': dest}
                },
                'title': title,
                'description': desc,
                'reviewers': reviewers,
                'close_source_branch': 'true'}, ensure_ascii=False)
        else:
            payload = json.dumps({
                'source': {
                    'branch': {'name': target},
                    'repository': {'full_name': owner + '/' + repo}
                },
                'destination': {
                    'branch': {'name': dest}
                },
                'title': title,
                'description': desc,
                'close_source_branch': 'true'}, ensure_ascii=False)
    except KeyError as e:
        logger.error("Failed to prepare payload for a Pull Request. Reason: '{}'.".format(str(e)))
        return None
    else:
        return payload

def submit_pullrequest(creds, **kwargs):
    """
    Submit a Pull Request.
    Return following information in a dictionaly when Pull Request is submitted. If one of
    those inforamtion cannot be obtained, all are set to 'N/A'.

        number          Pull Request number.
        pr_url          URL to the Pull Request page.
        pr_diff_url     URL to Pull Request diff page.
        
    Or, return None on any errors.

    Mandatory Parameters
    --------------------
    repository_owner                Name of repository owner.
    repository_name                 Name of repository to submit a Pull Request.
    feature_branch_name             Name of a branch which contains changes.
    destination_branch_name         Name of a branch the feature branch will be merged to.
    pr_title                        Pull Request title.
    pr_description                  Pull Request description.

    Optional Parameters
    -------------------
    pr_reviewers                    List of reviewers (valid usernames) for the Pull Request.
    """
    p= _prep_pr_payload(**kwargs)
    if p != None:
        ret = bitbucket.post_pullrequest(creds, kwargs['repository_owner'], kwargs['repository_name'], p)
        if ret.succeeded:
            try:
                j = json.loads(ret.response.text, object_pairs_hook=OrderedDict)
                r = {'number': j['id'], 'pr_url': j['links']['html']['href'], 'pr_diff_url': j['links']['diff']['href']}
            except ValueError as e:
                logger.error("Failed to load Pull Request response as JSON. Reason: '{}', Response: '{}'.".format(str(e), ret.response))
                return {'number': 'N/A', 'pr_url': 'N/A', 'pr_diff_url': 'N/A'}
            except KeyError as e:
                logger.error("Failed to process Pull Request response. Reason: '{}'.".format(str(e)))
                return {'number': 'N/A', 'pr_url': 'N/A', 'pr_diff_url': 'N/A'}
            else:
                return r
        else:
            logger.error("Failed to submit a Pull Request. Reason: '{}'.".format(ret.message))
            return None
    else:
        logger.error("Failed to submit a Pull Request. Failed to create a payload.")
        return None

