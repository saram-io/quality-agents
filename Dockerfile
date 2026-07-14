FROM python:3.12-slim

# Install uv installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /workspace

# Copy dependencies manifest
COPY pyproject.toml uv.lock ./

# Mount cache for faster builds and install dependencies
RUN uv sync --frozen

# Copy codebase
COPY . .

# Run the GxP Software Qualification suite on startup as a container verification check
CMD ["uv", "run", "python3", "-m", "app.qualification.runner"]
