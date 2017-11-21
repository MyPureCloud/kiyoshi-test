# Note:
# Following providers need to be running to perform this test.
#   configurator
#   scheduler

echo
echo '### whoami.'
curl 'localhost:64800/api/v0/whoami'
echo

echo
echo '### Exec non-existing task.'
echo '### Should be 400.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/task/foo/exec' \
 -d '{"config_path": "config/projects/YOUR_PROJECT_ID/resource.json", "request_id": "NIY"}'
echo

echo
echo '### Pull repo with non-existent config file.'
echo '### Should be 400.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/task/repository_puller/exec' \
 -d '{"config_path": "config/projects/foo/resource.json", "request_id": "NIY"}'
echo

echo
echo '### Pull YOUR_PROJECT_ID repo.'
echo '### Should be 200.'
curl -H 'Accept: application/json' \
 -X POST 'localhost:64800/api/v0/task/repository_puller/exec' \
 -d '{"config_path": "config/projects/YOUR_PROJECT_ID/resource.json", "request_id": "NIY"}'
echo

