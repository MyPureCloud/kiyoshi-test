from collections import namedtuple

# Credentials for Transifex APIs
#
# keys                  values
# -------------------------------------------
# username              user name
# userpasswd            user password
TransifexApiCreds = namedtuple('TransifexApiCreds', 'username, userpasswd')

# For Transifex project (summary).
#
# keys                  values
# -------------------------------------------
# slug                  project slug
# name                  project name
# description           project description
TransifexProject = namedtuple('TransifexProject', 'slug, name, description')

# For Transifex project details. 
#
# keys                  values
# -------------------------------------------
# slug                  project slug
# name                  project name
# description           project description
# resources             list of TransifexResource
TransifexProjectDetails = namedtuple('TransifexProjectDetails', 'slug, name, description, resources')

# For Transifex resource (summary).
#
# slug                  resource slug
# name                  resource name
TransifexResource = namedtuple('TransifexResource', 'slug, name')

# For Transifex resource details.
#
# slug                  resource slug
# name                  resource name
# last_updated          last updated date for the resource
# num_strings           number of strings in the resource
# num_words             number of words in the source
# language_code         language code of the resource
TransifexResourceDetails = namedtuple('TransifexResourceDetails', 'slug, name, last_updated, num_strings, num_words, language_code')

# For Transiefx source string details.
#
# comment               instructions attached to the source string
# tags                  list of tags attached to the source string
TransifexSourceStringDetails = namedtuple('TransifexSourceStringDetails', 'comment, tags')

# For Transifex translation strings details.
#
# 
#
# key                   key for the string.
# source_string         source string.
# translation           translation for the string.
# reviewed              true when reviewed, false otherwise.               
# last_update           last updated date.
TransifexTranslationStringDetails = namedtuple('TransifexTranslationStringDetails', 'key, source, translation, reviewed, last_updated')

# For Transifex translation stats for a resource.
#
# project_slug                  project slug
# resource_slug                 resource slug
# name                          resource name
# language_code                 language code of this stats
# last_updated                  last updated date for the resource
# last_updated_by               who last updated the resource
# num_reviewed_strings          number of reviewed strings.
# percentage_reviewed_strings   percentage of reviewed strings. e.g. '80%'
# num_translated_strings        number of translated strings.
# num_untranslated_strings      number of untranslated strings.
# percentage_translated_strings percentage of translated strings. e.g. '80%'
# num_translated_words          number of translated words.
# num_untranslated_words        number of untranslated words.
TransifexTranslationStats = namedtuple('TransifexTranslationStats', 'project_slug, resource_slug, name, language_code, last_updated, last_updated_by, num_reviewed_strings, percentage_reviewed_strings, num_translated_strings, num_untranslated_strings, percentage_translated_strings, num_translated_words, num_untranslated_words')


