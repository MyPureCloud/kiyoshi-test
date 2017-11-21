#
# No providers need to be run for this test.
#

echo '### who am i'
echo '### 200.'
curl 'localhost:65000/api/v0/whoami'
echo

echo
echo '### List project names'
echo '### 200. Some project names should be listed.'
curl 'localhost:65000/api/v0/configuration/tpa/projects'
echo

echo
echo '### Get YOUR_PROJECT_ID project config context'
echo '### 200. YOUR_PROJECT_ID configuration file should be dumped.'
curl 'localhost:65000/api/v0/configuration/tpa/project/YOUR_PROJECT_ID'
echo

echo
echo '### Get non-existent config context'
echo '### 400.'
curl 'localhost:65000/api/v0/configuration/tpa/path=foo%2Fbar.json'
echo

echo
echo '### Get existent config context'
echo '### 200. Sandbag configuration file should be dumped.'
curl 'localhost:65000/api/v0/configuration/tpa/path=config%2Fprojects%2FYOUR_PROJECT_ID%2Fuploaders.json'
echo

echo
echo '### Get non-existent job config context'
echo '### 400.'
curl 'localhost:65000/api/v0/configuration/tpa/project/YOUR_PROJECT_ID/job/no-such-job'
echo

echo
echo '### Get YOUR_PROJECT_ID valid job config context'
echo '### 200.'
curl 'localhost:65000/api/v0/configuration/tpa/project/YOUR_PROJECT_ID/job/resource_upload'
echo

