"""OpenShop LIFE PWA server. Run: python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502"""
from __future__ import annotations
import io, json, math, zipfile
from pathlib import Path
from typing import Any
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from scripts.studio_engine import (STORE_CATALOG, FOOD, LEGAL_LINKS, REQUIRED,
                                   parse_upload, rank_places, create_artifacts,
                                   play_one_day, daily_simulation, DECISIONS)

ROOT = Path(__file__).resolve().parent
WEB = ROOT / 'web'
app = FastAPI(title='OpenShop LIFE Studio PWA', version='3.0.0', docs_url='/api/docs')
app.mount('/assets', StaticFiles(directory=WEB), name='assets')

DEFAULT_CONFIG = {
    'shop':'手搖飲店', 'city':'桃園市', 'district':'中壢區',
    'floor_area_sqm': 66.1, 'budget':800000, 'price':65, 'variable':25,
    'daily':70, 'rent':38000, 'payroll':85000, 'fixed_other':18000,
    'days':26, 'delivery_share':.2, 'dinein_share':.3, 'commission':.3,
    'delivery_packaging':5, 'opening_target_date':'2027-03-01',
    'fitout':150000, 'equipment':120000, 'reserve':150000,
}

def validate_config(raw:dict[str,Any]) -> dict[str,Any]:
    if not isinstance(raw,dict):raise ValueError('設定必須是 JSON 物件')
    c={**DEFAULT_CONFIG,**raw}
    if c['shop'] not in STORE_CATALOG:raise ValueError('不支援的店鋪類型')
    if not isinstance(c['city'],str) or not c['city'].strip() or len(c['city'])>40:raise ValueError('縣市不可空白')
    if not isinstance(c['district'],str) or len(c['district'])>80:raise ValueError('行政區名稱不正確')
    numeric=['floor_area_sqm','budget','price','variable','daily','rent','payroll','fixed_other',
             'days','delivery_share','dinein_share','commission','delivery_packaging','fitout','equipment','reserve']
    for k in numeric:
        if isinstance(c[k],bool):raise ValueError(f'{k} 不可為布林值')
        try: c[k]=float(c[k])
        except (ValueError,TypeError):raise ValueError(f'{k} 必須是數字')
        if not math.isfinite(c[k]) or c[k]<0:raise ValueError(f'{k} 不可為負數或無限值')
    for k in ['delivery_share','dinein_share','commission']:
        if c[k]>1:raise ValueError(f'{k} 必須介於 0 和 1')
    if c['delivery_share']+c['dinein_share']>1+1e-9:raise ValueError('內用和外送占比不能超過100%')
    if not 1<=c['days']<=31:raise ValueError('每月營業天數必須介於1與31')
    if c['price']<=0 or c['daily']>100000 or c['budget']>1e10:raise ValueError('交易價格、訂單或預算超出允許範圍')
    return c

def jsonify_obj(o:Any):
    """Convert pandas/numpy scalar values in existing engine artifacts safely."""
    if isinstance(o,dict):return {str(k):jsonify_obj(v) for k,v in o.items()}
    if isinstance(o,(list,tuple)):return [jsonify_obj(v) for v in o]
    if hasattr(o,'item'):return jsonify_obj(o.item())
    if isinstance(o,float) and not math.isfinite(o):return None
    return o

class ConfigRequest(BaseModel):
    config: dict[str,Any]

class DayRequest(BaseModel):
    config: dict[str,Any]
    history: list[dict[str,Any]] = []
    choice: str = '一般營業'
    seed: int = 42

@app.get('/')
def home():return FileResponse(WEB/'index.html')

@app.get('/favicon.ico', include_in_schema=False)
def favicon():return FileResponse(WEB/'icons'/'icon-192.png',media_type='image/png')

@app.get('/manifest.webmanifest')
def manifest():return FileResponse(WEB/'manifest.webmanifest',media_type='application/manifest+json')

@app.get('/sw.js')
def service_worker():return FileResponse(WEB/'sw.js',media_type='application/javascript',headers={'Cache-Control':'no-store','Service-Worker-Allowed':'/'})

@app.get('/api/catalog')
def catalog():
    return {'shops':[{'name':name,'category':v[0],'icon':v[1],'price':v[2],'variable':v[3],'daily':v[4]} for name,v in STORE_CATALOG.items()],
            'decisions':DECISIONS,'links':LEGAL_LINKS,'defaults':DEFAULT_CONFIG,'required_columns':REQUIRED,
            'notice':'檔案範例為教學假設。PWA 介面與本地分析不等於 AI 模型自動觸發 SKILL.md。'}

@app.get('/api/sample')
def sample():
    p=ROOT/'examples'/'DEMO_商圈資料_情境假設_非官方.csv'
    return FileResponse(p,media_type='text/csv',filename='openshop_SAMPLE_ASSUMPTIONS.csv')

@app.post('/api/preview')
def preview(body:ConfigRequest):
    try:
        c=validate_config(body.config)
        market,legal,plan,audit,sim,rank=create_artifacts(c,None,None)
        return {'finance':jsonify_obj(sim),'legal':jsonify_obj(legal),'audit':jsonify_obj(audit),'verified':False,
                'notice':'情境試算，尚未上傳商圈資料及完成資料品質檢查'}
    except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))

@app.post('/api/analyze')
async def analyze(file:UploadFile=File(...), config:str=Form(...)):
    try:
        c=validate_config(json.loads(config))
        if not file.filename or not file.filename.lower().endswith(('.csv','.json')):
            raise ValueError('僅支援 .csv 或 .json')
        raw=await file.read(20*1024*1024+1)
        df,quality=parse_upload(raw,file.filename)
        market,legal,plan,audit,sim,rank=create_artifacts(c,df,quality)
        return JSONResponse(jsonify_obj({'market':market,'legal':legal,'plan':plan,'audit':audit,'finance':sim,
            'ranked':rank.to_dict('records'),'quality':quality,'source_status':'使用者提供，尚未獨立證明為官方資料',
            'notes':['排名為情境相對分數，不是獲利機率','人工法規確認仍屬必要','此為 Python 三角色分析，不等於 AI Skill 自動載入']}))
    except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:raise HTTPException(422,str(e))

@app.post('/api/day')
def play(body:DayRequest):
    try:
        c=validate_config(body.config)
        if len(body.history)>120:raise ValueError('互動遊戲上限120天')
        if body.choice not in DECISIONS:raise ValueError('未知的老闆決策')
        # Do not trust client-supplied history for arbitrary server operations.
        history=[]
        for item in body.history:
            action=item.get('decision')
            if action not in DECISIONS:raise ValueError('歷史決策格式錯誤')
            history=play_one_day(c,history,action,body.seed)
        history=play_one_day(c,history,body.choice,body.seed)
        return {'history':jsonify_obj(history),'last':jsonify_obj(history[-1]),'simulated':True}
    except (ValueError,TypeError,KeyError) as e:raise HTTPException(422,str(e))

@app.post('/api/days')
def simulate_days(body:ConfigRequest, duration:int=30,seed:int=42):
    try:
        c=validate_config(body.config)
        if duration<1 or duration>120:raise ValueError('模擬天數必須介於1與120')
        df=daily_simulation(c,seed,duration)
        return {'days':jsonify_obj(df.to_dict('records')),'simulated':True}
    except (ValueError,TypeError,KeyError) as e:raise HTTPException(422,str(e))

@app.get('/api/health')
def health():return {'ok':True,'version':'3.0','engine':'scripts.studio_engine'}
