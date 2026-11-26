# HTTP service (mcp_api). Requests from outside the container need MCP_API_KEY.
FROM python:3.12-slim

WORKDIR /app
COPY mcp_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_api/models models
COPY mcp_api/server server

RUN useradd --create-home app
USER app

ENV HOST=0.0.0.0 PORT=8000
EXPOSE 8000
CMD ["python", "-m", "server.main"]
