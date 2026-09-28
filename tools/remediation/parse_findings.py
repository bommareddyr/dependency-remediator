import csv, json, re, sys

COLUMN_ALIASES = {
    "component": ["component", "component name", "coordinates", "display name"],
    "cve":       ["cve", "issue", "vulnerability", "policy violation", "cve id"],
    "severity":  ["threat level", "severity", "cvss", "threat"],
    "fixed":     ["recommended version", "remediation", "fixed version",
                  "next no-violations version", "next non-failing version"],
}

def find_col(headers, key):
    norm = {h.strip().lower(): h for h in headers}
    for alias in COLUMN_ALIASES[key]:
        if alias in norm:
            return norm[alias]
    return None

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig"), delimiter="\t"))
if not rows:
    sys.exit("ERROR: findings.tsv is empty")
cols = {k: find_col(rows[0].keys(), k) for k in COLUMN_ALIASES}
missing = [k for k in ("component", "cve") if not cols[k]]
if missing:
    sys.exit(f"ERROR: missing columns {missing}. Headers found: {list(rows[0].keys())}")

out, skipped = {}, []
for r in rows:
    comp = r[cols["component"]].strip()
    # accepts "g:a:v", "g : a : v", or "g:a:jar:v"
    parts = [p.strip() for p in re.split(r"\s*:\s*", comp) if p.strip()]
    if len(parts) < 3:
        skipped.append(comp); continue
    g, a, v = parts[0], parts[1], parts[-1]
    e = out.setdefault(f"{g}:{a}:{v}", {"group": g, "artifact": a, "installed": v,
                                        "cves": [], "sonatype_recommended": set()})
    e["cves"].append({"id": r[cols["cve"]].strip(),
                      "severity": r[cols["severity"]].strip() if cols["severity"] else ""})
    if cols["fixed"] and r[cols["fixed"]].strip():
        e["sonatype_recommended"].add(r[cols["fixed"]].strip())

for e in out.values():
    e["sonatype_recommended"] = sorted(e["sonatype_recommended"])
print(json.dumps({"findings": list(out.values()), "unparsed_rows": skipped}, indent=2))
