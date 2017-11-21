
echo
echo '### Pull by non-existent config path.'
echo '### Should be 400.'
curl -H 'Accept: application/json' \
     -X POST 'localhost:64700/api/v0/repository/pull' \
      -d '{"config_path": "config/projects/false-project-name/resource.json", "request_id": "NIY"}'
echo

echo
echo '### Pull by YOUR_PROJECT_ID config path.'
echo '### Should be 200.'
curl -H 'Accept: application/json' \
     -X POST 'localhost:64700/api/v0/repository/pull' \
      -d '{"config_path": "config/projects/YOUR_PROJECT_ID/resource.json", "request_id": "NIY"}'
echo

echo
echo '### Pull again by YOUR_PROJECT_ID config path.'
echo '### Should be 200.'
curl -H 'Accept: application/json' \
     -X POST 'localhost:64700/api/v0/repository/pull' \
      -d '{"config_path": "config/projects/YOUR_PROJECT_ID/resource.json", "request_id": "NIY"}'
echo

echo
echo '### Check file existence w/ false platorm name.'
echo '### Should be 400.'
curl 'localhost:64700/api/v0/repository/platform/false-platform-name/repo/false-repo-name/file/path=false-file-path/exists'
echo

echo
echo '### Check file existence w/ false repo name.'
echo '### Should be 400.'
curl 'localhost:64700/api/v0/repository/platform/bitbucket/repo/false-repo-name/file/path=false-file-path/exists'
echo

echo
echo '### Check file existence w/ false file path.'
echo '### Should be 200 and exists is false.'
curl 'localhost:64700/api/v0/repository/platform/bitbucket/repo/YOUR_PROJECT_ID/file/path=false-file-path/exists'
echo

echo
echo '### Check file existence for valid YOUR_PROJECT_ID file.'
echo '### Should be 200 and exists is true.'
curl 'localhost:64700/api/v0/repository/platform/bitbucket/repo/YOUR_PROJECT_ID/file/path=translations%2Fen-us.json/exists'
echo

echo
echo '### Get file context w/ false repo name.'
echo '### Should be 400.'
curl 'localhost:64700/api/v0/repository/platform/bitbucket/repo/false-repo-name/file/path=translations%2Fen-us.json'
echo

echo
echo '### Get file context w/ false file path.'
echo '### Should be 400.'
curl 'localhost:64700/api/v0/repository/platform/bitbucket/repo/YOUR_PROJECT_ID/file/path=false-file-path'
echo

echo
echo '### Get file context for valid file.'
echo '### Should be 200 w/ sha1 and file context.'
curl 'localhost:64700/api/v0/repository/platform/bitbucket/repo/YOUR_PROJECT_ID/file/path=translations%2Fen-us.json'
echo

