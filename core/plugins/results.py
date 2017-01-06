import sys
from collections import namedtuple

# RestApiResults
# This is returned by functions to call REST APIs.
#
#   .succeeded: True when REST API call is succeeded (eg. 200 or 201). False, otherwise.
#   .response: 
#       .succeeded=True: Raw response data returned by request().
#       .succeeded=False: None.
#   .message:
#       .succeeded=True: Usually None, but there might be extra message.
#       .succeeded=False: Exception message.
RestApiResults = namedtuple('RestApiResults', 'succeeded, response, message')
def succeeded_rest_api_call_results(response, message=None):
    return RestApiResults(True, response, message)

def failed_rest_api_call_results(exception):
    return RestApiResults(False, None, "{}".format(str(exception)))


# UtilCallResults
#   UtilCallResults are currently only used in git/commands.py.
#
#   .succeeded: True on success, otherwise False.
#   .output: 
#       .succeeded=True: Desired output. Data type depeneds on the util function.
#       .succeeded=False: None.
#   .message:
#       .succeeded=True: Usually None, but there might be extra message.
#       .succeeded=False: Exception message.
UtilCallResults = namedtuple('UtilCallResults', 'succeeded, output, message')
def succeeded_util_call_results(output, message=None):
    return UtilCallResults(True, output, message)

def failed_util_call_results(exception):
    return UtilCallResults(False, None, "{}".format(str(exception)))

# PullRequestResults
# This is retuned by ResoruceRepository.submit_pullrequest().
#
#   .errors: Number of errors while processing a pull request.
#               NOTE:
#               A PR can be issued with some errors.
#   .submitted: True when a pull request is submitted. False otherwise.
#   .message: Additional message when a pull request is submitted or error message when error occurs.
#   .status_code: Response status_code if a pull request is submitted. None, otherwise.
#   .number: Pull request number.
#   .url: URL to the submitted pull request.
#   .diff_url: URL to the diff page of the submitted pull request.
PullRequestResults = namedtuple('PullRequestResults', 'errors, submitted, message, status_code, number, url, diff_url')
def succeeded_pullrequest_results(error, message=None, status_code=None, number=None, url=None, diff_url=None):
    return PullRequestResults(errors, True, message, status_code, number, url, diff_url)

def failed_pullrequest_results(errors, message, status_code=None, number=None, url=None, diff_url=None):
    return PullRequestResults(errors, False, message, status_code, number, url, diff_url)

