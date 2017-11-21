
echo
echo '### Invoke non existent job on YOUR_PROJECT_ID.'
echo '### should be 400.'
curl -X POST 'localhost:64600/api/v0/job/YOUR_PROJECT_ID/no-such-job/exec'
echo

echo
echo '### Invoke pull_repository job on YOUR_PROJECT_ID.'
echo '### should be 200.'
curl -X POST 'localhost:64600/api/v0/job/YOUR_PROJECT_ID/pull_repository/exec'
echo

 echo
 echo '### Invoke resource_existence_check job on YOUR_PROJECT_ID.'
 echo '### should be 200.'
 curl -X POST 'localhost:64600/api/v0/job/YOUR_PROJECT_ID/check_resources_exist/exec'
 echo
# 
# echo
# echo '### Invoke resource_comparison job on YOUR_PROJECT_ID.'
# echo '### should be 200.'
# curl -X POST 'localhost:64600/api/v0/job/YOUR_PROJECT_ID/resource_comparison/exec'
# echo

