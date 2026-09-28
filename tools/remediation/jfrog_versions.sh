#!/usr/bin/env bash
# usage: jfrog_versions.sh <groupId> <artifactId>
set -euo pipefail
ARTIFACTORY_URL="${ARTIFACTORY_URL:-https://artifactory.internal.example/artifactory}"
REPO="${ARTIFACTORY_REPO:-maven-virtual}"
G_PATH=$(echo "$1" | tr '.' '/')
curl -sf -H "Authorization: Bearer ${ARTIFACTORY_TOKEN:?set ARTIFACTORY_TOKEN}" \
  "$ARTIFACTORY_URL/$REPO/$G_PATH/$2/maven-metadata.xml" \
  | grep -oP '(?<=<version>)[^<]+' \
  | grep -viE 'alpha|beta|rc|cr|snapshot|milestone|\.m[0-9]' \
  || echo "NOT_FOUND"
