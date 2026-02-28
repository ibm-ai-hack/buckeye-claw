FROM python:3.11-slim

WORKDIR /app

# Install uv (pinned for reproducibility)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (cached unless pyproject.toml/uv.lock change)
RUN uv sync --no-dev --no-install-project --frozen

# Copy source
COPY . .

# Install the project itself (fast — deps already cached above)
RUN uv sync --no-dev --frozen

EXPOSE 5000

CMD ["uv", "run", "python", "main.py"]
