from .carriers.bitbucket import carrier as bitbucket
from .carriers.transifex import carrier as transifex

identity = {
    'type': 'provider',
    'name': 'repository_carrier'
}

server = {
    'http': {
        'port': '64700'
    }
}

providers = {
    'configurator': {
        'api': 'http://localhost:65000/api/v0'
    }
}

repository_carriers = {
    'bitbucket': bitbucket,
    'transifex': transifex
}

kafka = {
    'brokers': [
        {'server': 'localhost', 'port': '9092'}
    ],
    'topic': 'repository_carrier',
    'key': 'server'
}
