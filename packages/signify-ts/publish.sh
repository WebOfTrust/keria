#!/bin/sh
set -e

name=${NPM_PACKAGE_NAME:-"signify-ts"}
version=${NPM_PACKAGE_VERSION:?"NPM_PACKAGE_VERSION must be set"}
tag=${RELEASE_TAG:-"dev"}

cp package.json package.json.bak
npm ci
npm run build
npm pkg set version="${version}"
npm pkg set name="${name}"

if [ -z "$DRY_RUN" ]; then
    npm publish --tag "${tag}" --access public
else
    npm publish --tag "${tag}" --access public --dry-run
fi

mv package.json.bak package.json
