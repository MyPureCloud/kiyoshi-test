import json
from collections import OrderedDict

import logging
logger = logging.getLogger('tpa')

import api as github_api

def _prep_pr_payload(**kwargs):
    try:
        reviewers = []
        if 'pr_reviewers' in kwargs:
            for s in kwargs['pr_reviewers']:
                reviewers.append({'username': s})
            p = json.dumps({
                'title': kwargs['pr_title'],
                'body': kwargs['pr_description'],
                'head': kwargs['feature_branch_name'],
                'base': kwargs['destination_branch_name']
                }, ensure_ascii=False)
    except KeyError as e:
        logger.error("Failed to prepare payload for a Pull Request. Reason: '{}'.".format(str(e)))
        return None
    else:
        return p

def _create_review_request(creds, repository_owner, repository_name, pr_number, reviewers):
    if len(reviewers) == 0:
        logger.info("No reviewers specified for pull request #{}.".format(pr_number))
        return

    p = json.dumps({'reviewers': reviewers}, ensure_ascii=False)
    ret = github_api.post_review_request(creds, repository_owner, repository_name, pr_number, p)
    if ret.succeeded:
        logger.info("Added reviewers for pull request #{}: {}.".format(pr_number, ','.join(reviewers)))
    else:
        logger.error("Failed to create review request. Reason: '{}'.".format(ret.message))

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
    if p == None:
        logger.error("Failed to create a payload. Pull request not submitted.")
        return None

    ret = github_api.post_pullrequest(creds, kwargs['repository_owner'], kwargs['repository_name'], p)
    if ret.succeeded:
        try:
            j = json.loads(ret.response.text, object_pairs_hook=OrderedDict)
            pr_url = j['html_url']
            pr_diff_url = j['diff_url']
            pr_number = j['number']
        except ValueError as e:
            logger.error("Failed to load pull request response as JSON. Reason: '{}', Response: '{}'.".format(str(e), ret.response))
            return {'number': 'N/A', 'pr_url': 'N/A', 'pr_diff_url': 'N/A'}
        except KeyError as e:
            logger.error("Failed to process pull request response. Reason: '{}'.".format(str(e)))
            return {'number': 'N/A', 'pr_url': 'N/A', 'pr_diff_url': 'N/A'}
        else:
            _create_review_request(creds, kwargs['repository_owner'], kwargs['repository_name'], pr_number, kwargs['pr_reviewers'])
            return {'number': pr_number, 'pr_url': pr_url, 'pr_diff_url': pr_diff_url}
    else:
        logger.error("Failed to submit a pull request. Reason: '{}'.".format(ret.message))
        return None

def get_pullrequests(creds, repository_owner, repository_name, pullrequest_state_strings, author, limit):
    """
    Return list of Pull Request information as follows.
    Or, return None on any errors.

        state               State of the Pull Request.
        number              Pull Request number.
        title               Title of the Pull Request.
        description         Pull Request description.
        submitter           Username who submitted the Pull Request.
        date                Pull Request submission date.
        pr_url              URL to the Pull Request page.
        pr_diff_url         URL to the Pull Request (diff) page.

    author is to specify submitter of pull requests.
    pullrequest_state_strings is a list of none or any combination of 'open' and 'closed'.
    limit is to specify number of pull requests to query.
    """
    # FIXME
    # query issues only once with assuming github returns enough issues...
    ret = github_api.search_issues(repository_owner, repository_name, author, {'username': creds['username'], 'userpasswd': creds['userpasswd']})
    if not ret.succeeded:
        logger.error("Failed to search github issues. Reason: '{}'.".format(ret.message))
        return None
    
    try:
        j = json.loads(ret.response.text, object_pairs_hook=OrderedDict)
        r = []
        count = 0
        for x in j['items']:
            if count < limit and x['state'] in pullrequest_state_strings:
                r.append({
                    'state': x['state'],
                    'number': x['number'],
                    'title': x['title'],
                    'description': x['body'],
                    'submitter': x['user']['login'],
                    'date': x['created_at'],
                    'pr_url': x['pull_request']['html_url'],
                    'pr_diff"url': x['pull_request']['diff_url']
                    })
                count += 1
            else:
                break
    except ValueError as e:
        logger.error("Failed to load github query result as json. Reason: '{}'.".format(e))
        return None
    except KeyError as e:
        logger.error("Failed to process github query result. Reason: '{}'.".format(e))
        return None
    else:
        return r

