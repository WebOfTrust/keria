# Builder stage
FROM python:3.12.8-alpine3.21 AS builder

# Install compilation dependencies
RUN apk --no-cache add \
    curl \
    bash \
    alpine-sdk \
    libffi-dev \
    libsodium \
    libsodium-dev

SHELL ["/bin/bash", "-c"]

# Install Rust for blake3 dependency build
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /keria

# Copy in Python dependency files
COPY pyproject.toml uv.lock ./
COPY src/ src/

# Install Python dependencies with uv
RUN . "$HOME/.cargo/env" && uv sync --frozen --no-dev

# Runtime stage
FROM python:3.12.8-alpine3.21

# Install runtime dependencies
RUN apk --no-cache add \
    bash \
    curl \
    libsodium-dev \
    gcc

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /keria

# Copy over compiled dependencies from builder
COPY --from=builder /keria/.venv /keria/.venv
COPY --from=builder /keria/src /keria/src

# Create required directories
RUN mkdir -p /usr/local/var/keri
ENV KERI_AGENT_CORS=${KERI_AGENT_CORS:-false}

# Make sure we can run our app
ENV PATH="/keria/.venv/bin:$PATH"

EXPOSE 3901
EXPOSE 3902
EXPOSE 3903

ENTRYPOINT ["keria"]

CMD [ "start" ]
