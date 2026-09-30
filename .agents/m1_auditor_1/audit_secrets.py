import os
import pathlib
import re

root = pathlib.Path(r"C:\Users\Asus\Documents\antigravity\hopeful-curie")

key_patterns = [
    re.compile(r"80e0522929707e101b71fe4c97f7a563"),
    re.compile(r"jswPNZNilb8Iasj88YnTU8DMwiFHVcxHxKQ2sCKVi98"),
    re.compile(r"(?:api_key|secret_key|solscan_key|gmgn_key|auth_token)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", re.I),
    re.compile(r"gmgn_[a-zA-Z0-9]{20,}", re.I),
    re.compile(r"eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}")
]

findings = []

for p in root.rglob("*"):
    if not p.is_file():
        continue
    parts = p.parts
    if any(x.startswith(".git") or x.startswith(".cache") or x == "__pycache__" for x in parts):
        continue
    if p.name == ".env":
        continue
    # We also check .agents to see if any agent leaked secrets
    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(content.splitlines(), start=1):
            for pat in key_patterns:
                m = pat.search(line)
                if m:
                    # Ignore comment or doc references that are just examples or tests checking for leaks
                    findings.append({
                        "file": str(p),
                        "line": idx,
                        "match": m.group(0),
                        "snippet": line.strip()
                    })
    except Exception as e:
        print(f"Error reading {p}: {e}")

print(f"Total findings: {len(findings)}")
for f in findings:
    print(f"{f['file']}:{f['line']} -> {f['match']}")
    print(f"   Snippet: {f['snippet']}")
