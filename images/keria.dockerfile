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

WORKDIR /keria

RUN python -m venv venv
ENV PATH=/keria/venv/bin:${PATH}

RUN pip install --upgrade pip
# "src/" dir required for installation of dependencies with setup.py
RUN mkdir /keria/src
# Copy in Python dependency files
COPY requirements.txt setup.py ./

# Install Python dependencies
RUN . "$HOME/.cargo/env"
RUN pip install -r requirements.txt

# Runtime stage
FROM python:3.12.8-alpine3.21

# Install runtime dependencies
RUN apk --no-cache add \
    bash \
    curl \
    libsodium-dev \
    gcc

WORKDIR /keria

# Copy over compiled dependencies
COPY --from=builder /keria /keria
# Copy in KERIA source files - enables near instantaneous builds for source only changes
RUN mkdir -p /usr/local/var/keri
ENV KERI_AGENT_CORS=${KERI_AGENT_CORS:-false}
ENV PATH=/keria/venv/bin:${PATH}

EXPOSE 3901
EXPOSE 3902
EXPOSE 3903

COPY src/ src/

ENTRYPOINT ["keria"]

CMD [ "start" ]
