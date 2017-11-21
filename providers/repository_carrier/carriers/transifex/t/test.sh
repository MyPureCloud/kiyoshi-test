

echo
echo '### Get file context w/ false project slug.'
echo '### Should be 400.'
curl 'localhost:64700/api/v0/repository/platform/transifex/project/false-project-slug/resource/false-resource-slug/lang/false-lang-id'
echo

echo
echo '### Get file context w/ false resource slug.'
echo '### Should be 400.'
curl 'localhost:64700/api/v0/repository/platform/transifex/project/YOUR_PROJECT_SLAG/resource/false-resource-slug/lang/false-lang-id'
echo

echo
echo '### Get file context w/ false lang id.'
echo '### Should be 400.'
curl 'localhost:64700/api/v0/repository/platform/transifex/project/YOUR_PROJECT_SLAG/resource/YOUR_RESOURCE_SLUG/lang/false-lang-id'
echo

echo
echo '### Get resource file context for YOUR_PROJECT.'
echo '### Should be 200.'
curl 'localhost:64700/api/v0/repository/platform/transifex/project/YOUR_PROJECT_SLAG/resource/YOUR_RESOURCE_SLUG/lang/en-US'
echo

echo
echo '### Get resource stats for YOUR_PROJECT.'
echo '### Should be 200.'
curl 'localhost:64700/api/v0/repository/platform/transifex/project/inin-sandbag-en-us/resource/YOUR_RESOURCE_SLUG/status'
echo

echo
echo '### Get en-US translation stats for YOUR_PROJECT.'
echo '### Should be 200.'
curl 'localhost:64700/api/v0/repository/platform/transifex/project/YOUR_PROJECT_SLUG/resource/YOUR_RESOURCE_SLUG/lang/en-US/status'
echo

