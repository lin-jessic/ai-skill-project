"""Taiwan road-collision normalization and audit helpers. No made-up observations."""
from __future__ import annotations
import hashlib, json, zipfile, io
from pathlib import Path
import pandas as pd
import numpy as np

ALIASES={
 'year':['發生年度','年度','年','year'],
 'month':['發生月份','月','month'],
 'day':['發生日期','日','day'],
 'time':['發生時間','時間','時','time'],
 'category':['事故類別名稱','事故類別','事故類型','category'],
 'location':['發生地點','事故地點','地點','location'],
 'weather':['天候名稱','天候','weather'],
 'cause':['肇因研判子類別名稱-主要','肇因研判大類別名稱-主要','肇因研判子類別名稱','肇因','cause'],
 'lat':['緯度','緯度(度)','latitude','Latitude','lat'],
 'lon':['經度','經度(度)','longitude','Longitude','lng','lon'],
 'party':['當事者順位','當事人順位','party_rank'],
 'city':['縣市','縣市名稱','發生縣市','city'],
}
OUTPUT_COLS=['year','month','day','hour','category','location','weather','cause','lat','lon','city','party']

def load_file(path: Path)->pd.DataFrame:
    if not path.is_file() or path.stat().st_size==0:raise ValueError(f'找不到非空的真實資料：{path}')
    suf=path.suffix.lower()
    if suf=='.zip':
        with zipfile.ZipFile(path) as z:
            names=[n for n in z.namelist() if not n.endswith('/') and Path(n).suffix.lower() in ('.csv','.json') and not n.startswith('__MACOSX')]
            if not names:raise ValueError('壓縮檔找不到 CSV/JSON')
            frames=[]
            for name in names:
                data=z.read(name)
                try:frames.append(read_bytes(data,Path(name).suffix.lower()))
                except ValueError:continue
            if not frames:raise ValueError('ZIP 中無法解析可用資料')
            return pd.concat(frames,ignore_index=True)
    return read_bytes(path.read_bytes(),suf)

def read_bytes(data:bytes,suf:str)->pd.DataFrame:
    if suf=='.csv':
        for enc in ('utf-8-sig','cp950','big5','utf-16'):
            try:
                frame=pd.read_csv(io.BytesIO(data),encoding=enc,low_memory=False)
                if len(frame.columns)>1:return frame
            except (UnicodeError,pd.errors.ParserError):pass
        raise ValueError('CSV 無法解析，請確認格式/編碼')
    if suf=='.json':
        try:obj=json.loads(data.decode('utf-8-sig'))
        except Exception as e:raise ValueError(f'無法解析 JSON: {e}') from e
        if isinstance(obj,list):records=obj
        elif isinstance(obj,dict):
            records=None
            for k in ('result','data','records','items','Data','Records','response'):
                candidate=obj.get(k)
                if isinstance(candidate,list):records=candidate;break
                if isinstance(candidate,dict):
                    for inner in ('records','data','items','Data','Records'):
                        if isinstance(candidate.get(inner),list):records=candidate[inner];break
                    if records is not None:break
            if records is None:
                if any(k in obj for k in ALIASES['lat']+ALIASES['year']):records=[obj]
                else:raise ValueError('JSON 結構未知；請提供原始檔以新增正確對應，勿亂猜欄位')
        else:raise ValueError('JSON 頂層資料格式不支援')
        if not records:raise ValueError('JSON 沒有任何觀測列')
        df=pd.json_normalize(records)
        if df.empty:raise ValueError('JSON 解析結果為空')
        return df
    raise ValueError('僅支援 CSV、JSON、ZIP')

def normalize(df:pd.DataFrame):
    if df.empty:raise ValueError('資料為空，禁止用假資料替代')
    df=df.copy()
    df.columns=[str(c).replace('\ufeff','').strip() for c in df.columns]
    found={key:next((c for c in names if c in df.columns),None) for key,names in ALIASES.items()}
    if not any(found[k] for k in ('year','location','lat')):raise ValueError('不符合事故資料欄位，請檢查官方來源及 schema')
    out=pd.DataFrame(index=df.index)
    for k in found:
        out[k]=df[found[k]].astype('string') if found[k] else pd.Series(pd.NA,index=df.index,dtype='string')
    for field in ('lat','lon','year','month','day'):
        out[field]=pd.to_numeric(out[field].str.replace(',','',regex=False),errors='coerce')
    # ROC year can use 3-digit 114; convert to 2025. If year absent, leave missing.
    out.loc[out.year.between(80,190),'year']+=1911
    def parsehour(x):
        if pd.isna(x):return np.nan
        s=str(x).strip()
        if ':' in s:
            try:return int(s.split(':')[0])
            except ValueError:return np.nan
        s=s.replace('.0','')
        s=''.join(c for c in s if c.isdigit())
        if not s:return np.nan
        # HHMMSS or HHMM or H/HH
        if len(s)>=5:return int(s.zfill(6)[:2])
        if len(s)>=3:return int(s.zfill(4)[:2])
        return int(s)
    out['hour']=out['time'].map(parsehour)
    out.loc[~out.hour.between(0,23),'hour']=np.nan
    out['city']=out.city.fillna(out.location.str.extract(r'^(\S{2,3}?[市縣])',expand=False))
    # handle names with 台/臺 interchange
    out['city']=out.city.str.replace('台','臺',regex=False)
    valid=out.lat.between(21.5,25.5)&out.lon.between(119,123)
    out['map_valid']=valid.fillna(False).astype(bool)
    out['source_row']=np.arange(1,len(out)+1)
    duplicates=int(df.duplicated().sum())
    quality={'input_rows':len(df),'normalized_rows':len(out),'coordinate_valid_rows':int(out.map_valid.sum()),'coordinate_excluded_rows':int((~out.map_valid).sum()),'exact_duplicate_rows_flagged':duplicates,'column_mapping':found,'unit':'source rows (not guaranteed distinct crashes)','accident_id_available':False,'note':'Original rows are not deduplicated: multiple parties may represent one collision.'}
    return out,quality

def digest(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def summary(norm:pd.DataFrame):
    if norm.empty:raise ValueError('沒有實際事故資料')
    counts=lambda col:(norm[col].astype('string').fillna('未提供').value_counts().head(20).astype(int).to_dict())
    hours={str(i):int((norm.hour==i).sum()) for i in range(24)}
    valid=norm[norm.map_valid].copy()
    if len(valid):
        valid['latbin']=(np.floor(valid.lat/.005)*.005).round(3)
        valid['lonbin']=(np.floor(valid.lon/.005)*.005).round(3)
        cells=valid.groupby(['latbin','lonbin'],dropna=False).size().sort_values(ascending=False).reset_index(name='record_count')
        cells=cells.rename(columns={'latbin':'lat','lonbin':'lon'})
    else:cells=pd.DataFrame(columns=['lat','lon','record_count'])
    stats={'record_count':int(len(norm)),'map_record_count':int(len(valid)),'excluded_coordinate_count':int(len(norm)-len(valid)),'hours':hours,'weather':counts('weather'),'categories':counts('category'),'cities':counts('city'),'causes':counts('cause'),'years':counts('year'),'unit':'source rows','map_grid_degrees':0.005,'warning':'Historical frequency only; not current road risk or individual transport destination.'}
    return stats,cells

def audit(norm,quality,stats,cells):
    issues=[]
    if len(norm)!=quality['normalized_rows']:issues.append('Inspector count does not match records')
    if len(norm)!=stats['record_count']:issues.append('Analyst total does not match records')
    if int(norm.map_valid.sum())!=stats['map_record_count']:issues.append('Valid geocoded total mismatch')
    if int((~norm.map_valid).sum())!=stats['excluded_coordinate_count']:issues.append('Invalid geocode count mismatch')
    if sum(stats['hours'].values())!=int(norm.hour.notna().sum()):issues.append('Hour totals do not reconcile')
    if int(cells.record_count.sum())!=int(norm.map_valid.sum()):issues.append('Hotspot grid totals do not reconcile')
    if not norm.loc[norm.map_valid,'lat'].between(21.5,25.5).all() or not norm.loc[norm.map_valid,'lon'].between(119,123).all():issues.append('Bad map coordinates')
    return {'status':'PASS' if not issues else 'FAIL','issues':issues,'checks':['row count','geo count','hour partition','grid reconciliation','coordinate bounds'],'limitation':'No verified unique crash ID; event count cannot be asserted. No hospitalization data.'}
