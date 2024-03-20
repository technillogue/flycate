# an implementation of the replicate API on fly

this is a simplified cluster that provides access to the cog API at scale. rather than providing the true replicate predictions interface, it simply routes predictions to fly apps, which natively provide load balancing and scaling.

---

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

for demo reasons just add a separate route to create and update apps (a type of VersionDeployment thing) given metadata and stuff

POST /_internal/apps/<version>
GET?
PATCH?

fly launch --region ord --image r8.im/mistralai/mistral-7b-v0.1 --vm-size l40s --internal-port 5000

curl -s -d '{ "version": "740618b0c24c0ea4ce5f49fcfef02fcd0bdd6a9f1b0c5e7c02ad78e9b3b190a6", "input": { "prompt": "Tell me a short joke", "max_length": 32 } }' -H 'Content-Type: application/json' http://localhost:8080/v1/predictions|jq
