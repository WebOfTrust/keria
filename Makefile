.PHONY: build-keria ruff-check

VERSION=0.2.0-rc1
IMAGE_NAME=weboftrust/keria
VERSION_TAG=$(IMAGE_NAME):$(VERSION)
LATEST_TAG=$(IMAGE_NAME):latest

define DOCKER_WARNING
In order to use the multi-platform build enable the containerd image store
The containerd image store is not enabled by default.
To enable the feature for Docker Desktop:
	Navigate to Settings in Docker Desktop.
	In the General tab, check Use containerd for pulling and storing images.
	Select Apply and Restart."
endef

build-wheel:
	@python setup.py sdist

build-keria: .warn
	@docker build \
		--build-arg KERI_AGENT_CORS=false \
		--platform=linux/amd64,linux/arm64 \
		--no-cache \
		-f images/keria.dockerfile \
		-t $(LATEST_TAG) \
		-t $(VERSION_TAG) \
		.

publish-keria:
	@docker push $(VERSION_TAG) && docker push $(LATEST_TAG)

.warn:
	@echo -e ${RED}"$$DOCKER_WARNING"${NO_COLOUR}

RED="\033[0;31m"
NO_COLOUR="\033[0m"
export DOCKER_WARNING
