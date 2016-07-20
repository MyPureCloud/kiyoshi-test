import os, sys, re, requests, json, codecs
from requests.exceptions import ConnectionError
from hashlib import sha1
from shutil import copyfile

import settings
from CrowdinCredsConfigurationClass import CrowdinCredsConfiguration
from TranslationRepositoryClass import TranslationRepository, TranslationBundle, Translation

class CrowdinTranslationDownload:
    def __init__(self):
        self.path = str()
        self.status = str()
        self.errors = 0

class CrowdinRepository(TranslationRepository):
    def __init__(self, config, log_dir):
        super(CrowdinRepository, self).__init__(config, log_dir)
        self._crowdin_resource_slug_prefix = str()
        self._crowdin_project_key = str() 
        self._log_dir = log_dir

    def _set_crowdin_creds(self):
        if not os.path.isfile(settings.CROWDIN_CREDS_FILE):
            sys.stderr.write("File not found: {}.\n".format(settings.CROWDIN_CREDS_FILE))
            return False

        t = CrowdinCredsConfiguration()
        if not t.parse(settings.CROWDIN_CREDS_FILE):
            sys.stderr.write("Failed to parse: {}\n".format(settings.CROWDIN_CREDS_FILE))
            return False
        else:
            self._crowdin_resource_slug_prefix = t.get_resource_slug_prefix()
            self._crowdin_project_key = self._find_project_key( t.get_project_keys())
            if self._crowdin_project_key:
                return True
            else:
                return False

    def _get_project_id(self):
        """ Crowdin has project identifier but it is not editable.
            Thus auto generating project id by project name is not a good way.
            So, use config project name field for crowdin project id. 
        """
        return self.config.get_project_name()

    def _find_project_key(self, keys):
        pkey = self._get_project_id()
        if not pkey:
            self._crowdin_project_key = None
            return

        for key in keys:
            for k, v in key.items():
                if k == pkey:
                    return v
        else:
            sys.stdout.write("Project id not found: '{}'\n".format(pkey))
            return None

    def generate_resource_slug(self, seeds, extension):
        """ A resource slug format is
                <resource slug prefix><sha1>.<resource filename extension>
            <sha1> is generated by given string 'seeds'.

            Crowdin does not use resource slug. A resource has to be identified by path in a project.
                e.g. /master/src/strings/en-Us.json

            TPA does not use particular directory structure to store resource files in a project.
            All resource files are put in root directory with the resource slug as file name.

                e.g. /inin-2c23541d082178afb8c00c336e401f41e49642f3.json

            In Clowdin UI, 'title' is given to the resource file so that the file name becomes more
            meaningful for translators.

                e.g. /PCL Cocoa Documents
        """
        if not self._crowdin_resource_slug_prefix:
            self._set_crowdin_creds()

        text = ''.join(seeds).encode('utf-8')
        if self._crowdin_resource_slug_prefix:
            return '{}{}.{}'.format(self._crowdin_resource_slug_prefix, sha1(text).hexdigest(), extension)
        else:
            return '{}.{}'.format(sha1(text).hexdigest(), extention)

    def import_resource(self, resource):
        pid = self._get_project_id()
        extension = os.path.splitext(os.path.basename(resource.resource_path))[1][1:]
        rslug = self.generate_resource_slug([resource.repository_name, resource.resource_path], extension)
        if not rslug:
            return False
        else:
            sys.stdout.write("Destination Resource: {}\n".format(rslug))

        return self._upload(pid, rslug, resource.local_path, resource.repository_name, resource.resource_path)

    def get_translation_bundle(self, repository_name, resource_path, resource_translations):
        translations = []
        for lang_code in self.config.get_project_languages():
            for translation in resource_translations:
                if lang_code == translation.language_code:
                    translation_path = translation.path
                    break
            else:
                translation_path = None
            translations.append(Translation(repository_name, resource_path, translation_path, lang_code.strip().rstrip()))
        return TranslationBundle(self, translations, self._log_dir)

    def _get_language_stats(self, project_slug, resource_slug, language_code):
        if not self._crowdin_project_key:
            self._set_crowdin_creds()

        if not self._crowdin_project_key:
            sys.stderr.write("Project key not found for '{}'.\n".format(project_slug))
            return {} 

        params = {'language': language_code, 'json': True}
        url = 'http://api.crowdin.com/api/project/{}/language-status?key={}'.format(project_slug, self._crowdin_project_key)
        try:
            r = requests.post(url, params=params)
        except ConnectionError as e:
            sys.stderr.write("{}\n".format(e))
            return {}

        try:
            j = json.loads(r.text)
        except ValueError as e:
            sys.stderr.write("Failed to read language status as json. Reason: '{}'.\n".format(e))
            sys.stderr.write("Response context...\n")
            sys.stderr.write(r.text + '\n')
            return {}
        else:
            # TODO --- too many lines. make it one line or so.
            sys.stdout.write("language: '{}'\n".format(language_code))
            sys.stdout.write(r.text + '\n')
        
        for entry in j['files']:
            if entry['node_type'] == 'file' and entry['name'] == resource_slug:
                return entry
        else:
            return {}

    def _is_review_completed(self, stats, resource_filename):
        return (stats['approved'] == stats['phrases']) and (stats['translated'] == stats['phrases'])

    def _display_upload_stats(self, status_code, response_text, project_slug, crowdin_resource_path, resource_full_path): 
        if status_code == 200 or status_code == 201:
            sys.stdout.write(response_text + "\n")
            try:
                j = json.loads(response_text)
            except ValueError as e:
                sys.stderr.write("Failed read response result as json. Reason: '{}'.\n".format(e))
            else:
                if j['success'] ==  'true' or j['success'] == True:
                    result = 'SUCCESS'
                else:
                    result = 'FAILURE'
        else:
            result = 'FAILURE'
            sys.stderr.write(response_text + "\n")
        
        d = {
            "operation": "ResourceUpload",
            "results": result,
            "resource_full_path": resource_full_path,
            "status_code": status_code,
            "project_slug": project_slug,
            "crowdin_resource_path": crowdin_resource_path,
            "new_strings": 'n/a',
            "mod_strings": 'n/a',
            "del_strings": 'n/a'
            }
        sys.stdout.write("ExecStats='{}'\n".format(json.dumps(d)))

    def _upload(self, project_slug, resource_slug, import_file_path, repository_name, resource_path):
        if not self._crowdin_project_key:
            self._set_crowdin_creds()

        if not self._crowdin_project_key:
            sys.stderr.write("Project key not found for '{}'.\n".format(project_slug))
            return False 

        # Crowein requires identical filename extension for uploading file and destination file in crowdin.
        crowdin_resource_path = os.path.join('/', resource_slug)
        renamed_import_file_path = import_file_path + os.path.splitext(crowdin_resource_path)[1]
        os.rename(import_file_path, renamed_import_file_path)

        url = 'https://api.crowdin.com/api/project/{}/update-file?key={}'.format(project_slug, self._crowdin_project_key)
        payload = {'json': True}
        fi = open(renamed_import_file_path, 'r')
        files = {'files[{}]'.format(crowdin_resource_path): fi} 

        try:
            r = requests.post(url, params=payload, files=files)
        except ConnectionError as e:
            fi.close()
            sys.stderr.write("{}\n".format(e))
            return False 
        else:
            fi.close()

        self._display_upload_stats(r.status_code, r.text, project_slug, crowdin_resource_path, os.path.join(repository_name, resource_path)) 
        # TODO --- when uploading resource file does not contain changes, crowdin 'skips' uploading. 
        #          Here, both 'skip' and 'updated' are treated as 'imported'.
        if r.status_code == 200 or r.status_code == 201:
            os.rename(renamed_import_file_path, os.path.join(self._log_dir, resource_slug + '_crowdin_imported'))
            return True
        else:
            os.rename(renamed_import_file_path, os.path.join(self._log_dir, resource_slug + '_import_failed'))
            return False

    def download_translation(self, repository_name, resource_path, language_code):
        download = CrowdinTranslationDownload()        
        pid = self._get_project_id()
        extension = os.path.splitext(os.path.basename(resource_path))[1][1:]
        rslug = self.generate_resource_slug([repository_name, resource_path], extension)
        if not rslug:
            download.errors += 1
            download.status = "Failed to generate resource slug."
            return download

        d = self._get_language_stats(pid, os.path.basename(rslug), language_code)
        if not d: 
            download.errors += 1
            download.status = "Failed to obtain language stats."
            return download

        d['repository_name'] = repository_name
        d['reosurce_path'] = resource_path
        d['language_code'] = language_code
        d['project_id'] = pid
        d['resource_slug'] = rslug
        sys.stdout.write('LanguageStats=' + json.dumps(d) + '\n')

        if self._is_review_completed(d, rslug):
            self._download_translation(download, pid, rslug, language_code)
        else:  
            download.status = "Review not completed: {}, pid: '{}', rslug: '{}'".format(language_code, pid, rslug)   
        return download

    def _download_translation(self, crowdin_download_obj, project_slug, resource_slug, language_code):
        if not self._crowdin_project_key:
            self._set_crowdin_creds()

        if not self._crowdin_project_key:
            sys.stderr.write("Project key not found for '{}'.\n".format(project_slug))
            return 

        # TODO --- need to build the project before exporting a translation???

        crowdin_translation_path = os.path.join('/', resource_slug)
        payload = {'json': True}
        url = 'https://api.crowdin.com/api/project/{}/export-file?file={}&language={}&key={}'.format(project_slug, crowdin_translation_path, language_code, self._crowdin_project_key)

        try:
            r = requests.post(url, params=payload)
        except ConnectionError as e:
            sys.stderr.write("{}\n".format(e))
            crowdin_download_obj.errors += 1
            crowdin_download_obj.status = "Failed to download translation."
            return 
        else:
            if not (r.status_code == 200 or r.status_code == 201):
                sys.stderr.write("{}\n".format(r.status_code))
                sys.stderr.write("{}\n".format(r.text))
                crowdin_download_obj.errors += 1
                crowdin_download_obj.status = "Failed to download translation. Status: {}".format(r.status_code)
                return

        # FIXME
        # at this stage, a resource_slug file with 0 byte is created.

        raw_download_path = os.path.join(self._log_dir, resource_slug + '_' + language_code + '_raw')
        if os.path.isfile(raw_download_path):
            os.remove(raw_download_path)

        if sys.version_info[0:1] == (2,):
            with codecs.open(raw_download_path, 'w', encoding='utf-8') as fo:
                fo.write(r.text)
        else:
            with open(raw_download_path, 'w') as fo:
                fo.write(r.text)

        download_path = os.path.join(self._log_dir, resource_slug + '_' + language_code)
        if os.path.isfile(download_path):
            os.remove(download_path)

        with open(raw_download_path, 'r') as fi:
                #if sys.version_info[0:1] == (2,):
                #    with codecs.open(download_path, 'w', encoding='utf-8') as fo:
                #        fo.write(j)
                #else:
                #    with open(download_path, 'w') as fo:
                #        fo.write(j)
                copyfile(raw_download_path, download_path)

                crowdin_download_obj.path = os.path.abspath(download_path)
                crowdin_download_obj.status = "Donloaded: {}".format(download_path)

