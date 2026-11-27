"""政府資料下載工具；來源延續 V4。下載不等於完成 ETL。"""
import argparse, hashlib, json, sys
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse
from urllib.request import Request,build_opener,HTTPRedirectHandler
from pathlib import Path
from engine import now,write_json,read_json
ROOT=Path(__file__).resolve().parents[4]
SOURCES={'tax':('9400','https://eip.fia.gov.tw/data/BGMOPEN1.zip'),'population':('77132',None),'metro':('164957',None),'industry':('25346',None),'restaurant':('94937',None)}
def allowed(url):
    p=urlparse(url);h=p.hostname or '';return p.scheme=='https' and (h=='gov.tw' or h.endswith('.gov.tw')) and not p.username and not p.password
class Redirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed(newurl): raise ValueError('非政府 HTTPS 轉址遭拒')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def request(url):
    if not allowed(url):raise ValueError('非政府 HTTPS 來源遭拒')
    return build_opener(Redirect()).open(Request(url,headers={'User-Agent':'OpenShop classroom data tool/5.0'}),timeout=30)
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href');
            if href:self.links.append(href)
def discover(key):
    ident,direct=SOURCES[key];page='https://data.gov.tw/dataset/'+ident
    if direct:return [direct]
    with request(page) as r: raw=r.read(4_000_001)
    if len(raw)>4_000_000:raise ValueError('資料頁過大')
    p=Links();p.feed(raw.decode('utf-8',errors='replace'));out=[]
    for href in p.links:
        url=urljoin(page,href);low=url.lower()
        if allowed(url) and any(x in low for x in ('.csv','.json','.zip','.xlsx','/download','file?oid=','file_id=')) and url not in out:out.append(url)
    return out

def download(key,url,limit,period):
    raw=ROOT/'data'/'raw'/key;raw.mkdir(parents=True,exist_ok=True)
    h=hashlib.sha256();size=0;tmp=raw/'download.part'
    try:
        with request(url) as r,tmp.open('wb') as f:
            kind=r.headers.get('Content-Type','').lower()
            if 'text/html' in kind:raise ValueError('回傳 HTML，非資料檔')
            final=r.geturl()
            while True:
                b=r.read(1024*1024)
                if not b:break
                size+=len(b)
                if size>limit:raise ValueError('檔案超過設定上限')
                h.update(b);f.write(b)
        if not size:raise ValueError('空檔案')
        with tmp.open('rb') as f:head=f.read(256)
        if head.lstrip().lower().startswith((b'<!doctype html',b'<html')):raise ValueError('HTML 偽裝資料檔')
        suffix='.zip' if head.startswith(b'PK') else '.json' if head.lstrip().startswith((b'{',b'[')) else '.csv' if 'csv' in kind or '.csv' in final.lower() else '.bin'
        dest=raw/(h.hexdigest()[:16]+suffix);tmp.replace(dest)
        return {'dataset':key,'source_page':'https://data.gov.tw/dataset/'+SOURCES[key][0],'url':final,'file':str(dest.relative_to(ROOT)),'sha256':h.hexdigest(),'bytes':size,'period':period,'retrieved_at':now(),'status':'downloaded_not_validated'}
    finally:
        if tmp.exists():tmp.unlink()
def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--only',choices=SOURCES);p.add_argument('--list',action='store_true');p.add_argument('--url');p.add_argument('--period');p.add_argument('--max-mb',type=int,default=250);a=p.parse_args();manifest=ROOT/'data'/'official_download_manifest.json'
    if a.check:
        print(json.dumps(read_json(manifest) if manifest.exists() else {'files':[],'errors':[],'note':'尚未下載官方資料'},ensure_ascii=False,indent=2));return 0
    if not a.only:p.error('請指定 --only，避免未經確認下載大型檔案')
    if not 1<=a.max_mb<=1500:p.error('max-mb 須介於 1–1500')
    manifest.parent.mkdir(parents=True,exist_ok=True);m=read_json(manifest) if manifest.exists() else {'files':[],'errors':[]}
    try:
        urls=discover(a.only)
        if a.list:print(json.dumps(urls,ensure_ascii=False,indent=2));return 0
        if a.url and a.url not in urls:raise ValueError('指定網址不在本次官方資料頁解析結果')
        if not a.url and len(urls)!=1:raise ValueError(f'找到 {len(urls)} 個資源，請先 --list 並指定 --url；不任意挑選期間')
        item=download(a.only,a.url or urls[0],a.max_mb*1024**2,a.period);m['files'].append(item);write_json(manifest,m);print(item);return 0
    except Exception as e:m['errors'].append({'dataset':a.only,'timestamp':now(),'error':str(e)});write_json(manifest,m);print(str(e),file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
