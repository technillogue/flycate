POST https://api.replicate.com/v1/predictions
{
  "version": "...",
  "input": {
    "text": "Alice"
  }
}

you just need a handler for that one route that

0) redis or something keeping track of apps that are created
1) forward requests to cogs
- uses or creates a deployment key or whatever
- makes a fly app


truncate the version id, that's the app name
fetch the version id like docker image?

LookupVersionMetadata

for demo reasons just add a separate route to create and update apps (a type of VersionDeployment thing) given metadata and shit

POST /_internal/apps/<version>
GET?
PATCH?

fly launch --region ord --image r8.im/mistralai/mistral-7b-v0.1 --vm-size l40s --internal-port 5000
