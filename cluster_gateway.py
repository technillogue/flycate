from typing import AsyncIterator
import aiohttp
import os
from aiohttp import web


def key(version_id: str) -> str:
    return f"flycate-model-{version_id[:8]}"


# Create the web application
app = web.Application()


@app.cleanup_ctx.append
async def client(app: web.Application) -> AsyncIterator[None]:
    async with aiohttp.ClientSession() as app.client:
        yield


# /_internal/create-app
async def create_app(request: web.Request) -> web.Response:
    data = await request.json()
    docker_image_uri = data["docker_image_uri"]
    version_id = data["version_id"]

    os.system(
        f"fly launch --image {docker_image_uri} --name {key(version_id)} "
        "--vm-size l40s "
        "--internal-port 5000 "
        "--org replicate "
        "--region ord "
        "--yes"
    )
    os.system("rm fly.toml")
    return web.json_response({"message": f"App created: {key(version_id)}"})


# /v1/predictions
async def handle_predict(request: web.Request) -> web.Response:
    data = await request.json()
    version_id = data.pop("version")
    print("request:", request)

    for i in range(3):
        try:
            async with app.client.post(
                f"https://{key(version_id)}.fly.dev/predictions", json=data
            ) as response:
                print("response:", response)
                if response.status == 409:
                    # Retry on 409 (Conflict) status
                    continue
                else:
                    # Return the response exactly as it is for all other status codes
                    headers = dict(response.headers)
                    headers.pop("Content-Type")
                    resp = web.Response(
                        body=await response.read(),
                        status=response.status,
                        headers=headers,
                        content_type=response.content_type,
                        charset=response.charset,
                    )
                    print("final response:", resp)
                    return resp
        except Exception as e:
            # Handle any other exceptions
            return web.json_response({"error": str(e)}, status=500)

    # If all retries failed
    return web.json_response(
        {"error": "Failed to get prediction after multiple retries"}, status=500
    )


app.add_routes(
    [
        web.post("/_internal/create-app", create_app),
        web.post("/v1/predictions", handle_predict),
    ]
)

if __name__ == "__main__":
    web.run_app(app)
