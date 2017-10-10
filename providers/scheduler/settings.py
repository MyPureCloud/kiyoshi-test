identity = {
        'type': 'provider',
        'name': 'scheduler'
}

server = {
        'http': {
            'port': '64900'
        }
}

providers = {
    'configurator': {
        'api': 'http://localhost:65000/api/v0'
        }
    }

kafka = {
    'brokers': [
        {'server': 'localhost', 'port': '9092'}
    ],
    'topic': 'scheduler',
    'key': 'server'
}
