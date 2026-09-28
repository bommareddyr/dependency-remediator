# jfrog_versions.py - lists release versions of a library available in JFrog Artifactory
# usage: python jfrog_versions.py <groupId> <artifactId>
import os, re, sys, urllib.request

ARTIFACTORY_URL = "https://artifactory.yourcompany.com/artifactory"   # CHANGE ME
REPO = "maven-virtual"                                                 # CHANGE ME

if len(sys.argv) != 3:
    sys.exit("usage: python jfrog_versions.py <groupId> <artifactId>")
group, artifact = sys.argv[1], sys.argv[2]
token = os.environ.get("ARTIFACTORY_TOKEN")
if not token:
    sys.exit("ERROR: ARTIFACTORY_TOKEN is not set. See guide Step 3.")

url = f"{ARTIFACTORY_URL}/{REPO}/{group.replace('.', '/')}/{artifact}/maven-metadata.xml"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
try:
    xml = urllib.request.urlopen(req, timeout=30).read().decode()
except Exception as e:
    print(f"NOT_FOUND ({e})")
    sys.exit(0)

def vkey(v):
    return [int(x) for x in re.findall(r"\d+", v)] or [0]

skip = re.compile(r"alpha|beta|rc|cr|snapshot|milestone|\.m\d", re.I)
versions = sorted({v for v in re.findall(r"<version>([^<]+)</version>", xml) if not skip.search(v)}, key=vkey)
print("\n".join(versions) if versions else "NOT_FOUND (no release versions)")
