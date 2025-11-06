#!/bin/bash
set -e

tag=${RELEASE_TAG:-dev}
version=$(cat pyproject.toml | grep "version =" | cut -d= -f2 | tr -d '" ')

if ! [[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Version does not match semver spec: $version"
    exit 1
fi

if [ "$tag" = "dev" ]; then
    version="${version}-dev.$(git rev-parse --short HEAD)"
fi

echo "$version"
