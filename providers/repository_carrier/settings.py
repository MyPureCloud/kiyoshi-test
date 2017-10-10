import carriers.bitbucket.carrier
import carriers.transifex.carrier

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
    'bitbucket': carriers.bitbucket.carrier,
    'transifex': carriers.transifex.carrier
}

kafka = {
    'brokers': [
        {'server': 'localhost', 'port': '9092'}
    ],
    'topic': 'repository_carrier',
    'key': 'server'
}
