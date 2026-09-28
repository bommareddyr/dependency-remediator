# risk.py - classifies a version change as LOW / MEDIUM / HIGH
# usage: python risk.py <group:artifact> <fromVersion> <toVersion>
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) != 4:
    sys.exit("usage: python risk.py <group:artifact> <from> <to>")
ga, old, new = sys.argv[1:4]

def nums(v):
    return ([int(x) for x in re.findall(r"\d+", v)] + [0, 0, 0])[:3]

patterns = [l.strip() for l in open(os.path.join(HERE, "high_risk_libraries.txt"), encoding="utf-8")
            if l.strip() and not l.startswith("#")]
framework = any(ga.startswith(p) for p in patterns)
o, n = nums(old), nums(new)

if n < o:
    level, why = "HIGH", "version goes DOWN"
elif n[0] != o[0]:
    level, why = "HIGH", "major version change - likely breaking"
elif framework and n[1] != o[1]:
    level, why = "HIGH", "minor version change of a framework library"
elif n[1] != o[1]:
    level, why = "MEDIUM", "minor version change"
else:
    level, why = "LOW", "patch-level change"
print(f"{level}: {why} ({ga} {old} -> {new})")
