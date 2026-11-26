"""Restore OpenShop PWA web assets and check the correct file signatures."""
from pathlib import Path
import hashlib, shutil, sys
root=Path(__file__).resolve().parent
web=root/'web'
checks={
    'index.html': lambda s:s.lstrip().lower().startswith('<!doctype html>') and '<html' in s,
    'styles.css':lambda s:':root' in s and '{' in s and 'document.getElementById' not in s,
    'app.js':lambda s:"'use strict'" in s and 'document.' in s,
    'sw.js':lambda s:'self.addEventListener' in s and 'caches.' in s,
    'manifest.webmanifest':lambda s:'"display"' in s and '"standalone"' in s,
}
print('OpenShop PWA - verify static files')
failed=False
for name,check in checks.items():
    p=web/name
    try:
        s=p.read_text(encoding='utf-8-sig')
        ok=check(s)
        print(('PASS' if ok else 'FAIL'),p.name,len(p.read_bytes()),'bytes')
        failed |= not ok
    except Exception as e:
        print('FAIL',name,e)
        failed=True
try:
    from PIL import Image
    for size in (192,512):
        p=web/'icons'/f'icon-{size}.png'
        with Image.open(p) as im: ok=im.size==(size,size)
        print('PASS' if ok else 'FAIL',p.name)
        failed |= not ok
except ImportError:
    for size in (192,512):
        p=web/'icons'/f'icon-{size}.png'
        sig=p.read_bytes()[:8] if p.exists() else b''
        ok=sig==b'\x89PNG\r\n\x1a\n'
        print('PASS' if ok else 'FAIL',p.name)
        failed |= not ok
if failed:
    print('FAILED. Please copy web folder from this ZIP into v2/web again.')
    sys.exit(1)
print('ALL FILE SIGNATURES OK. Restart server and hard-refresh browser.')
