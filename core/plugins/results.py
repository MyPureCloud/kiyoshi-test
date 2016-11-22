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
# This is returned by utility functions which process data by calling REST APIs.
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

# ResourceUploadResults
# This is used for ExecStats to represents results of uploading a resource to translation repository.
#
#   .operation: Name of operation 'ResourceUpload'.
#   .results: 'SUCCESS' or 'FAIURE'
#   .message: Additional message or error message when error occurs.
#   .status_code: REST API status code. e.g. '200'
#   .resource_path: resource path in repository. e.g. 'src/strings/en-US.json'
#   .project_slug: Slug of destination project in translation repository.
#   .resource_slug: Slug of destination resource in translation repository.
#   .new_strings: Number of new strings in the resource.
#   .mod_strings: Number of modified strings in the resource.
#   .del_strings: Number of deleted strings in the resource.
#ResourceUploadResults = namedtuple('ResourceUploadResults', 'operation, results, message, status_code, resource_path, project_slug, resource_slug, new_strings, mod_stings, del_strings')

# TranslationUploadResults
# This is used for ExecStats to represents results of uploading translation(s) to resource repository.
#
#   .operation: Name of operation 'TranslationUpload'.
#   .results: 'SUCCESS' or 'FAILURE'.
#   .message: Additional message.
#   .status_code: REST API status code.
#   .pullrequest_url: URL to issued pull request.
#TranslationUploadResults = namedtuple('TranslationUploadResults', 'operation, results, message, status_code, pulllrequest_url')

# LanguageStatus
# This is used for LanguageStats to represents translation status for a particular language in translation repository.
#
#   .operation: Name of operation 'GetLanguageStats'
#   .results: 'SUCCESS' or 'FAILURE'.
#   .message: Additional message.
#   .status_code: REST API status code.
#   .project_slug: Slug of project in translation repository.
#   .resoruce_slug: Slug o resource in the translation repository.
#   .language_code: Language code. e.g. 'es-MX'
#   .repository_name: Name of resource repository.
#   .resource_path: Resource path in the resource repository.
#LanguageStatus = namedtuple('GetLanguageStats', 'operation, results, message, status_code, project_slug, resource_slug, langauge_code, repository_name, resource_path')


