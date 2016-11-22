import urlparse

# IP address and port of TPA server.
TPA_SERVER = 'http://localhost:8080/'

# Various URLs
TPA_API_CONFIG = urlparse.urljoin(TPA_SERVER, 'api/v0/config')
TPA_API_JOB = urlparse.urljoin(TPA_SERVER, 'api/v0/job')
TPA_API_JOBS = urlparse.urljoin(TPA_SERVER, 'api/v0/jobs')
TPA_API_LOG = urlparse.urljoin(TPA_SERVER, 'api/v0/log')
TPA_API_PROJECT = urlparse.urljoin(TPA_SERVER, 'api/v0/project')
TPA_API_PROJECTS = urlparse.urljoin(TPA_SERVER, 'api/v0/projects')

# Port for this server.
HTTP_PORT='8081'
