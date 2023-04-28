
FROM python:3.10.4-alpine3.16

RUN apk update
RUN apk add bash
SHELL ["/bin/bash", "-c"]

RUN apk add alpine-sdk
RUN apk add libffi-dev
RUN apk add libsodium
RUN apk add libsodium-dev

# Setup Rust for blake3 dependency build
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

COPY . /keria
WORKDIR /keria

# Install KERIpy dependencies
# Must source the Cargo environment for the blake3 library to see the Rust intallation during requirements install
RUN source "$HOME/.cargo/env" && pip install -r requirements.txt

EXPOSE 3901
EXPOSE 3902
EXPOSE 3903

RUN mkdir -p /usr/local/var/keri

ENTRYPOINT ["keria", "start",  "--config-file", "demo-witness-oobis", "--config-dir", "./scripts"]


