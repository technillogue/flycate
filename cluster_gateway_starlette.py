import asyncio
import logging
import os
import random

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

logging.getLogger().setLevel("DEBUG")

client = httpx.AsyncClient()
local = not bool(os.getenv("FLY_APP_NAME"))
flyctl = flyctl = "fly" if local else "/root/.fly/bin/fly"


def key(version_id: str) -> str:
    return f"flycate-model-{version_id[:4]}"


async def run_command(command: str) -> int:
    print("running", command)
    process = await asyncio.create_subprocess_shell(command)
    return await process.wait()


async def create_app(request: Request) -> JSONResponse:
    data = await request.json()
    docker_image_uri = data["docker_image_uri"]
    app_name = key(data["version_id"])
    hardware = data.get("hardware", "a100-40gb")
    if await run_command(f"{flyctl} status -a {app_name}") == 0:
        return JSONResponse({"message": f"{app_name} already exists"})
    await run_command(
        f"{flyctl} launch --image {docker_image_uri} --name {app_name} "
        "--vm-size l40s "
        "--internal-port 5000 "
        "--org replicate "
        "--region ord "
        "--now "
        "--yes"
    )
    if not local:
        await run_command("rm fly.toml")
    return JSONResponse({"message": f"App created: {app_name}"})


async def handle_predict(request: Request) -> Response:
    data = await request.json()
    version_id = data.pop("version")
    try:
        # retry for about 15s, which should be enough for good models to boot
        for i in range(30):
            response = await client.post(
                f"https://{key(version_id)}.fly.dev/predictions", json=data
            )
            print("response:", response)
            if response.status_code == 409:
                await asyncio.sleep(random.random())
                continue
            return Response(content=response.content, status_code=response.status_code)
    except Exception as e:
        print(repr(e))
        return JSONResponse({"error": str(e)}, status_code=500)
    return JSONResponse(
        {"error": "Failed to get prediction after multiple retries"},
        status_code=500,
    )


routes = [
    Route("/_internal/create-app", create_app, methods=["POST"]),
    Route("/v1/predictions", handle_predict, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
