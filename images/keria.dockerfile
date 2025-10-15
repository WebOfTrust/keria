FROM python:3.12.8-alpine3.21 AS builder

RUN apk add --no-cache \
    build-base \
    curl \
    gcc \
    libffi-dev \
    libsodium-dev \
    musl-dev \
    patch \
    pkgconfig

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /keria

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-editable

COPY src/ src/
RUN uv sync --locked --no-dev

FROM python:3.12.8-alpine3.21
WORKDIR /keria

RUN apk add --no-cache \
    bash \
    curl \
    libsodium-dev \
    gcc

COPY --from=builder /keria /keria

ENV PATH="/keria/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 3901
EXPOSE 3902
EXPOSE 3903
ENTRYPOINT ["keria"]
CMD ["start"]
