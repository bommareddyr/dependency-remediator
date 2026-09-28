#!/usr/bin/env bash
# usage: verify.sh <groupId> <artifactId>
set -euo pipefail
if [ -f pom.xml ]; then
  mvn -q -B dependency:tree -Dincludes="$1:$2" -DoutputType=text
else
  ./gradlew -q dependencyInsight --dependency "$1:$2" --configuration runtimeClasspath
fi
