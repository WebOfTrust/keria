#!/bin/sh
set -e

package_info=$(cat package.json)
scope=${NPM_PACKAGE_SCOPE:-$(echo "$package_info" | jq .name -r | grep '/' | cut -d'/' -f1)}
name=${NPM_PACKAGE_NAME:-$(echo "$package_info" | jq .name -r | cut -d'/' -f2)}

version=$(echo "$package_info" | jq .version -r)
tag=${NPM_PUBLISH_TAG:-dev}

if [ "$scope" != "" ]; then
    name="${scope}/${name}"
fi

if [ "$tag" = "dev" ]; then
    version="${version}-dev.$(git rev-parse --short HEAD)"
fi

npm ci
npm run build

# Creating a temporary directory for publishing.
#
# This allows us to modify the version and name of the published package
# without having to commit changes to the repo. Which is useful for tagged
# and scoped package releases.
publish_dir="$(mktemp -d)"
cp -r README.md LICENSE dist package.json package-lock.json "${publish_dir}/"
jq ".version = \"${version}\" | .name = \"${name}\" | del(.scripts.prepare)" package.json > "${publish_dir}/package.json"

if [ -z "$DRY_RUN" ]; then
    npm publish "${publish_dir}" --tag "${tag}"
else
    npm publish "${publish_dir}" --tag "${tag}" --dry-run
fi
