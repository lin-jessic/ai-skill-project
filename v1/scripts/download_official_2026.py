"""取得警政署官網 A1 及 A2 (2026)；保留真實來源，不產生假資料。"""
import json, argparse, hashlib, sys, time, zipfile
from pathlib import Path
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parents[1]
CATALOG=json.loads((Path(__file__).parent/'official_sources.json').read_text(encoding='utf-8'))
def download(item, destination):
    dest=destination/item['filename']
    if dest.is_file() and dest.stat().st_size>100:
        print('略過已存在檔案:',dest.name)
        return 'skip'
    tmp=dest.with_suffix(dest.suffix+'.part')
    try:
        req=Request(item['url'],headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SafeRoadCourseProject/1.0','Accept':'*/*'})
        sha=hashlib.sha256();count=0
        with urlopen(req,timeout=120) as response, tmp.open('wb') as w:
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                count+=len(chunk);sha.update(chunk);w.write(chunk)
        if count<100:raise ValueError('內容過小')
        if item['type']=='zip':
            if not zipfile.is_zipfile(tmp):raise ValueError('下載內容不是有效 ZIP')
            with zipfile.ZipFile(tmp) as z:
                if z.testzip():raise ValueError('ZIP CRC 檢查失敗')
        else:
            text=tmp.read_text(encoding='utf-8-sig')
            obj=json.loads(text)
            if not isinstance(obj,(dict,list)):raise ValueError('不是 JSON 物件或陣列')
        tmp.replace(dest)
        metadata={'source_url':item['url'],'sha256':sha.hexdigest(),'bytes':count,'original_filename':item['filename']}
        (destination/(item['filename']+'.source.json')).write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
        print('下載完成:',dest.name, f'{count:,} bytes')
        return 'ok'
    except Exception as exc:
        print('下載失敗:',item['filename'],type(exc).__name__,str(exc))
        tmp.unlink(missing_ok=True)
        return 'failed'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(ROOT/'data'/'raw'))
    parser.add_argument('--only',choices=['all','a1','a2'],default='all')
    args=parser.parse_args()
    dest=Path(args.output).expanduser().resolve();dest.mkdir(parents=True,exist_ok=True)
    chosen=[i for i in CATALOG if args.only=='all' or args.only in i['filename'].lower()]
    print('下載位置：',dest)
    outcomes=[download(x,dest) for x in chosen]
    print('完成：',outcomes.count('ok'),'已存在：',outcomes.count('skip'),'失敗：',outcomes.count('failed'))
    if 'failed' in outcomes:
        print('可從 https://data.gov.tw/dataset/57023 / 57024 點選原始檔案並手動放入上述資料夾。')
        return 2
    return 0
if __name__=='__main__':sys.exit(main())
