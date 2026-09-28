# dependency-remediator
Use ai to remediate the library vulnerability in the project
.github/agents/dependency-remediator.agent.md
.github/agents/dependency-reviewer.agent.md
.github/instructions/build-files.instructions.md
remediation/findings.tsv            # you paste Excel data here
tools/remediation/parse_findings.py # TSV -> findings.json
tools/remediation/jfrog_versions.sh # versions available in Artifactory
tools/remediation/verify.sh         # confirms resolved versions after the fix
