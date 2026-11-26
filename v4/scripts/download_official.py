"""OpenShop Taiwan official datasets: fully unattended download, no file chooser.

Downloads are from resource links published on data.gov.tw, never fabricated.
Run from v2: python -m scripts.download_official
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
LOG = ROOT / 'data' / 'official_download_manifest.json'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36'
SOURCES = {
    'tax': ('9400', 'tax', 'https://eip.fia.gov.tw/data/BGMOPEN1.zip'),
    'population': ('77132', 'population', None),
    'metro': ('164957', 'transit', None),
    'industry': ('25346', 'market', None),
    'restaurant': ('94937', 'market', None),
}
ALLOWED_HOST_SUFFIXES = ('.gov.tw', '.nat.gov.tw')
MAX_FILE_BYTES = {'tax': 1_500_000_000, 'population': 250_000_000,
                  'metro': 100_000_000, 'industry': 100_000_000,
                  'restaurant': 100_000_000}

class SourcePageParser(HTMLParser):
    """Extract links and adjacent visible text from the resources section."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.entries = []
        self.active_href = None
        self.active_parts = []
        self.recent_text = ''
        self.last_item = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and self.inside:
            self.active_href = attrs.get('href', '')
            self.active_parts = []

    def handle_data(self, data):
        s = data.strip()
        if not s:
            return
        if '資料資源下載網址' in s:
            self.inside = True
            return
        if self.inside and any(word in s for word in ('提供機關聯絡人', '提供機關', '更新頻率', '授權方式')) and len(s) < 25:
            self.inside = False
            return
        if self.inside:
            if self.active_href is not None:
                self.active_parts.append(s)
            elif self.last_item is not None and len(self.last_item['note']) < 250:
                self.last_item['note'] += ' ' + s
            self.recent_text = s

    def handle_endtag(self, tag):
        if tag == 'li':
            self.last_item = None
        if tag == 'a' and self.active_href is not None:
            item = {'href': html.unescape(self.active_href),
                    'label': ' '.join(self.active_parts), 'note': ''}
            self.entries.append(item)
            self.last_item = item
            self.active_href = None
            self.active_parts = []


def valid_official_url(url):
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    return parsed.scheme == 'https' and (host == 'gov.tw' or host.endswith(ALLOWED_HOST_SUFFIXES))


def request(url, timeout=40):
    if not valid_official_url(url):
        raise ValueError('Non-government download URL rejected: ' + url[:160])
    return urlopen(Request(url, headers={'User-Agent': UA, 'Accept': '*/*'}), timeout=timeout)


def fetch_entries(dataset):
    page = 'https://data.gov.tw/dataset/' + dataset
    with request(page) as r:
        content = r.read(4_000_000)
    parser = SourcePageParser()
    parser.feed(content.decode('utf-8', errors='replace'))
    entries = []
    seen = set()
    for item in parser.entries:
        url = urljoin(page, item['href'])
        label = (item['label'] + ' ' + item['note']).strip()
        if not valid_official_url(url):
            continue
        if not re.search(r'CSV|JSON|ZIP|XLSX?|ODS', label, re.I) and not re.search(r'\.(csv|json|zip|xlsx?)(\?|$)|/download', url, re.I):
            continue
        if url in seen:
            continue
        seen.add(url)
        entries.append({'url': url, 'label': label})
    if not entries:
        raise ValueError('No official resource links parsed. Portal markup may have changed.')
    return entries


def extract_ym(text, key):
    """YYYYMM from public resource label; 2024/25/26 or ROC 113/114/115."""
    if key == 'population':
        m = re.search(r'(?<!\d)(11[345])\s*[-/]?\s*(0[1-9]|1[0-2])(?!\d)', text)
        if m:
            return (int(m.group(1)) + 1911) * 100 + int(m.group(2))
    m = re.search(r'(?<!\d)(202[456])\s*[-年/._]?\s*(1[0-2]|0?[1-9])\s*月?', text)
    if m:
        return int(m.group(1)) * 100 + int(m.group(2))
    m = re.search(r'(?<!\d)(202[456])(0[1-9]|1[0-2])(?!\d)', text)
    if m:
        return int(m.group(1)) * 100 + int(m.group(2))
    return None


def plan_resources(entries, key, all_months=False):
    if key == 'restaurant':
        return [(None, entries[-1])]
    matched = []
    for e in entries:
        ym = extract_ym(e['label'], key)
        if ym and 202401 <= ym <= 202612 and (ym % 100) <= 12:
            matched.append((ym, e))
    if not matched:
        raise ValueError('No 2024-2026 dated downloadable resources detected for ' + key)
    by_month = {}
    for ym, e in matched:
        by_month[ym] = e
    if all_months:
        return sorted(by_month.items())
    latest_by_year = {}
    for ym in sorted(by_month):
        latest_by_year[ym // 100] = (ym, by_month[ym])
    return [latest_by_year[y] for y in sorted(latest_by_year)]


def verify_file(path):
    if not path.is_file() or path.stat().st_size < 20:
        raise ValueError('Empty or unexpectedly tiny resource')
    with path.open('rb') as f:
        head = f.read(4096).lstrip()
    lower = head.lower()
    if lower.startswith((b'<!doctype html', b'<html', b'<?xml')) or b'<html' in lower[:500]:
        raise ValueError('Server returned HTML/XML rather than downloadable data')
    if path.suffix.lower() == '.zip' and not zipfile.is_zipfile(path):
        raise ValueError('Not a valid ZIP archive')
    if path.suffix.lower() == '.json':
        if head[:1] not in (b'{', b'['):
            raise ValueError('Not JSON')
    if path.suffix.lower() == '.csv':
        if b'\0' in head:
            raise ValueError('Binary content is not a CSV')
    return True


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def extension(url, content_type):
    path = urlparse(url).path.lower()
    for ext in ('.zip', '.csv', '.json', '.xlsx', '.xls'):
        if path.endswith(ext):
            return ext
    t = (content_type or '').lower()
    if 'zip' in t:
        return '.zip'
    if 'json' in t:
        return '.json'
    if 'excel' in t or 'spreadsheet' in t:
        return '.xlsx'
    return '.csv'


def save_download(key, ym, entry, log):
    folder = RAW / SOURCES[key][1]
    folder.mkdir(parents=True, exist_ok=True)
    url = entry['url']
    stem = {'tax': 'BGMOPEN1', 'population':'village_population',
            'metro':'taoyuan_metro', 'industry':'industry_counts',
            'restaurant':'restaurant_survey'}[key]
    suffix = '_' + str(ym) if ym else ''
    for old_ext in ('.csv', '.zip', '.json', '.xlsx', '.xls'):
        old = folder / (stem + suffix + old_ext)
        if old.exists():
            try:
                verify_file(old)
                print('  [SKIP valid existing]', old.relative_to(ROOT))
                log['files'].append({'dataset':key,'status':'existing','path':str(old.relative_to(ROOT)),
                                     'size_bytes':old.stat().st_size,'sha256':sha256(old),'url':url})
                return True
            except ValueError:
                print('  [INVALID previous file]', old.name)
    error = ''
    for attempt in range(1, 4):
        part = folder / (stem + suffix + '.download')
        part.unlink(missing_ok=True)
        try:
            with request(url,timeout=55) as res:
                res_url = res.geturl()
                if not valid_official_url(res_url):
                    raise ValueError('Unexpected non-government redirect: ' + res_url)
                ext = extension(res_url, res.headers.get('Content-Type'))
                dest = folder / (stem + suffix + ext)
                limit = MAX_FILE_BYTES[key]
                count = 0
                with part.open('wb') as out:
                    while True:
                        buf = res.read(512 * 1024)
                        if not buf: break
                        count += len(buf)
                        if count > limit:
                            raise ValueError('Exceeded safety size limit')
                        out.write(buf)
            # Verify temp by suffix without copying large file
            temp_verified = folder / (stem + suffix + ext)
            if ext == '.zip' and not zipfile.is_zipfile(part):
                raise ValueError('Invalid ZIP')
            if count < 20:
                raise ValueError('Empty response')
            with part.open('rb') as inp:
                h = inp.read(4096).lstrip().lower()
            if h.startswith((b'<!doctype html', b'<html', b'<?xml')) or b'<html' in h[:500]:
                raise ValueError('HTML/XML instead of data')
            if ext == '.csv' and b'\0' in h:
                raise ValueError('Binary response instead of CSV')
            if ext == '.json' and h[:1] not in (b'{', b'['):
                raise ValueError('Response is not JSON')
            part.replace(dest)
            log['files'].append({'dataset':key,'period':ym,'status':'downloaded',
                                 'path':str(dest.relative_to(ROOT)), 'size_bytes':count,
                                 'sha256':sha256(dest), 'url':url,'resource_label':entry['label']})
            print('  [OK]', dest.relative_to(ROOT), f'({count:,} bytes)')
            return True
        except Exception as exc:
            error = str(exc)
            part.unlink(missing_ok=True)
            print('  [RETRY %d/3] %s' % (attempt, error[:180]))
            if attempt < 3: time.sleep(attempt)
    log['files'].append({'dataset':key,'period':ym,'status':'failed', 'url':url,'error':error})
    print('  [FAILED]', key, ym, error[:180])
    return False


def check():
    print('\nLOCAL DOWNLOAD STATUS (file presence is not schema validation)')
    for key, (_, folder, _) in SOURCES.items():
        directory = RAW / folder
        files = [p for p in directory.glob('*') if p.is_file() and not p.name.endswith('.download')] if directory.exists() else []
        print('  %-12s: %d file(s) in data/raw/%s' % (key, len(files), folder))
    print('Manifest:', LOG)


def main(argv=None):
    args = argparse.ArgumentParser(description='Download real Taiwan government OpenShop datasets automatically')
    args.add_argument('--check',action='store_true',help='list already saved files')
    args.add_argument('--all-months',action='store_true',help='download all available months for 2024-2026, not just annual latest')
    args.add_argument('--skip-tax',action='store_true',help='skip very large tax dataset')
    args.add_argument('--only',choices=list(SOURCES),help='download only specified dataset')
    a = args.parse_args(argv)
    if a.check:
        check();return 0
    LOG.parent.mkdir(parents=True,exist_ok=True)
    log = {'generated_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
           'mode': 'all-months' if a.all_months else 'latest-month-per-year',
           'files':[], 'errors':[], 'sources':{k:'https://data.gov.tw/dataset/'+v[0] for k,v in SOURCES.items()}}
    keys = [a.only] if a.only else list(SOURCES)
    if a.skip_tax:
        keys = [k for k in keys if k!='tax']
    successes = 0;failed = 0
    for key in keys:
        dataset, _, direct = SOURCES[key]
        print('\n==== %s | data.gov.tw/dataset/%s ====' % (key,dataset),flush=True)
        try:
            if direct:
                plans = [(None, {'url':direct,'label':'Official direct source'})]
            else:
                entries = fetch_entries(dataset)
                plans = plan_resources(entries,key,a.all_months)
            print('Resources selected:',len(plans),flush=True)
            for ym, entry in plans:
                if save_download(key,ym,entry,log): successes += 1
                else: failed += 1
        except Exception as ex:
            failed+=1
            print('[SOURCE ERROR]',str(ex)[:280],flush=True)
            log['errors'].append({'dataset':key,'reason':str(ex), 'source_page':'https://data.gov.tw/dataset/'+dataset})
        LOG.write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
    print('\n==== COMPLETE: %d succeeded/existing, %d failed ====' % (successes,failed))
    check()
    if failed:
        print('Some government download URLs were not reachable. See official_download_manifest.json.')
    print('NOTE: Official files downloaded != dashboard integration completed.')
    return 0 if not failed else 1

if __name__=='__main__':
    sys.exit(main())
