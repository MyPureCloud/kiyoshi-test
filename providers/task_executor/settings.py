import executors.resource_comparator_formatter.executor
import executors.email_notificator.executor
import executors.resource_comparator.executor
import executors.resource_puller.executor
import executors.resource_existence_checker.executor

identity = {
        'type': 'provider',
        'name': 'task_executor'
}

server = {
        'http': {
            'port': '64800'
        }
}

providers = {
    'repository_carrier': {
        'api': 'http://localhost:64700/api/v0'
    }
}
executors = {
        'resource_comparator_formatter': executors.resource_comparator_formatter.executor,
        'email_notificator': executors.email_notificator.executor,
        'resource_comparator': executors.resource_comparator.executor,
        'resource_puller': executors.resource_puller.executor,
        'resource_existence_checker': executors.resource_existence_checker.executor
        }

kafka = {
    'brokers': [
        {'server': 'localhost', 'port': '9092'}
    ],
    'topic': 'task_executor',
    'key': 'server'
}

