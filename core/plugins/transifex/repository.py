import os
import sys
import re
import json
import codecs
import requests
from requests.exceptions import ConnectionError
from hashlib import sha1
from collections import namedtuple

import logging
logger = logging.getLogger('tpa')

from core.plugins.repository_base import TranslationRepository, TranslationBundle, Translation

from . import api as transifex
from . import utils as utils 

# Credentials for Transifex APIs
#
# keys                  values
# -------------------------------------------
# username              user name
# userpasswd            user password
TransifexApiCreds = namedtuple('TransifexApiCreds', 'username, userpasswd')

class TransifexRepository(TranslationRepository):
    def __init__(self, config, creds, log_dir):
        super(TransifexRepository, self).__init__(config, log_dir)
        self._transifex_project_slug_prefix = creds.project_slug_prefix
        self._transifex_resource_slug_prefix = creds.resource_slug_prefix
        self._api_creds = TransifexApiCreds(creds.username, creds.userpasswd)
        self._log_dir = log_dir

    def generate_project_slug(self, project_name):
        return utils.generate_project_slug(self._transifex_project_slug_prefix, project_name)

    def generate_resource_slug(self, seeds):
        return utils.generate_resource_slug(self._transifex_resource_slug_prefix, seeds)

    def import_resource(self, resource):
        pslug = self.generate_project_slug(self.config.project_name)
        if not pslug:
            return False

        logger.info("Destination project: {} ({})".format(pslug, self.config.project_name))

        rslug = self.generate_resource_slug([resource.repository_name, resource.resource_path])
        if not rslug:
            return False

        logger.info("Destination Resource: {}".format(rslug))

        ret = transifex.put_resource(pslug, rslug, resource.local_path, resource.repository_name, resource.resource_path, self._api_creds)
        if not ret.succeeded:
            self._display_upload_stats('N/A', ret.message, pslug, rslug, os.path.join(resource.repository_name, resource.resource_path))
            return False

        # TODO --- this can be move to util
        self._display_upload_stats(ret.response.status_code, ret.response.text, pslug, rslug, os.path.join(resource.repository_name, resource.resource_path))
        os.rename(resource.local_path, os.path.join(self._log_dir, rslug + '_import_failed'))
        return True

    def get_translation_bundle(self, repository_name, resource_path, resource_translations):
        translations = []
        for lang_code in self.config.project_language_codes:
            for translation in resource_translations:
                if lang_code == translation.language_code:
                    translation_path = translation.path
                    break
            else:
                translation_path = None
            translations.append(Translation(repository_name, resource_path, translation_path, lang_code.strip().rstrip()))

        return TranslationBundle(self, translations, self._log_dir)

    # TODO ---  part where it handles response_text can move to util
    def _display_upload_stats(self, status_code, response_text, project_slug, resource_slug, resource_full_path): 
        num_new = 'n/a'
        num_mod = 'n/a'
        num_del = 'n/a'
        result = 'FAILURE'
        if status_code == 200 or status_code == 201:
            logger.info(response_text)
            try:
                j = json.loads(response_text)
            except ValueError as e:
                logger.error("Failed read response result as json. Reason: '{}'.".format(e))
            else:
                num_new = j['strings_added']
                num_mod = j['strings_updated']
                num_del = j['strings_delete']
                result = 'SUCCESS'
        else:
            logger.error(response_text)
        
        d = {
            "operation": "ResourceUpload",
            "results": result,
            "resource_full_path": resource_full_path,
            "status_code": status_code,
            "project_slug": project_slug,
            "resource_slug": resource_slug,
            "new_strings": num_new,
            "mod_strings": num_mod,
            "del_strings": num_del
            }
        logger.info("ExecStats='{}'".format(json.dumps(d)))

    def _write_failure_language_stats(self, repository_name, resource_path, language_code, message):
        d = {}
        d['repository_name'] = repository_name
        d['reosurce_path'] = resource_path
        d['language_code'] = language_code
        d['message'] = message
        logger.info('LanguageStats=' + json.dumps(d))

    # TODO --- handing response_text part can move to util
    def _write_language_stats(self, repository_name, resource_path, language_code, pslug, rslug, response_text):
        try:
            d = json.loads(response_text)
        except ValueError as e:
            self._write_failure_language_stats(repository_name, resource_path, language_code, "Failed to read language status as json. Reason: '{}'.".format(e))
            return

        d['repository_name'] = repository_name
        d['reosurce_path'] = resource_path
        d['language_code'] = language_code
        d['project_slug'] = pslug
        d['resource_slug'] = rslug
        d['operation'] = 'GetLanguageStats'
        logger.info('LanguageStats=' + json.dumps(d))

    def download_translation(self, repository_name, resource_path, language_code):
        pslug = self.generate_project_slug(self.config.project_name)
        if not pslug:
            self._write_failure_language_stats(repository_name, resource_path, language_code, "Failed to generate project slug.")
            return None

        rslug = self.generate_resource_slug([repository_name, resource_path])
        if not rslug:
            self._write_failure_language_stats(repository_name, resource_path, language_code, "Failed to generate resource slug.")
            return None

        ret = transifex.get_language_stats(pslug, rslug, language_code, self._api_creds)
        if not ret.succeeded:
            self._write_failure_language_stats(repository_name, resource_path, language_code, "Failed to obtain language stats.")
            return None

        self._write_language_stats(repository_name, resource_path, language_code, pslug, rslug, ret.response.text)
        if not utils.translation_review_completed(ret.response.text):
            logger.info("Review not completed: {}, pslug: '{}', rslug: '{}'".format(language_code, pslug, rslug))  
            return None

        return self._download_translation(pslug, rslug, language_code)

    def _store_raw_download_file(self, raw_download_path, get_translation_response_text):
        if os.path.isfile(raw_download_path):
            os.remove(raw_download_path)

        if sys.version_info[0:1] == (2,):
            with codecs.open(raw_download_path, 'w', encoding='utf-8') as fo:
                fo.write(get_translation_response_text)
        else:
            with open(raw_download_path, 'w') as fo:
                fo.write(get_translation_response_text)

    def _store_translation(self, download_path, translation_content):
        if os.path.isfile(download_path):
            os.remove(download_path)
        
        if sys.version_info[0:1] == (2,):
            with codecs.open(download_path, 'w', encoding='utf-8') as fo:
                fo.write(translation_content)
        else:
            with open(download_path, 'w') as fo:
                fo.write(translation_content)

    def _download_translation(self, project_slug, resource_slug, language_code):
        ret = transifex.get_translation_reviewed(project_slug, resource_slug, language_code, self._api_creds)
        if not ret.succeeded:
            logger.error("Failed to download translation.")
            return None

        raw_download_path = os.path.join(self._log_dir, resource_slug + '_' + language_code + '_raw')
        self._store_raw_download_file(raw_download_path, ret.response.text)

        c = utils.get_translation_content(ret.response.text)
        if not c:
            logger.error("Failed read raw download.")
            return None

        download_path = os.path.join(self._log_dir, resource_slug + '_' + language_code)
        self._store_translation(download_path, c)
        logger.info("Donloaded: {}".format(download_path))
        return os.path.abspath(download_path)

    # TODO --- util/tpa_utils.py uses this to extract project/resource names and slugs
    #          from response text.
    #          re-write to get project/resource name and slugs via transifex/transifex_utils. 
    def get_stats_project(self):
        project_slug = self.generate_project_slug(self.config.project_name)
        ret = transifex.get_project_details(project_slug, self._api_creds)
        if ret.succeeded:
            return ret.response.text
        else:
            return None

