import configurators.tpa.configurator

identity = {
        'type': 'provider',
        'name': 'configurator'
}

server = {
        'http': {
            'port': '65000'
        }
}

configurators = {
    'tpa': configurators.tpa.configurator
}

kafka = {
    'brokers': [
        {'server': 'localhost', 'port': '9092'}
    ],
    'topic': 'configurator',
    'key': 'server'
}
