
echo
echo '### Upload translated files from Transifex YOUR_PROJECT_ID to Bitbucket.'
echo '### Should be 200.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/task/translation_uploader/exec' \
 -d '{"config_path": "config/projects/YOUR_PROJECT_ID/uploader.json", "request_id": "NIY"}'
echo


