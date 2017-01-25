import os
import sys
import json
import codecs
from hashlib import sha1
from shutil import copyfile

import logging
logger = logging.getLogger('tpa')

import settings
from core.plugins.repository_base import TranslationRepository, TranslationBundle, Translation
import utils
import creds

class CrowdinRepository(TranslationRepository):
    def __init__(self, config, creds, log_dir):
        super(CrowdinRepository, self).__init__(config, log_dir)
        #self._crowdin_resource_slug_prefix = creds.resource_slug_prefix 
        # FIXME --- until removing translation config files, config.project_name has to be resource repository name so
        #           that the following code can construct a correct project id.
        self._project_id = creds.project_slug_prefix + config.project_name
        self._crowdin_project_key = self._find_project_key(creds.project_keys)
        self._log_dir = log_dir

    def _find_project_key(self, keys):
        for key in keys:
            for k, v in key.items():
                if k == self._project_id:
                    return v
        else:
            logger.info("Project id not found: '{}'.".format(pkey))
            return None

    def import_resource(self, resource):
        return self._upload(self._project_id, resource.repository_name, resource.repository_branch, resource.resource_path, resource.local_path)

    def get_translation_bundle(self, repository_name, repository_branch, resource_path, resource_translations):
        translations = []
        for translation in resource_translations:
            translations.append(Translation(repository_name, repository_branch, resource_path, translation.path, translation.language_code.strip().rstrip()))
        return TranslationBundle(self, translations, self._log_dir)

    def _upload(self, project_slug, repository_name, repository_branch, resource_path, import_file_path):
        renamed_import_file_path = import_file_path + os.path.splitext(resource_path)[1]
        os.rename(import_file_path, renamed_import_file_path)
        crowdin_resource_path = resource_path

        d = {
            "operation": "ResourceUpload",
            "resource_full_path": os.path.join(repository_name, resource_path),
            "status_code": "N/A",
            "project_slug": project_slug,
            "crowdin_resource_path": crowdin_resource_path,
            "new_strings": "N/A",
            "mod_strings": "N/A",
            "del_strings": "N/A"
            }
        if utils.update_file(self._crowdin_project_key, project_slug, repository_branch, crowdin_resource_path, renamed_import_file_path):
            os.rename(renamed_import_file_path, renamed_import_file_path + '_crowdin_imported')
            d['results'] = 'SUCCESS'
            logger.info("ExecStats='{}'.".format(json.dumps(d)))
            return True
        else:
            os.rename(renamed_import_file_path, renamed_import_file_path + '_import_failed')
            d['results'] = 'FAILURE'
            logger.info("ExecStats='{}'.".format(json.dumps(d)))
            return False

    def download_translation(self, repository_name, repository_branch, resource_path, language_code):
        if utils.all_strings_approved(self._crowdin_project_key, self._project_id, repository_branch, resource_path, language_code):
            dest = os.path.join(self._log_dir, os.path.basename(resource_path) + '_' + language_code)
            if os.path.isfile(dest):
                os.remove(dest)
            return utils.export_file(self._crowdin_project_key, self._project_id, repository_branch, resource_path, language_code, dest)
        else:  
            return None

    def get_stats_project(self):
        # NIY
        return None
