echo
echo '### Check YOUR_PROJECT_ID resource files with non-existent config file.'
echo '### Should be 400.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/task/resource_comparator/exec' \
 -d '{"config_path": "config/projects/YOUR_PROJECT_ID/foo.json", "request_id": "NIY"}'
echo

echo
echo '### Check YOUR_PROJECT_ID resource files.'
echo '### Should be 200.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/task/resource_comparator/exec' \
 -d '{"config_path": "config/projects/YOUR_PROJECT_ID/uploader.json", "request_id": "NIY"}'
echo

echo
echo '### Check YOUR_PROJECT_ID resource files w/ format option.'
echo '### Should be 200.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/task/resource_comparator/exec' \
 -d '{"config_path": "config/projects/YOUR_PROJECT_ID/uploader.json", "request_id": "NIY", "format": "summary"}'
echo

