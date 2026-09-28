# sonatype_check.py - asks Sonatype IQ whether specific versions have known vulnerabilities
# usage: python sonatype_check.py group:artifact:version [more ...]
#        python sonatype_check.py --diff <diff file saved by tree_tools.py>
import base64, json, os, sys, urllib.request

IQ_URL = "https://iq.yourcompany.com"   # CHANGE ME
MIN_SEVERITY = 0.0                      # raise (e.g. 7.0) only if your policy ignores lower scores

user, token = os.environ.get("IQ_USER"), os.environ.get("IQ_TOKEN")
if not (user and token):
    sys.exit("ERROR: IQ_USER / IQ_TOKEN not set. See setup Step 19.")

args = sys.argv[1:]
if args[:1] == ["--diff"] and len(args) == 2:
    d = json.load(open(args[1], encoding="utf-8"))
    coords = [f'{i["library"]}:{v}' for i in d.get("changed", []) + d.get("added", []) for v in i["after"]]
else:
    coords = args
if not coords:
    print("Nothing to check."); sys.exit(0)

auth = base64.b64encode(f"{user}:{token}".encode()).decode()
purls = [f"pkg:maven/{c.split(':')[0]}/{c.split(':')[1]}@{c.split(':')[2]}?type=jar" for c in coords]
results = []
for i in range(0, len(purls), 100):
    body = json.dumps({"components": [{"packageUrl": p} for p in purls[i:i + 100]]}).encode()
    req = urllib.request.Request(f"{IQ_URL}/api/v2/components/details", data=body,
                                 headers={"Authorization": f"Basic {auth}",
                                          "Content-Type": "application/json"})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=60))
    except Exception as e:
        sys.exit(f"ERROR: could not reach Sonatype IQ ({e}). Mark results UNVERIFIED.")
    for d in data.get("componentDetails", []):
        purl = d.get("component", {}).get("packageUrl", "?")
        issues = [f'{s.get("reference")}({s.get("severity")})'
                  for s in (d.get("securityData") or {}).get("securityIssues", [])
                  if (s.get("severity") or 0) >= MIN_SEVERITY]
        status = ("UNKNOWN" if d.get("matchState") == "unknown"
                  else "VULNERABLE" if issues else "CLEAN")
        results.append(status)
        print(f"{status:10} {purl}  {' '.join(issues)}")

overall = ("NOT CLEAN" if "VULNERABLE" in results
           else "NEEDS MANUAL CHECK" if "UNKNOWN" in results else "CLEAN")
print(f"OVERALL: {overall}")
