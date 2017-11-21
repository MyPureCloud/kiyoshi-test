
echo
echo '### Invoke email notificator.'
echo '### should be 200 and you get email.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/task/email_notificator/exec' \
 -d '{"config_path": "config/projects/test_email_notificator/email_template.json", "request_id": "NIY"}'
echo

