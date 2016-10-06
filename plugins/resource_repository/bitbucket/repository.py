import sys
import os
import json
import urllib

from core.common.results import PullRequestResults
from core.resource_repository import ResourceRepository, Resource, ResourceBundle
from core.git.repository import GitRepository

import api as bitbucket
import utils as utils

class BitbucketRepository(ResourceRepository):
    def __init__(self, config, creds, log_dir):
        self.config = config
        self._log_dir = log_dir
        self._repository_owner = config.get_repository_owner()
        self._repository_name = config.get_repository_name()
        # add ????
        # self._repository_platform
        # self._repository_url
        # etc
        self.local_repo = self._create_local_repository(config, creds)
        self._import_entries = []

    def _create_local_repository(self, config, creds):
        repo = GitRepository(config.get_repository_url(), config.get_repository_owner(), config.get_repository_name(), config.get_repository_branch(), creds)
        return repo

    def get_repository_name(self):
        return self._repository_name

    def get_repository_platform(self):
        return self.config.get_repository_platform() 

    def get_repository_url(self):
        return self.config.get_repository_url()

    def get_local_resource_path(self, resource_path):
        return self.local_repo.get_local_resource_path(resource_path)

    def isfile(self, file_path):
        return self.local_repo.isfile(file_path)

    def clone(self):
        username = urllib.quote(self.local_repo.get_user_name(), safe='')
        userpasswd = urllib.quote(self.local_repo.get_user_passwd(), safe='')
        orig_url = self.local_repo.get_repository_url()
        url = orig_url[0:8] + username + ':' + userpasswd + '@' + orig_url[8:]
        return self.local_repo.clone(repository_url_with_creds_embedded=url)

    def _create_resource(self, repository_name, resource_index):
        return Resource(repository_name,
                    self.config.get_resource_path(resource_index),
                    self.config.get_resource_filetype(resource_index),
                    self.config.get_resource_language_code(resource_index),
                    self.config.get_resource_translation(resource_index)
                    )

    def get_resource_bundle(self):
        resources = []
        n = self.config.get_resource_len()
        for i in range(0, n):
            resources.append(self._create_resource(self.config.get_repository_name(), i))
        return  ResourceBundle(self.local_repo, resources, self._log_dir)

    def _add_import_entry(self, translation_bundles):
        options = self.config.get_options()
        if 'hold_pullrequest_until_all_languages_completes' in options:
            if options['hold_pullrequest_until_all_languages_completes']:
                sys.stdout.write("hold_pullrequest_until_all_languages_completes: true\n")
                self._add_import_entry_with_all_languages(translation_bundles)
            else:
                sys.stdout.write("hold_pullrequest_until_all_languages_completes: false\n")
                self._add_import_entry_with_any_languages(translation_bundles)
        else:
            self._add_import_entry_with_any_languages(translation_bundles)

    def _add_import_entry_with_any_languages(self, translation_bundles):
        if len(translation_bundles) == 0: 
            return
        for bundle in translation_bundles:
            sys.stdout.write("Handling bundle...\n")
            for translation in bundle:
                # ensure both translation path and local path are required in order to perfom importing a translation.
                #
                # if the translation_path is not set (means it is not listed in resource config), it is considered as
                # resource repository is not ready for importing the translation.
                #
                # currently, translation's local_path is set only when translation is completed AND translation path is
                # set in resource config.
                if translation.translation_path and translation.local_path:    
                    self._import_entries.append({'translation_path': translation.translation_path, 'local_path': translation.local_path})
                    sys.stdout.write("+'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.translation_path))
                else:
                    # TODO --- diplaying download status might be more informative.
                    sys.stdout.write("-'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.translation_path))

    def _add_import_entry_with_all_languages(self, translation_bundles):
        if len(translation_bundles) == 0:
            return
        for bundle in translation_bundles:
            sys.stdout.write("Handling bundle...\n")
            incompleted_translation = 0
            candidates = []
            for translation in bundle:
                # ensure both translation path and local path are required in order to perfom importing a translation.
                #
                # if the translation_path is not set (means it is not listed in resource config), it is considered as
                # resource repository is not ready for importing the translation.
                #
                # currently, translation's local_path is set only when translation is completed AND translation path is
                # set in resource config.
                if translation.translation_path:
                    if translation.local_path:
                        candidates.append({'translation_path': translation.translation_path, 'local_path': translation.local_path})
                        sys.stdout.write("+'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.translation_path))
                    else:
                        incompleted_translation += 1
                else:
                    # TODO --- diplaying download status might be more informative.
                    sys.stdout.write("-'{}': Local path: '{}' ('{}').\n".format(translation.language_code, translation.local_path, translation.translation_path))

            if incompleted_translation == 0 and len(candidates) >= 1:
                for candidate in candidates:
                    self._import_entries.append(candidate)


    def import_bundles(self, translation_bundles):
        self._add_import_entry(translation_bundles)
        if len(self._import_entries) == 0:
            message = "Nothing to import (_import_entries is empty)."
            self._write_execstats("SUCCESS", message, None, None)
            sys.stdout.write("{}\n".format(message))
            return

        creds = self.local_repo.get_creds()
        pr_title_to_find = self.config.get_pullrequest_title()
        ret = utils.get_file_paths_in_open_pullrequests(self._repository_owner, self._repository_name, pr_title_to_find, creds)
        if not ret.succeeded:
            message = "Aborted importing bundle due to failure on checking files in open pullrequests. Reason: '{}'.".format(ret.message)
            self._write_execstats("FAILURE", message, None, None)
            sys.stderr.write("{}\n".format(message))
            return None

        final_entries = []
        for import_entry in self._import_entries:
            if any(import_entry['translation_path'] in desc for desc in ret.output):
                sys.stdout.write("In open pullrequest: '{}'\n".format(import_entry['translation_path']))
            else:
                sys.stdout.write("Not in open pullrequest: '{}'\n".format(import_entry['translation_path']))
                final_entries.append({'translation_path': import_entry['translation_path'], 'local_path': import_entry['local_path']})

        if len(final_entries) == 0:
            message = "Nothing to import (final_entries is empty)."
            self._write_execstats("SUCCESS", message, None, None)
            sys.stdout.write("{}\n".format(message))
            return None

        return self.local_repo.update_files_in_new_branch(final_entries)

    def _write_execstats(self, results, reason, status_code, pullrequest_url):
        d = {
            "operation": "TranslationUpload",
            "results": results,
            "reason": reason,
            "status_code": status_code,
            "pullrequest_url": pullrequest_url
        }
        sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))

    def _generate_pullrequest_description(self, file_paths):
        return 'Translation Process Automation generated string (DO NOT EDIT): [' + ','.join(file_paths) + ']' 

    #def _set_remote_url(self):
    #    url = "https://{}:{}@bitbucket.org/{}/{}.git".format(
    #            self.local_repo.get_user_name(),
    #            self.local_repo.get_user_passwd(),
    #            self.local_repo.get_repository_owner(),
    #            self.local_repo.get_repository_name())
    #    return self.local_repo.set_remote_url(url)

    def submit_pullrequest(self, merge_branch_name, additional_reviewers):
        staged_files = self.local_repo.get_staged_file(merge_branch_name)
        if len(staged_files) == 0:
            message = "PR not submitted because no updates in branch: '{}'.".format(merge_branch_name)
            self._write_execstats("SUCCESS", message, None, None)
            return PullRequestResults(0, False, message, None, None, None, None)

        sys.stdout.write("Updated files in branch: '{}'\n".format(merge_branch_name))
        for ent in staged_files:
            sys.stdout.write("- '{}'\n".format(ent))

        #if not self._set_remote_url():
        #    message = "Not submitted PR. Failed to set remote url."
        #    self._write_execstats("FAILURE", message, None, None)
        #    return PullRequestResults(1, False, message, None, None, None, None)

        if not self.local_repo.push_branch(merge_branch_name):
            message = "Not submitted PR. Failed to push branch: '{}'.".format(merge_branch_name)
            self._write_execstats("FAILURE", message, None, None)
            return PullRequestResults(1, False, message, None, None, None, None)

        ret = bitbucket.submit_pullrequest(self._repository_owner,
                                        self._repository_name,
                                        merge_branch_name,
                                        self.local_repo.get_repository_branch_name(),
                                        self.config.get_pullrequest_title(),
                                        self._generate_pullrequest_description(staged_files),
                                        list(set(self.config.get_pullrequest_reviewers() + additional_reviewers)),
                                        self.local_repo.get_creds()
                                        )

        if not ret.succeeded:
            message = "Failed to submit PR. Reason: '{}'.".format(ret.message)
            self._write_execstats("FAILURE", message, None, None)
            return PullRequestResults(1, False, message, None, None, None, None)

        ret2 = utils.get_pullrequest_details(ret.response.text)
        if not ret2.succeeded:
            message = "Submitted PR but failed to obtain PR details." 
            sys.stderr.write("Failed to obtain PR details.\n")
            sys.stderr.write("{}\n".format(ret2.message))
            self._write_execstats("FAILURE", message, None, None)
            return PullRequestResults(1, True, message, None, None, None, None)

        try:
            number = ret2.output['number']
            url = ret2.output['pr_url']
            diff_url = ret2.output['pr_diff_url']
            message = "Submitted a PR."
            self._write_execstats("SUCCESS", message, ret.response.status_code, url)
            return PullRequestResults(0, True, message, ret.response.status_code, number, url, diff_url)
        except KeyError as e:
            message = "Submitted a PR but failed to parse PR details. Reason: '{}'".format(e)
            sys.stderr.write('{}\n'.format(ret2.output))
            sys.stderr.write('{}\n'.format(message))
            self._write_execstats("SUCCESS", message, ret.response.status_code, None)
            return PullRequestResults(1, True, message, None, None, None, None)

