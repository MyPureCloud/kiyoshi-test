from .executors.resource_comparator_formatter import executor as resource_comparator_formatter
from .executors.email_notificator import executor as email_notificator
from .executors.resource_comparator import executor as resource_comparator
from .executors.repository_puller import executor as repository_puller
from .executors.resource_existence_checker import executor as resource_existence_checker
from .executors.resource_uploader import executor as resource_uploader
from .executors.translation_uploader import executor as translation_uploader

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
        'resource_comparator_formatter': resource_comparator_formatter,
        'email_notificator': email_notificator,
        'resource_comparator': resource_comparator,
        'resource_uploader': resource_uploader,
        'repository_puller': repository_puller,
        'resource_existence_checker': resource_existence_checker,
        'translation_uploader': translation_uploader
        }

kafka = {
    'brokers': [
        {'server': 'localhost', 'port': '9092'}
    ],
    'topic': 'task_executor',
    'key': 'server'
}

