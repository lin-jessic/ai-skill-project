"""Download official datasets with clear status, metadata and SHA256. No placeholder rows."""
import argparse,datetime,hashlib,json,sys,zipfile
from pathlib import Path
import requests
from scripts.logic import ROOT,RAW,SOURCES

def download(key,force=False):
    s=SOURCES[key];dst=RAW/s['file'];dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() and not force:
        print(f'[SKIP] {key}: 已有 {dst.relative_to(ROOT)}');return True
    tmp=dst.with_name(dst.name+'.part')
    try:
        with requests.get(s['url'],timeout=(12,90),stream=True,headers={'User-Agent':'OpenShopAI-Education/2.0'}) as r:
            r.raise_for_status()
            size=0
            with tmp.open('wb') as f:
                for part in r.iter_content(1024*256):
                    if not part:continue
                    size+=len(part)
                    if size>450*1024*1024:raise ValueError('資料超過 450 MB 保護上限')
                    f.write(part)
        if tmp.stat().st_size<100:raise ValueError('檔案過小，疑似非資料內容')
        with tmp.open('rb') as f:signature=f.read(512).lstrip().lower()
        if signature.startswith((b'<!doctype html',b'<html',b'<?xml')):raise ValueError('取得網頁／錯誤頁，不是資料檔')
        if dst.suffix=='.zip' and not zipfile.is_zipfile(tmp):raise ValueError('下載內容不是有效 ZIP')
        sha=hashlib.sha256(tmp.read_bytes()).hexdigest()
        tmp.replace(dst)
        meta={'key':key,'dataset':s['dataset'],'title':s['title'],'source_url':s['url'],'downloaded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'file':str(dst.relative_to(ROOT)),'bytes':size,'sha256':sha,'status':'downloaded','note':'下載成功不代表資料綱要已完成相容性驗證'}
        manifest=ROOT/'data'/'download_manifest.json';old=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {};old[key]=meta;manifest.write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'[OK] {key}: {size:,} bytes -> {dst.relative_to(ROOT)}');return True
    except Exception as e:
        tmp.unlink(missing_ok=True)
        print(f'[FAIL] {key}: {e}\n  官方頁面：https://data.gov.tw/dataset/{s["dataset"]}')
        return False

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--only',choices=list(SOURCES));p.add_argument('--force',action='store_true');args=p.parse_args()
    keys=[args.only] if args.only else list(SOURCES)
    failed=[key for key in keys if not download(key,args.force)]
    print(f'成功/已存在：{len(keys)-len(failed)} / {len(keys)}。失敗資料請到官方頁面手動下載並保留原格式。')
    sys.exit(bool(failed))
