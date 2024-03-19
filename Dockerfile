FROM python:3.12
RUN curl -L https://fly.io/install.sh | sh
RUN --mount=type=cache,target=/root/.cache/pip pip install starlette httpx uvicorn
WORKDIR /app
COPY ./cluster_gateway_starlette.py /app/cluster_gateway.py
ENTRYPOINT ["/usr/local/bin/python3.12", "/app/cluster_gateway.py"]
