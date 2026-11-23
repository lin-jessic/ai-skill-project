"""Download raw government A1 accidents, recording official provenance. No mock fallback."""
from pathlib import Path
import argparse,hashlib,json,sys,urllib.request

SOURCE='https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/F4077949-50CC-4640-8114-79958CC8BBEA/resource/0DFEFF78-EAA2-4402-B759-BFCC63B002A7/download'
ROOT=Path(__file__).resolve().parents[1]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--url',default=SOURCE);ap.add_argument('--output',default=str(ROOT/'data/raw/a1_official.json'));a=ap.parse_args()
 dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
 try:
  req=urllib.request.Request(a.url,headers={'User-Agent':'Mozilla/5.0 SafeRoadCourseProject/1.0'})
  with urllib.request.urlopen(req,timeout=75) as response:
   body=response.read()
  if len(body)<100:raise ValueError('下載內容過小，可能是錯誤頁面')
  # Download is expected to be JSON; reject server-generated HTML/errors.
  if body.lstrip()[:1] not in (b'{',b'['):raise ValueError('資源不是 JSON，請開啟官方頁面手動下載')
  json.loads(body.decode('utf-8-sig'))
  dest.write_bytes(body)
  meta={'url':a.url,'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'official_dataset':'https://data.gov.tw/dataset/57023'}
  dest.with_suffix(dest.suffix+'.source.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
  print('官方資料下載成功：',dest,'SHA256:',meta['sha256'])
 except Exception as exc:
  print('下載失敗：',exc,'\n請從 https://data.gov.tw/dataset/57023 手動下載 JSON 放到 data/raw。',file=sys.stderr)
  raise SystemExit(2)
if __name__=='__main__':main()
