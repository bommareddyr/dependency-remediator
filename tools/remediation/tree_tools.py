# tree_tools.py - dependency tree helper for Maven and Gradle
# Run from the repository root:
#   python tree_tools.py snapshot <name> [:gradleSubproject ...]
#   python tree_tools.py roots <name>
#   python tree_tools.py check <name>
#   python tree_tools.py diff <before> <after>
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.getcwd()
WORK = os.path.join(HERE, "work", os.path.basename(REPO))
os.makedirs(WORK, exist_ok=True)
DEP = re.compile(r"^(?P<prefix>[\s|+\\`-]*)(?P<body>[A-Za-z0-9_.\-]+:[A-Za-z0-9_.\-]+.*)$")

def vkey(v):
    return [int(x) for x in re.findall(r"\d+", v)] or [0]

def snapshot(name, subprojects):
    out = os.path.join(WORK, f"{name}.txt")
    if os.path.exists(out):
        os.remove(out)
    if os.path.exists(os.path.join(REPO, "pom.xml")):
        mvn = shutil.which("mvn") or sys.exit("ERROR: mvn not found on PATH")
        r = subprocess.run([mvn, "-B", "-q", "dependency:tree", f"-DoutputFile={out}",
                            "-DappendOutput=true"], cwd=REPO, capture_output=True, text=True)
    else:
        gw = os.path.join(REPO, "gradlew.bat" if os.name == "nt" else "gradlew")
        if not os.path.exists(gw):
            sys.exit("ERROR: no pom.xml or gradlew in this folder. Run from the repo root.")
        cmd = [gw, "-q"]
        for p in (subprojects or [""]):
            cmd += [f"{p}:dependencies" if p else "dependencies", "--configuration", "runtimeClasspath"]
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        open(out, "w", encoding="utf-8").write(r.stdout)
    if r.returncode != 0:
        sys.exit(f"ERROR: dependency tree failed.\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    print(f"Saved snapshot '{name}'")

def parse(name):
    path = os.path.join(WORK, f"{name}.txt")
    if not os.path.exists(path):
        sys.exit(f"ERROR: snapshot '{name}' not found. Run: snapshot {name}")
    entries, module = [], ""
    for raw in open(path, encoding="utf-8", errors="replace"):
        line = raw.rstrip()
        if line.startswith("Project '"):
            module = line; continue
        m = DEP.match(line)
        if not m or re.search(r"\((c|n)\)$", line):
            continue
        prefix, body = m.group("prefix"), re.sub(r"\s*\(\*\)$", "", m.group("body"))
        gradle = "---" in prefix
        depth = len(prefix) // (5 if gradle else 3)
        if gradle:
            left, _, right = body.partition(" -> ")
            parts = left.split(":")
            version = right.split()[0] if right else (parts[2].split()[0] if len(parts) > 2 else "")
        else:
            parts = body.split()[0].split(":")
            version = parts[-2] if len(parts) >= 5 else (parts[3] if len(parts) == 4 else "")
        if depth == 0:
            module = f"{parts[0]}:{parts[1]}"; continue
        entries.append({"module": module, "depth": depth,
                        "ga": f"{parts[0]}:{parts[1]}", "version": version})
    return entries

def findings():
    r = subprocess.run([sys.executable, os.path.join(HERE, "parse_findings.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr or r.stdout)
    return {f"{f['group']}:{f['artifact']}": f for f in json.loads(r.stdout)["findings"]}

def roots(name):
    wanted, direct, groups, root = findings(), {}, {}, None
    seen = set()
    for e in parse(name):
        if e["depth"] == 1:
            root = e
        if e["ga"] not in wanted:
            continue
        seen.add(e["ga"])
        item = {"library": e["ga"], "resolved": e["version"],
                "recommended": wanted[e["ga"]]["recommended"]}
        if e["depth"] == 1:
            direct[e["ga"]] = item
        else:
            key = f'{root["ga"]}:{root["version"]}'
            groups.setdefault(key, {})[e["ga"]] = item
    result = {
        "direct": list(direct.values()),
        "by_root": sorted([{"root": k, "fixes": len(v), "libraries": list(v.values())}
                           for k, v in groups.items()], key=lambda x: -x["fixes"]),
        "not_in_this_repo": sorted(set(wanted) - seen),
    }
    print(json.dumps(result, indent=2))

def check(name):
    wanted, resolved = findings(), {}
    for e in parse(name):
        resolved.setdefault(e["ga"], set()).add(e["version"])
    for ga, f in sorted(wanted.items()):
        vers, target = sorted(resolved.get(ga, [])), f["recommended"]
        if not vers:
            status = "GONE (no longer in build)"
        elif not target:
            status = "NO TARGET (needs human)"
        elif all(vkey(v) >= vkey(target) for v in vers):
            status = "PASS"
        else:
            status = "FAIL"
        print(f"{status:28} {ga}  resolved={','.join(vers) or '-'}  target={target or '-'}")

def diff(a, b):
    def versions(n):
        d = {}
        for e in parse(n):
            d.setdefault(e["ga"], set()).add(e["version"])
        return d
    before, after = versions(a), versions(b)
    result = {
        "changed": [{"library": k, "before": sorted(before[k]), "after": sorted(after[k])}
                    for k in sorted(before.keys() & after.keys()) if before[k] != after[k]],
        "added": [{"library": k, "after": sorted(after[k])} for k in sorted(after.keys() - before.keys())],
        "removed": sorted(before.keys() - after.keys()),
    }
    path = os.path.join(WORK, f"diff_{a}_{b}.json")
    json.dump(result, open(path, "w", encoding="utf-8"), indent=2)
    print(json.dumps(result, indent=2))
    print(f"Saved {path}")

if __name__ == "__main__":
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if cmd == "snapshot" and args: snapshot(args[0], args[1:])
    elif cmd == "roots" and args: roots(args[0])
    elif cmd == "check" and args: check(args[0])
    elif cmd == "diff" and len(args) == 2: diff(args[0], args[1])
    else: sys.exit(__doc__ or "see usage at top of file")
