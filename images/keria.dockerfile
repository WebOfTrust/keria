# Builder stage
FROM python:3.10.13-alpine3.18 as builder

# Install compilation dependencies
RUN apk --no-cache add \
    bash \
    alpine-sdk \
    libffi-dev \
    libsodium \
    libsodium-dev

SHELL ["/bin/bash", "-c"]

# Install Rust for blake3 dependency build
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

WORKDIR /keria

RUN python -m venv venv
ENV PATH=/keria/venv/bin:${PATH}
RUN pip install --upgrade pip

# Copy in Python dependency files
COPY requirements.txt setup.py ./
# "src/" dir required for installation of dependencies with setup.py
RUN mkdir /keria/src
# Install Python dependencies
RUN . "$HOME/.cargo/env" && \
    pip install -r requirements.txt

# Runtime stage
FROM python:3.10.13-alpine3.18

# Install runtime dependencies
RUN apk --no-cache add \
    bash \
    alpine-sdk \
    libsodium-dev

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

ENTRYPOINT ["keria", "start",  "--config-file", "demo-witness-oobis", "--config-dir", "./scripts"]
