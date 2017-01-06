import sys
import os
import re
import json
from collections import OrderedDict
import urllib

import logging
logger = logging.getLogger('tpa')

from core.plugins.results import PullRequestResults
from core.plugins.git.repository import GitRepository
from core.plugins.repository_base import ResourceRepository, Resource, ResourceBundle
import utils

class GithubRepository(ResourceRepository):
    def __init__(self, config, creds, log_dir):
        self.config = config
        self._log_dir = log_dir
        self._repository_owner = config.repository_owner
        self._repository_name = config.repository_name
        # add ????
        # self._repository_platform
        # self._repository_url
        # etc
        self.local_repo = self._create_local_repository(config, creds)
        self._import_entries = []

    def _create_local_repository(self, config, creds):
        repo = GitRepository(config.repository_url, config.repository_owner, config.repository_name, config.repository_branch, creds)
        return repo

    def get_repository_name(self):
        return self._repository_name

    def get_repository_platform(self):
        return self.config.repository_platform 

    def get_repository_platform(self):
        return self.config.epository_platform 

    def get_repository_url(self):
        return self.config.repository_url

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

    def _set_remote_url(self):
        user_name = self.local_repo.get_user_name()
        user_passwd = self.local_repo.get_user_passwd()
        repository_owner = self.local_repo.get_repository_owner()
        repository_name = self.local_repo.get_repository_name()
        url = "https://{}:{}@github.com/{}/{}.git".format(user_name, user_passwd, repository_owner, repository_name)
        return self.local_repo.set_remote_url(url)

    def get_resource_bundle(self):
        resources = []
        n = len(self.config.resources)
        for i in range(0, n):
            resources.append(self._create_resource(self.config.repository_name, i))

        logger.info("Number of Resource in ResourceBundle: '{}'".format(len(resources)))
        for x in resources:
            logger.info("{}".format(x))

        return  ResourceBundle(self.local_repo, resources, self._log_dir)

    def _create_resource(self, repository_name, resource_index):
        r = Resource(
                repository_name,
                self.config.resources[resource_index].path,
                self.config.resources[resource_index].filetype,
                self.config.resources[resource_index].language_code,
                self.config.resources[resource_index].translations)
        return r

    def _add_import_entry(self, translation_bundles):
        options = self.config.options
        if 'hold_pullrequest_until_all_languages_completes' in options:
            if options['hold_pullrequest_until_all_languages_completes']:
                logger.info("hold_pullrequest_until_all_languages_completes: true")
                self._add_import_entry_with_all_languages(translation_bundles)
            else:
                logger.info("hold_pullrequest_until_all_languages_completes: false")
                self._add_import_entry_with_any_languages(translation_bundles)
        else:
            self._add_import_entry_with_any_languages(translation_bundles)

    def _add_import_entry_with_any_languages(self, translation_bundles):
        if len(translation_bundles) == 0: 
            return
        for bundle in translation_bundles:
            logger.info("Handling bundle...")
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
                    logger.info("+'{}': Local path: '{}' ('{}').".format(translation.language_code, translation.local_path, translation.translation_path))
                else:
                    # TODO --- diplaying download status might be more informative.
                    logger.info("-'{}': Local path: '{}' ('{}').".format(translation.language_code, translation.local_path, translation.translation_path))

    def _add_import_entry_with_all_languages(self, translation_bundles):
        if len(translation_bundles) == 0:
            return
        for bundle in translation_bundles:
            logger.info("Handling bundle...")
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
                        logger.info("+'{}': Local path: '{}' ('{}').".format(translation.language_code, translation.local_path, translation.translation_path))
                    else:
                        incompleted_translation += 1
                else:
                    # TODO --- diplaying download status might be more informative.
                    logger.info("-'{}': Local path: '{}' ('{}').".format(translation.language_code, translation.local_path, translation.translation_path))

            if incompleted_translation == 0 and len(candidates) >= 1:
                for candidate in candidates:
                    self._import_entries.append(candidate)


    def import_bundles(self, translation_bundles):
        self._add_import_entry(translation_bundles)
        if len(self._import_entries) == 0:
            message = "Nothing to import (_import_entries is empty)."
            self._write_execstats("SUCCESS", message, None, None)
            logger.info(message)
            return None

        creds = self.local_repo.get_creds()

        NUM_QUERY = 30
        pr_submitter = creds['username'] # assumes pull request submitter is one who clone the local repository. e.g. TPA admin user 
        l = utils.get_pullrequests(creds, self._repository_owner, self._repository_name, ['open'], pr_submitter, NUM_QUERY)
        if l == None:
            message = "Aborted importing bundle due to failure on checking files in open pullrequests."
            self._write_execstats("FAILURE", message, None, None)
            logger.error(message)
            return None

        final_entries = []
        for import_entry in self._import_entries:
            if any(import_entry['translation_path'] in x['description'] for x in l):
                logger.info("In open Pull Request: '{}'".format(import_entry['translation_path']))
            else:
                logger.info("Not in open Pull Request: '{}'".format(import_entry['translation_path']))
                final_entries.append({'translation_path': import_entry['translation_path'], 'local_path': import_entry['local_path']})

        if len(final_entries) == 0:
            message = "Nothing to import (final_entries is empty)."
            self._write_execstats("SUCCESS", message, None, None)
            logger.info(message)
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
        logger.info("ExecStats='{}'".format(json.dumps(d)))

    def _generate_pullrequest_description(self, file_paths):
        return 'Translation Process Automation generated string (DO NOT EDIT): [' + ','.join(file_paths) + ']' 

    def submit_pullrequest(self, merge_branch_name, additional_reviewers):
        staged_files = self.local_repo.get_staged_file(merge_branch_name)
        if len(staged_files) == 0:
            message = "PR not submitted because no updates in branch: '{}'.".format(merge_branch_name)
            self._write_execstats("SUCCESS", message, None, None)
            return PullRequestResults(0, False, message, None, None, None, None)

        logger.info("Updated files in branch: '{}'".format(merge_branch_name))
        for ent in staged_files:
            logger.info("- '{}'".format(ent))

        if not self._set_remote_url():
            message = "Not submitted PR. Failed to set remote url."
            self._write_execstats("FAILURE", message, None, None)
            return PullRequestResults(1, False, message, None, None, None, None)

        if not self.local_repo.push_branch(merge_branch_name):
            message = "Not submitted PR. Failed to push branch: '{}'.".format(merge_branch_name)
            self._write_execstats("FAILURE", message, None, None)
            return PullRequestResults(1, False, message, None, None, None, None)

        reviewers = list(set(self.config.pullrequest.reviewers + additional_reviewers))
        r = utils.submit_pullrequest(
                self.local_repo.get_creds(),
                repository_owner=self._repository_owner,
                repository_name=self._repository_name,
                feature_branch_name=merge_branch_name,
                destination_branch_name=self.local_repo.get_repository_branch_name(),
                pr_title=self.config.pullrequest.title,
                pr_description=self._generate_pullrequest_description(staged_files),
                pr_reviewers=reviewers
                )

        if r != None:
            self._write_execstats("SUCCESS", "Submitted a pull request.", None, r['pr_url'])
            return PullRequestResults(0, True, "Submitted a pull request.", None, r['number'], r['pr_url'], r['pr_diff_url'])
        else:
            message = "Failed to submit PR."
            self._write_execstats("FAILURE", message, None, None)
            return PullRequestResults(1, False, message, None, None, None, None)

