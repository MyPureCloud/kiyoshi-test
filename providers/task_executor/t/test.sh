
# echo
# echo '### Invoke email notificator with one resource comparison results.'
# echo '### should be 200 and you get email.'
# curl -H 'Accept: application/json' \
#  -X POST 'localhost:64800/api/v0/tasks/multitasks_executor/exec' \
#  -d '{"tasks": [{"executor_id": "resource_comparator", "config_path": "config/projects/YOUR_PROJECT_ID/uploader.json", "request_id": "NIY", "accept_feeds": "false"}, {"executor_id": "resource_comparator_formatter", "config_path": "config/projects/maint_resource_comparision/format.json", "request_id": "NIY", "accept_feeds": "true"}, {"executor_id": "email_notificator", "config_path": "config/projects/test_email_notificator/email_template.json", "request_id": "NIY", "accept_feeds": "true"}]}'
# echo

echo
echo '### Invoke email notificator with two resource comparison results.'
echo '### should be 200 and you get email.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/tasks/multitasks_executor/exec' \
 -d '{"tasks": [{"executor_id": "resource_comparator", "config_path": "config/projects/YOUR_PROJECT_ID_1/uploader.json", "request_id": "NIY", "accept_feeds": "false"}, {"executor_id": "resource_comparator", "config_path": "config/projects/YOUR_PROJECT_ID_2/uploader.json", "request_id": "NIY", "accept_feeds": "false"}, {"executor_id": "resource_comparator_formatter", "config_path": "config/projects/maint_resource_comparision/format.json", "request_id": "NIY", "accept_feeds": "true"}, {"executor_id": "email_notificator", "config_path": "config/projects/test_email_notificator/email_template.json", "request_id": "NIY", "accept_feeds": "true"}]}'
echo


