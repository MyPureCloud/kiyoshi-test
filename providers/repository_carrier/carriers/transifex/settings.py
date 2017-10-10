
identity = {
        'type': 'repository_carrier',
        'name': 'transifex'
}

# Full path to local cache directory where downloads from Transifex reside.
local_cache_dir = '/home/foo/transifex'

# Transifex account information.
# 'project_slug_prefix' and 'resource_slug_prefix' are prefix strings which
# will be part of project and resource slugs.
creds = {
    "userfullname": "",
    "username" : "",
    "userpasswd": "",
    "useremail": "",
    "project_slug_prefix": "MyOrgName-",
    "resource_slug_prefix": "MyOrgName-"
}

kafka = {
    'topic': 'transifex'
}
