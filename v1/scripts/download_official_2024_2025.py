# -*- coding: utf-8 -*-
"""警政署 113/114 年 A1+A2 原始檔下載器；只下載，不生成假資料。"""
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
SOURCES = {
    2024: ('https://data.gov.tw/dataset/172969', 'https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/CCAD7AA8-5139-4066-8BE3-D6CC3154C137/resource/0A260239-9958-4046-8834-E68E5EC38406/download'),
    2025: ('https://data.gov.tw/dataset/177136', 'https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/FCD9C2D4-CB71-4EAA-AA4C-B088E5FE3157/resource/EF9B9192-7E4D-4E48-BF8A-AA3D4B298788/download'),
}

def validate_zip(path):
    if not zipfile.is_zipfile(path):
        raise ValueError('不是有效 ZIP；可能下載到錯誤網頁')
    with zipfile.ZipFile(path) as arc:
        data = [n for n in arc.namelist() if n.lower().endswith(('.csv','.json')) and not n.startswith('__MACOSX')]
        if not data:
            raise ValueError('ZIP 裡沒有本專案可讀的 CSV/JSON，請打開 ZIP 確認格式')
        bad = arc.testzip()
        if bad:
            raise ValueError(f'ZIP CRC 驗證失敗: {bad}')
        return data

def download(year):
    page, url = SOURCES[year]
    dest = RAW / f'{year}_A1_A2_official.zip'
    meta = RAW / f'{year}_A1_A2_official.zip.source.json'
    if dest.exists():
        try:
            entries = validate_zip(dest)
            print(f'[{year}] 已存在且 ZIP 驗證成功，保留原檔：{dest.name} ({len(entries)} 個 CSV/JSON)')
            return True
        except Exception as exc:
            print(f'[{year}] 現有檔案格式有問題，為避免覆蓋請先自行確認：{exc}')
            return False
    part = dest.with_suffix('.zip.part')
    part.unlink(missing_ok=True)
    try:
        print(f'[{year}] 下載中：{page}',flush=True)
        req = Request(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)','Accept':'application/zip,application/octet-stream,*/*'})
        h=hashlib.sha256(); total=0
        with urlopen(req,timeout=150) as r,part.open('wb') as f:
            while True:
                chunk=r.read(1024*1024)
                if not chunk: break
                total+=len(chunk); h.update(chunk); f.write(chunk)
                if total%(20*1024*1024)<len(chunk): print(f'  已下載 {total/1024/1024:.1f} MB',flush=True)
        if total<100: raise ValueError('下載內容太小')
        entries=validate_zip(part)
        part.replace(dest)
        meta.write_text(json.dumps({'year':year,'publisher':'內政部警政署','dataset_page':page,'source_url':url,'downloaded_at_utc':datetime.now(timezone.utc).isoformat(),'bytes':total,'sha256':h.hexdigest(),'archive_data_files':entries},ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'[{year}] 成功：{dest.name}，{total:,} bytes，CSV/JSON: {len(entries)}，SHA256: {h.hexdigest()}')
        return True
    except Exception as exc:
        part.unlink(missing_ok=True)
        print(f'[{year}] 下載失敗：{type(exc).__name__}：{exc}')
        print(f'  請改到官網下載：{page}，存成 {dest}')
        return False

def main():
    RAW.mkdir(parents=True,exist_ok=True)
    print('資料目錄：',RAW)
    result=[download(y) for y in (2024,2025)]
    print('\n結果：', '全部下載/核對成功' if all(result) else '部分未成功，請依上述官方頁面手動下載')
    print('注意：2024與2025 為全年 A1+A2，勿再放入相同年度重複來源。')
    print('完成後在專案根目錄執行：python scripts\\run_all.py')
    return 0 if all(result) else 1
if __name__=='__main__':
    sys.exit(main())
