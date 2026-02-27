FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first for layer caching
COPY pyproject.toml .
COPY uv.lock .

# Install only core dependencies (no grubhub/buckeyelink extras — those need emulators)
RUN uv sync --no-dev --no-install-project

# Copy source
COPY . .

# Install the project itself
RUN uv sync --no-dev

EXPOSE 5000

CMD ["uv", "run", "python", "main.py"]
