# echo https://sentry.io/api/0/organizations/careerlyft-technologies/releases/ -H 'authorization: Bearer $1' -H 'content-type: application/json'  -d '{"version":"$2","ref":"$3", "projects":["authentication-service","admin","cv-profile","payment-service","cvscripts-service"]}'
# echo curl -X POST https://sentry.io/api/0/organizations/careerlyft-technologies/releases/ -H 'authorization: Bearer '$1'' -H 'content-type: application/json'  -d '{"version":"'$2'","ref":"'$3'", "projects":["authentication-service","admin","cv-profile","payment-service","cvscripts-service"]}'
curl -X POST https://sentry.io/api/0/organizations/careerlyft-technologies/releases/ -H 'authorization: Bearer '$1'' -H 'content-type: application/json'  -d '{"version":"'$2'","ref":"'$3'", "projects":["authentication-service","admin","cv-profile","payment-service","cvscripts-service"]}'


# curl app.getsentry.com/api/0/organizations/{organization_slug}/releases/ 
curl https://sentry.io/api/0/organizations/careerlyft-tech/releases/$3/deploys/ \
  -X POST \
  -H 'Authorization: Bearer '$1'' \
  -H 'Content-Type: application/json' \
  -d '
  {
    "environment": "'$4'",
    "name": "'$2'"
    "url": "'$5'"
}
'