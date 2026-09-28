# parse_findings.py - converts Sonatype rows pasted from Excel into clean JSON
# usage: python parse_findings.py   (reads findings.tsv in this same folder)
import csv, json, os, re, sys

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "findings.tsv")

COLUMN_ALIASES = {
    "component":   ["component", "component name", "coordinates", "display name"],
    "cve":         ["cve", "issue", "vulnerability", "cve id", "policy violation"],
    "severity":    ["threat level", "severity", "cvss", "threat"],
    "recommended": ["target version", "approved version", "recommended version", "remediation",
                    "fixed version", "next no-violations version", "next non-failing version"],
    "status":      ["status", "waiver", "waived"],
}

def find_col(headers, key):
    norm = {h.strip().lower(): h for h in headers if h}
    return next((norm[a] for a in COLUMN_ALIASES[key] if a in norm), None)

def cell(row, key):
    return (row.get(cols[key]) or "").strip() if cols[key] else ""

if not os.path.exists(FILE):
    sys.exit(f"ERROR: {FILE} not found. Paste Sonatype rows into it first.")
rows = list(csv.DictReader(open(FILE, encoding="utf-8-sig"), delimiter="\t"))
if not rows:
    sys.exit("ERROR: findings.tsv is empty.")
cols = {k: find_col(rows[0].keys(), k) for k in COLUMN_ALIASES}
missing = [k for k in ("component", "cve") if not cols[k]]
if missing:
    sys.exit(f"ERROR: could not find columns {missing}. Headers seen: {list(rows[0].keys())}")

out, unparsed, waived = {}, [], []
for r in rows:
    comp = cell(r, "component")
    if "waiv" in cell(r, "status").lower():
        waived.append(comp); continue
    parts = [p for p in re.split(r"\s*:\s*", comp) if p]
    if len(parts) < 3:
        if comp: unparsed.append(comp)
        continue
    g, a, v = parts[0], parts[1], parts[-1]
    e = out.setdefault(f"{g}:{a}", {"group": g, "artifact": a, "installed": v,
                                    "cves": [], "recommended": set()})
    e["cves"].append({"id": cell(r, "cve"), "severity": cell(r, "severity")})
    if cell(r, "recommended"):
        e["recommended"].add(cell(r, "recommended"))

for e in out.values():
    recs = sorted(e["recommended"])
    e["recommended"] = recs[-1] if recs else ""
    e["recommended_conflict"] = recs if len(recs) > 1 else []
print(json.dumps({"findings": list(out.values()), "unparsed_rows": unparsed,
                  "waived_rows": waived}, indent=2))
