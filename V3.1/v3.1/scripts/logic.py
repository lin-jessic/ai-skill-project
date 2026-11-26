"""OpenShop calculations and cautious transformations. No invented official records."""
from __future__ import annotations
import csv
import io
import json
import math
import re
import zipfile
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw'
OUT=ROOT/'outputs'
CITIES=['臺北市','新北市','桃園市','臺中市','臺南市','高雄市','基隆市','新竹市','新竹縣','苗栗縣','彰化縣','南投縣','雲林縣','嘉義市','嘉義縣','屏東縣','宜蘭縣','花蓮縣','臺東縣','澎湖縣','金門縣','連江縣']
CITY_ALIAS={'台北市':'臺北市','台中市':'臺中市','台南市':'臺南市','台東縣':'臺東縣'}
SHOP_TYPES=['手搖飲店','咖啡廳','早餐店','甜點店','餐館','服飾店','花店']
FOOD=set(SHOP_TYPES[:5])
SOURCES={
 'tax':{'title':'財政部全國營業（稅籍）登記資料','dataset':'9400','url':'https://eip.fia.gov.tw/data/BGMOPEN1.zip','file':'tax/BGMOPEN1.zip','kind':'官方原始 ZIP；提供直連'},
 'population':{'title':'內政部村里人口資料','dataset':'77132','url':'https://data.gov.tw/dataset/77132','file':'population/population.csv','kind':'官方資料頁；請選當期資源'},
 'metro':{'title':'桃園捷運站運量','dataset':'164957','url':'https://data.gov.tw/dataset/164957','file':'transit/taoyuan_metro.csv','kind':'官方資料頁；請選當期資源'},
 'industry':{'title':'商業登記家數及資本額','dataset':'25346','url':'https://data.gov.tw/dataset/25346','file':'market/industry.csv','kind':'官方資料頁；請選當期資源'},
 'restaurant':{'title':'餐飲業經營實況','dataset':'94937','url':'https://data.gov.tw/dataset/94937','file':'market/restaurant_statistics.csv','kind':'官方資料頁；請選當期資源'},
}


def clean_city(s):
    s=str(s or '').strip();return CITY_ALIAS.get(s,s)

def money_sim(price=65, variable=25, daily=100, rent=35000, payroll=75000, fixed_other=20000, days=26, initial=800000, dinein_share=0.2, delivery_share=0.25, commission=0.30, delivery_packaging=4):
    values=[price,variable,daily,rent,payroll,fixed_other,days,initial,dinein_share,delivery_share,commission,delivery_packaging]
    if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):raise ValueError('所有參數須是有限數值')
    if any(v<0 for v in values):raise ValueError('費用、數量與比例不可為負')
    if dinein_share+delivery_share>1+1e-9:raise ValueError('內用與外送占比不可超過 100%')
    if dinein_share>1 or delivery_share>1 or commission>1:raise ValueError('比例不可大於 100%')
    orders=daily*days; takeaway_share=1-dinein_share-delivery_share
    revenue=orders*price
    delivery_fee=orders*delivery_share*price*commission
    packaging=orders*delivery_share*delivery_packaging
    variable_cost=orders*variable
    fixed=rent+payroll+fixed_other
    contribution=price-variable-delivery_share*(price*commission+delivery_packaging)
    monthly_profit=revenue-variable_cost-fixed-delivery_fee-packaging
    breakeven=math.ceil(fixed/(days*contribution)) if days>0 and contribution>0 else None
    runway=initial/abs(monthly_profit) if monthly_profit<0 else None
    return dict(revenue=round(revenue,2),monthly_cost=round(variable_cost+fixed+delivery_fee+packaging,2),monthly_profit=round(monthly_profit,2),orders=orders,variable_cost=variable_cost,fixed_cost=fixed,delivery_fee=round(delivery_fee,2),packaging=round(packaging,2),contribution_per_order=round(contribution,2),breakeven_daily=breakeven,runway_months=round(runway,2) if runway is not None else None,shares={'內用':dinein_share,'外帶':max(0,takeaway_share),'外送':delivery_share},notes='僅假設值試算；未計創業初期投入、稅捐、折舊、利息與業主薪資等；不能代表實際獲利或顧客偏好。')

def read_any(path:Path,max_rows=1_000_000):
    """Reads CSV / JSON / ZIP with conservative file limits. No pickle/executable files."""
    path=Path(path)
    if not path.exists():return pd.DataFrame()
    if path.stat().st_size>250*1024**2:raise ValueError('檔案超過 250 MB；大型稅籍原始 ZIP 請先以 CLI 分批篩選')
    if path.suffix.lower()=='.zip':
        with zipfile.ZipFile(path) as z:
            files=[i for i in z.infolist() if i.filename.lower().endswith(('.csv','.json')) and not i.is_dir() and i.file_size<350*1024**2]
            if not files:return pd.DataFrame()
            i=files[0]
            if i.file_size>100*max(1,i.compress_size):raise ValueError('ZIP 解壓比過大')
            with z.open(i) as f:return _parse_bytes(f.read(),i.filename,max_rows)
    return _parse_bytes(path.read_bytes(),path.name,max_rows)

def _parse_bytes(raw,name,max_rows):
    if name.lower().endswith('.json'):
        d=json.loads(raw.decode('utf-8-sig'))
        if isinstance(d,dict):
            for key in ('data','result','records','items'):
                if isinstance(d.get(key),list):d=d[key];break
        return pd.DataFrame(d).head(max_rows)
    for encoding in ('utf-8-sig','cp950','big5','utf-16'):
        try:
            frame=pd.read_csv(io.BytesIO(raw),encoding=encoding,nrows=max_rows,low_memory=False)
            if len(frame.columns)==1 and ('\t' in str(frame.columns[0])):continue
            return frame
        except (UnicodeError,UnicodeDecodeError):continue
    raise ValueError('CSV 編碼無法辨識')

def find_col(df, *aliases):
    lookup={str(c).strip().lower().replace(' ',''):c for c in df.columns}
    for k in aliases:
        x=k.lower().replace(' ','')
        if x in lookup:return lookup[x]
    return None

def population_summary(df):
    """Returns population by city/district only when raw data has explicit columns."""
    if df.empty:return pd.DataFrame(columns=['city','district','population','villages'])
    area=find_col(df,'區域別','site_id','行政區','區域別名稱')
    pop=find_col(df,'人口數','people_total','總人口數')
    if area is None or pop is None:raise ValueError('人口資料缺少「區域別」或「人口數」欄位')
    work=df[[area,pop]].copy();work['population']=pd.to_numeric(work[pop].astype(str).str.replace(',',''),errors='coerce')
    work['city']=work[area].astype(str).str.extract(r'(臺北市|台北市|新北市|桃園市|臺中市|台中市|臺南市|台南市|高雄市|基隆市|新竹市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義市|嘉義縣|屏東縣|宜蘭縣|花蓮縣|臺東縣|台東縣|澎湖縣|金門縣|連江縣)',expand=False).map(lambda s:clean_city(s) if isinstance(s,str) else s)
    work['district']=work[area].astype(str).str.extract(r'([\u4e00-\u9fff]{1,5}[區鄉鎮市])$',expand=False)
    return work.dropna(subset=['city','population']).groupby(['city','district'],dropna=False).agg(population=('population','sum'),villages=('population','size')).reset_index()

def metro_summary(df):
    if df.empty:return pd.DataFrame(columns=['station','daily_riders'])
    station=find_col(df,'捷運站別','站名','車站','station')
    count=find_col(df,'平均日運量','平均每日運量','運量','進站人數')
    if station is None or count is None:raise ValueError('捷運資料缺少「捷運站別」或「平均日運量」')
    w=df[[station,count]].copy();w['daily_riders']=pd.to_numeric(w[count].astype(str).str.replace(',',''),errors='coerce')
    return w.dropna(subset=['daily_riders']).groupby(station)['daily_riders'].mean().reset_index().rename(columns={station:'station'}).sort_values('daily_riders',ascending=False)

def industry_summary(df):
    if df.empty:return pd.DataFrame(columns=['city','restaurants','all_businesses'])
    city=find_col(df,'縣市別','縣市','縣市名稱')
    restaurants=find_col(df,'住宿及餐飲業家數','住宿餐飲業家數')
    total=find_col(df,'總計家數','總家數')
    if not all([city,restaurants,total]):raise ValueError('商業登記資料缺少縣市別、住宿及餐飲業家數或總計家數')
    w=df[[city,restaurants,total]].copy();w.columns=['city','restaurants','all_businesses']
    w['city']=w.city.map(clean_city)
    for k in ('restaurants','all_businesses'):w[k]=pd.to_numeric(w[k].astype(str).str.replace(',',''),errors='coerce')
    return w.dropna(subset=['restaurants']).groupby('city',as_index=False)[['restaurants','all_businesses']].sum()

def count_tax_zip_by_city(path, city, keyword=None):
    """Stream nationwide CSV rows from ZIP, avoiding an all-country DataFrame in RAM.

    Counts matching registration records only, NOT confirmed active shops.
    """
    path=Path(path)
    if not zipfile.is_zipfile(path):raise ValueError('稅籍檔不是 ZIP')
    total=0;found=False
    with zipfile.ZipFile(path) as z:
        members=[m for m in z.infolist() if m.filename.lower().endswith('.csv') and not m.is_dir()]
        if not members:raise ValueError('ZIP 內沒有 CSV；請檢查官方 ZIP 目前採用的格式')
        for item in members:
            if item.file_size>2*1024**3:raise ValueError('ZIP 內單一檔案過大')
            if item.compress_size and item.file_size / item.compress_size>500:raise ValueError('ZIP 壓縮率異常')
            with z.open(item) as f:
                for encoding in ['utf-8-sig','cp950']:
                    try:
                        f.seek(0)
                        chunks=pd.read_csv(f,encoding=encoding,chunksize=25000,dtype=str,on_bad_lines='skip')
                        for chunk in chunks:
                            addr=find_col(chunk,'營業地址','營業所在地址','地址')
                            code=find_col(chunk,'行業代號','行業代碼','行業名稱','營業項目')
                            if addr is None:raise ValueError('找不到營業地址欄位')
                            found=True
                            mask=chunk[addr].astype(str).str.contains(city,regex=False,na=False)
                            if keyword and code is not None:mask &= chunk[code].astype(str).str.contains(keyword,regex=False,na=False)
                            total+=int(mask.sum())
                        break
                    except UnicodeDecodeError:
                        if encoding=='cp950':raise
                        continue
    if not found:raise ValueError('ZIP 內沒有可解析的稅籍記錄')
    return total

def tax_competitors(df,city,keyword=None):
    """Counts registration records, not verified open stores nor radius-based competitors."""
    if df.empty:return None
    addr=find_col(df,'營業地址','營業所在地址','地址')
    code=find_col(df,'行業代號','行業代碼','營業項目','行業名稱','營業項目名稱')
    if addr is None:return None
    x=df[addr].astype(str).str.contains(city,regex=False,na=False)
    if keyword and code is not None:x &= df[code].astype(str).str.contains(keyword,regex=False,na=False)
    return int(x.sum())

def legal_checklist(shop,city):
    rows=[('商業或公司設立登記','依組織及營業型態確認登記義務','https://onestop.nat.gov.tw/'),('稅籍及稅務','確認稅籍登記、發票與報稅義務','https://www.etax.nat.gov.tw/'),('場地用途與消防','向所在地主管機關查核土地使用、建築與消防條件','https://www.gov.tw/'),('僱用與勞動條件','依實際僱用條件查核工時、薪資、保險與勞動規則','https://laws.mol.gov.tw/')]
    if shop in FOOD:rows += [('食品業者登錄','確認是否符合食品業者登錄適用對象','https://www.fda.gov.tw/'),('食品衛生／GHP','依店型與作業內容核對衛生與設備要求','https://www.fda.gov.tw/TC/siteContent.aspx?sid=3077')]
    return [{'item':a,'action':b,'source':c,'status':'待核實','scope':f'{shop}／{city}'} for a,b,c in rows]

def operations_plan(shop):
    tasks=['開店前確認設備安全、清潔與可使用狀態','現金、訂單與交班紀錄','員工工時、休息與教育訓練紀錄','建立異常事故及客訴通報流程']
    if shop in FOOD:tasks+=['確認食材來源與進貨紀錄','依食材特性管理溫度與保存期限','避免交叉污染並落實器具清潔','核對食品標示及過敏原相關義務']
    if shop=='服飾店':tasks+=['確認商品標示與來源','建立庫存盤點及退換貨規範']
    return tasks

def availability():
    result={}
    for key,v in SOURCES.items():
        path=RAW/v['file'];result[key]={**v,'present':path.exists(),'bytes':path.stat().st_size if path.exists() else 0}
    return result

def build_report(config,sim,stats,legal):
    lines=['# OpenShop AI｜創業可行性模擬報告','',f"店型：{config['shop']} ｜城市：{config['city']}",f"建模時間：{config.get('date','未指定')}",'','## 第一角色｜法遵與現場作業','此清單僅作為核對方向，**不代表主管機關核准或法律意見**。']
    for a in legal:lines.append(f"- [ ] {a['item']}：{a['action']}（{a['source']}）")
    lines+=['','## 第二角色｜市場與選址資料','以下只展示已匯入且可解析的官方公開資料；欠缺資料時不產生分數。']
    for k,v in stats.items():lines.append(f'- {k}：{v}')
    lines+=['','## 第三角色｜財務情境',f"- 每月營收：NT$ {sim['revenue']:,.0f}",f"- 每月成本：NT$ {sim['monthly_cost']:,.0f}",f"- 每月簡化損益：NT$ {sim['monthly_profit']:,.0f}",f"- 每日損益平衡訂單：{sim['breakeven_daily'] if sim['breakeven_daily'] is not None else '無法計算'}",'','## 稽核與限制','- 法規適用性仍需依營業地址、業態、規模及主管機關逐項確認。','- 行業登記家數不是實際同業營業數；捷運運量不是來客數。','- 內用、外帶、外送比例為使用者假設，非市場實測偏好。','- 財務數字為假設試算，非可驗證的營運預測。','',f"財務模型註記：{sim['notes']}"]
    return '\n'.join(lines)
