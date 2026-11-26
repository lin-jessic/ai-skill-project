"""Fast, dependency-free v4 project integrity check."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    'SKILL.md', 'AGENTS.md', 'README_FIRST.txt', 'app_pwa.py',
    'scripts/studio_engine.py', 'scripts/download_official.py',
    'references/data_sources.md', 'references/verified_official_sources.md',
    'web/index.html', 'web/app.js', 'web/styles.css',
    'web/manifest.webmanifest', 'web/sw.js',
    'examples/DEMO_商圈資料_情境假設_非官方.csv',
]

def main():
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    if missing:
        print('MISSING:')
        print('\n'.join(missing))
        return 1
    skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8-sig')
    checks = {
        'skill_name': 'name: store-opening-advisor' in skill,
        'three_agents': all(x in skill for x in ('01_market_analyst', '02_legal_advisor', '03_procedure_auditor')),
        'audit_output': '04_audit.json' in (ROOT / 'scripts/studio_engine.py').read_text(encoding='utf-8-sig'),
        'pwa_api': "FastAPI" in (ROOT / 'app_pwa.py').read_text(encoding='utf-8-sig'),
        'official_downloader': 'official_download_manifest.json' in (ROOT / 'scripts/download_official.py').read_text(encoding='utf-8-sig'),
    }
    failed = [k for k, ok in checks.items() if not ok]
    print('OpenShop LIFE v4 preflight')
    for key, ok in checks.items(): print(('PASS' if ok else 'FAIL'), key)
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main())
