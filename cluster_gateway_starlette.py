from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
import httpx
import os
import logging


logging.getLogger().setLevel("DEBUG")

client = httpx.AsyncClient()
local = os.getenv("FLY_APP_NAME")


def key(version_id: str) -> str:
    return f"flycate-model-{version_id[:4]}"


async def run_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        return stdout.decode().strip()
    else:
        raise Exception(f"Command failed with error {stderr.decode().strip()}")


async def create_app(request):
    data = await request.json()
    docker_image_uri = data["docker_image_uri"]
    version_id = data["version_id"]
    cmd = "fly" if local else "/root/.fly/bin/fly"

    os.system(
        f"{cmd} launch --image {docker_image_uri} --name {key(version_id)} "
        "--vm-size l40s "
        "--internal-port 5000 "
        "--org replicate "
        "--region ord "
        "--now "
        "--yes"
    )
    if not local:
        os.system("rm fly.toml")
    return JSONResponse({"message": f"App created: {key(version_id)}"})


async def handle_predict(request):
    try:
        try:
            data = await request.json()
            version_id = data.pop("version")
            print("request:", request)
        except Exception as e:
            print(repr(e))
            raise

        try:
            for i in range(10):
                response = await client.post(
                    f"https://{key(version_id)}.fly.dev/predictions", json=data
                )
                print("response:", response)
                if response.status_code == 409:
                    await asyncio.sleep(random.random())
                    continue
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response.headers,
                )
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse(
            {"error": "Failed to get prediction after multiple retries"},
            status_code=500,
        )
    except Exception as e:
        print(repr(e))


routes = [
    Route("/_internal/create-app", create_app, methods=["POST"]),
    Route("/v1/predictions", handle_predict, methods=["POST"]),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
