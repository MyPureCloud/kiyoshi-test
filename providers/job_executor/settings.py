
identity = {
        'type': 'provider',
        'name': 'job_executor'
}

server = {
        'http': {
            'port': '64600'
        }
}

providers = {
    'configurator': {
        'api': 'http://localhost:65000/api/v0'
    },
    'task_executor': {
        'api': 'http://localhost:64800/api/v0'
    }
}

kafka = {
    'brokers': [
        {'server': 'localhost', 'port': '9092'}
    ],
    'topic': 'job_executor'
}

