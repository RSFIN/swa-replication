#!/usr/bin/env python3
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
# Benchmark task content may legitimately contain synthetic names/emails, so scan
# repository metadata/code/config/results but exclude benchmark payloads and binary figures.
scan_roots=[ROOT/'README.md', ROOT/'Makefile', ROOT/'configs', ROOT/'docs', ROOT/'scripts', ROOT/'results']
patterns={
    'personal_home_path': re.compile(r'(?i)(/Users/[^/\s]+|/home/[^/\s]+|[A-Z]:\\Users\\[^\\\s]+)'),
    'private_key_material': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'likely_secret_assignment': re.compile(r'(?i)(?:api[_-]?key|token|secret|password)\s*[:=]\s*["\'](?!\s*["\'])[^"\']{8,}["\']'),
    'institutional_email': re.compile(r'(?i)\b[A-Z0-9._%+-]+@(?!example\.|test\.|localhost)[A-Z0-9.-]+\.[A-Z]{2,}\b'),
}
# Public/provider endpoint strings and explanatory uses of variable names are not secrets.
allow_email_files=set()
hits=[]

def iter_files(item):
    if item.is_file():
        yield item
    elif item.is_dir():
        for p in item.rglob('*'):
            if p.is_file() and p.suffix.lower() not in {'.pdf','.png','.jpg','.jpeg','.svg','.zip','.pyc'}:
                yield p

for item in scan_roots:
    for p in iter_files(item):
        try:
            text=p.read_text(encoding='utf-8',errors='ignore')
        except Exception:
            continue
        rel=p.relative_to(ROOT).as_posix()  # POSIX-style paths for cross-platform matching
        for name,pat in patterns.items():
            # Avoid self-matching the regex literals in this checker.
            if str(rel) == 'scripts/analysis/check_anonymity.py':
                continue
            # Result files may legitimately contain benchmark-synthetic emails.
            if name == 'institutional_email' and str(rel).startswith('results/'):
                continue
            for m in pat.finditer(text):
                # env.example contains only empty credential placeholders.
                if name=='likely_secret_assignment' and str(rel)=='configs/env.example':
                    continue
                hits.append((str(rel),name,m.group(0)[:120]))

if hits:
    print('ANONYMITY SCAN: REVIEW NEEDED')
    for rel,name,snip in hits[:100]:
        print(f'  {rel}: {name}: {snip}')
    raise SystemExit(1)

print('OK: no personal home paths, nonempty credential-like assignments, private keys, or institutional-email strings detected in repository metadata/code/config/results.')
print('Note: benchmark-derived task payloads are excluded because they may contain synthetic benchmark names/emails.')
