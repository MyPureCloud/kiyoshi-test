
echo
echo '### whoami.'
curl 'localhost:64900/api/v0/whoami'
echo

echo
echo '### List projects w/o adding any projects.'
echo '### Should be 200 w/ 0 projects.'
curl 'localhost:64900/api/v0/schedule/projects'
echo

echo
echo '### List YOUR_PROJECT_ID project, which is not in scheduler.'
echo '### Should be 400.'
curl 'localhost:64900/api/v0/schedule/project/YOUR_PROJECT_ID'
echo

echo
echo '### Add YOUR_PROJECT_ID project.'
echo '### Should be 200 w/ some job ids.'
curl -X POST 'localhost:64900/api/v0/schedule/project/YOUR_PROJECT_ID'
echo

echo
echo '### List projects.'
echo '### Should be 200 w/ YOUR_PROJECT_ID projects.'
curl 'localhost:64900/api/v0/schedule/projects'
echo

echo
echo '### List YOUR_PROJECT_ID project.'
echo '### Should be 200 w/ YOUR_PROJECT_ID jobs.'
curl 'localhost:64900/api/v0/schedule/project/YOUR_PROJECT_ID'
echo

#echo
#echo '### Add the same project to scheduler.'
#echo '### Should be 202 b/c there is no updates in configuration.'
#curl -X POST 'localhost:64900/api/v0/schedule/project/YOUR_PROJECT_ID'
#echo

# echo
# echo '### List YOUR_PROJECT_ID project.'
# echo '### Should be 200 w/ some job ids.'
# curl 'localhost:64900/api/v0/schedule/project/YOUR_PROJECT_ID'
# echo
#
# echo
# echo '### Exec scheduled project jobs.'
# echo '### Should be 200. '
# curl -X POST 'localhost:64900/api/v0/schedule/project/YOUR_PROJECT_ID/job/sandbag_resource_uploading/exec'
# echo

