"""Interactive file-driven opening simulator. Distinguishes evidence from assumptions."""
from __future__ import annotations
import json,io,math,hashlib,random
from datetime import date,timedelta
from pathlib import Path
import pandas as pd
from scripts.logic import money_sim,legal_checklist,operations_plan

STORE_CATALOG={
'手搖飲店':('餐飲','🧋',65,25,70), '咖啡廳':('餐飲','☕',145,52,45), '早餐店':('餐飲','🥪',90,36,85),
'甜點店':('餐飲','🍰',180,76,38),'便當店':('餐飲','🍱',125,69,75),'拉麵店':('餐飲','🍜',240,110,38),
'火鍋店':('餐飲','🍲',420,205,30),'麵包店':('餐飲','🥐',120,54,65),'冰品店':('餐飲','🍧',110,42,55),
'服飾店':('零售','👗',680,390,12),'花店':('零售','💐',850,450,10),'文具店':('零售','✏️',190,105,36),
'書店':('零售','📚',420,280,14),'寵物用品店':('零售','🐾',510,320,18),'手機配件店':('零售','📱',360,170,22),
'美甲工作室':('服務','💅',1100,230,6),'美髮沙龍':('服務','✂️',850,200,12),'自助洗衣店':('服務','🫧',120,30,40),
'健身工作室':('服務','🏋️',500,130,15),'花藝教室':('服務','🌸',950,360,8)
}
FOOD={'手搖飲店','咖啡廳','早餐店','甜點店','便當店','拉麵店','火鍋店','麵包店','冰品店'}
LEGAL_LINKS={
'商業登記':'https://onestop.nat.gov.tw/',
'稅籍登記':'https://www.etax.nat.gov.tw/',
'建管土地使用消防':'https://www.gov.tw/',
'工時薪資與保險':'https://laws.mol.gov.tw/',
'食品業者登錄':'https://www.fda.gov.tw/TC/siteList.aspx?sid=12325',
'食品衛生GHP':'https://www.fda.gov.tw/TC/siteContent.aspx?sid=3077',
'特殊行業規範':'https://www.gov.tw/'
}
REQUIRED=['district','population','competitors','footfall','rent']
ALIAS={'district':['district','行政區','商圈','候選地點','area'], 'population':['population','人口','人口數'],
'competitors':['competitors','同業數','競爭店家數'], 'footfall':['footfall','人流指標','交通量','旅運量'],
'rent':['rent','租金','月租金'], 'data_source':['data_source','資料來源','source']}

def parse_upload(data:bytes, filename:str):
    if len(data)>20*1024*1024:raise ValueError('上傳檔案不可大於20MB')
    if filename.lower().endswith('.json'):
        obj=json.loads(data.decode('utf-8-sig'))
        if isinstance(obj,dict):obj=obj.get('records',obj.get('data',obj))
        if not isinstance(obj,list):raise ValueError('JSON 須是紀錄陣列，或含 records/data 陣列')
        df=pd.DataFrame(obj)
    elif filename.lower().endswith('.csv'):
        df=None
        for enc in ['utf-8-sig','cp950','big5']:
            try: df=pd.read_csv(io.BytesIO(data),encoding=enc);break
            except UnicodeDecodeError:continue
        if df is None:raise ValueError('CSV 編碼無法辨識')
    else:raise ValueError('請使用 CSV 或 JSON')
    if len(df)>10000:raise ValueError('候選商圈資料最多 10000 列')
    mapping={}
    for target,names in ALIAS.items():
        col=next((x for x in df.columns if str(x).strip().lower() in [a.lower() for a in names]),None)
        if col is not None:mapping[col]=target
    df=df.rename(columns=mapping)
    missing=[c for c in REQUIRED if c not in df.columns]
    if missing:raise ValueError('缺少必要欄位：'+', '.join(missing))
    warnings=[]
    initial=len(df)
    df=df.drop_duplicates(subset=['district']).copy()
    if len(df)<initial:warnings.append(f'已移除 {initial-len(df)} 個重複候選地點；保留第一列')
    for c in REQUIRED[1:]:
        df[c]=pd.to_numeric(df[c].astype(str).str.replace(',','',regex=False),errors='coerce')
    bad=df[REQUIRED].isna().any(axis=1)|(df[REQUIRED[1:]]<0).any(axis=1)
    if bad.any():raise ValueError(f'共有 {int(bad.sum())} 列含缺值／負數／非數字，請修正來源資料後重新匯入；不會自行補假值')
    if df.empty:raise ValueError('沒有可用的候選商圈資料')
    if not df['district'].astype(str).str.strip().all():raise ValueError('行政區不可空白')
    df['district']=df['district'].astype(str)
    if 'data_source' not in df.columns:
        df['data_source']='使用者上傳；尚未驗證來源'
        warnings.append('未提供 data_source，商圈數據視為使用者資料而非官方統計')
    warnings += ['人口、競業與人流的時間範圍／空間範圍須一致；人流不等於來客數']
    return df.reset_index(drop=True), {'rows':len(df),'warnings':warnings,'sha256':hashlib.sha256(data).hexdigest(),'filename':filename}

def rank_places(df:pd.DataFrame, weights=(0.40,0.35,0.25)):
    """User-supplied area attributes; relative heuristic, not empirical outcome probability."""
    x=df.copy()
    if x.empty:return x
    def norm(c,reverse=False):
        col=x[c].astype(float)
        if col.max()==col.min():return pd.Series(.5,index=x.index)
        y=(col-col.min())/(col.max()-col.min())
        return 1-y if reverse else y
    x['人口指標']=norm('population');x['交通指標']=norm('footfall')
    x['競爭指標']=norm('competitors',True);x['租金指標']=norm('rent',True)
    x['情境分數']=(x['人口指標']*weights[0]+x['交通指標']*weights[1]+(x['競爭指標']*.6+x['租金指標']*.4)*weights[2])*100
    return x.sort_values(['情境分數','district'],ascending=[False,True]).reset_index(drop=True)

def daily_simulation(config, seed=42, duration=30, events=True):
    """Deterministic Monte Carlo storytelling; all observations are synthetic."""
    if duration<1 or duration>365:raise ValueError('模擬天數須介於 1–365')
    base=float(config['daily']);price=float(config['price']); variable=float(config['variable'])
    delivery=float(config['delivery_share']);commission=float(config['commission']); pack=float(config['delivery_packaging'])
    fixed=(float(config['rent'])+float(config['payroll'])+float(config['fixed_other']))/max(1,int(config['days']))
    rnd=random.Random(seed); cash=float(config['budget']); rows=[]
    start=date.fromisoformat(str(config.get('start_date','2026-12-01')))
    event_options=[('平日正常',1),('在地活動',1.35),('雨天來客降低',.77),('網路好評',1.18),('設備維修',.6),('原料缺貨',.68)]
    for d in range(duration):
        day=start+timedelta(days=d)
        if events:
            event,rate=rnd.choices(event_options,weights=[70,7,10,6,3,4])[0]
        else:event,rate='一般營業',1
        weekend=1.15 if day.weekday()>=5 else 1
        orders=max(0,round(base*rate*weekend*rnd.uniform(.91,1.09)))
        revenue=orders*price
        margin=orders*(price-variable-delivery*(price*commission+pack))
        profit=margin-fixed;cash+=profit
        rows.append({'date':str(day),'day':d+1,'event':event,'orders':orders,'revenue':round(revenue),
                     'profit':round(profit,2),'cash':round(cash,2),'channel_dinein':round(orders*float(config['dinein_share'])),
                     'channel_delivery':round(orders*delivery),'simulated':True})
    return pd.DataFrame(rows)

def legal_for(shop,city):
    checklist=legal_checklist('餐館' if shop in FOOD and shop not in ['手搖飲店','咖啡廳','早餐店','甜點店'] else shop,city)
    if shop in FOOD and not any(x['item']=='食品業者登錄' for x in checklist):
        for key,label in [('食品業者登錄','食品業者登錄'),('食品衛生GHP','食品衛生／GHP')]:
            checklist.append({'item':label,'action':'確認適用範圍、作業場域與衛生規範','source':LEGAL_LINKS[key],'status':'待核實','scope':f'{shop}／{city}'})
    if STORE_CATALOG[shop][0]=='服務':
        checklist.append({'item':'專業資格／特殊行業許可','action':'依服務項目向當地主管機關逐項核實','source':LEGAL_LINKS['特殊行業規範'],'status':'待核實','scope':f'{shop}／{city}'})
    return checklist

def create_artifacts(config,df,quality):
    """Required teacher order: market -> legal -> procedure/audit."""
    ranked=rank_places(df) if df is not None else pd.DataFrame()
    sim=money_sim(price=config['price'],variable=config['variable'],daily=config['daily'],rent=config['rent'],payroll=config['payroll'],
                  fixed_other=config['fixed_other'],days=config['days'],initial=config['budget'],
                  dinein_share=config['dinein_share'],delivery_share=config['delivery_share'],
                  commission=config['commission'],delivery_packaging=config['delivery_packaging'])
    ctx={'business_type':config['shop'],'location':config['city'],'district':config.get('district','未指定'),
         'floor_area_sqm':config.get('floor_area_sqm',0),'budget_twd':config['budget'],
         'opening_target_date':config.get('opening_target_date'),'assumptions':['成本與來客量由使用者輸入','地方建管與實際租址未審查']}
    market={'agent':'01_market_analyst','project_context':ctx,'quality':quality or {'rows':0,'warnings':['未提供商圈數據，停止市場排序']},
            'ranked_areas':ranked[['district','情境分數','data_source']].round(2).to_dict('records') if not ranked.empty else [],
            'forecast_monthly_revenue_assumption':sim['revenue'],'score_is_relative_heuristic':True,
            'open_questions':['需核對人口和店家數之統計區域／期間','租金須取得真實物件報價'],
            'status':'complete' if not ranked.empty else 'partial'}
    legal=legal_for(config['shop'],config['city'])
    legal_doc={'agent':'02_legal_advisor','upstream':'01_market_report.json','items':[],
               'needs_authority_confirmation':True,'status':'partial'}
    high={'場地用途與消防','專業資格／特殊行業許可','食品業者登錄'}
    for item in legal:
        n=item['item'];legal_doc['items'].append({**item,'risk':'high' if n in high else 'medium',
            'authority':'所在地主管機關／相關中央主管機關','action_required':item['action'],
            'needs_authority_confirmation':True,'source_date_missing':True})
    steps=[('1','確認業態、地址與場地用途','地方主管機關',7),('2','商業或公司設立及稅籍登記','經濟部／財政部',10),
           ('3','食品或特殊業別登錄與證照確認','相關主管機關',10),('4','消防建管、裝修與設備確認','地方建管／消防機關',20),
           ('5','人員、勞動條件與SOP訓練','勞動相關主管機關',7),('6','核對預算、開幕前稽核','創業者／主管機關',5)]
    needs=sum([config.get('deposit',config['rent']*2),config.get('fitout',150000),config.get('equipment',120000),config.get('reserve',150000)])
    issues=[]
    if needs>config['budget']:issues.append('初期裝潢、設備、押金與預備金假設合計高於可用預算')
    if all(x.get('source') and x.get('authority') and x.get('action_required') for x in legal_doc['items'] if x['risk']=='high') is False:issues.append('高風險法規缺少機關／動作／來源')
    issues+=['尚未完成實際地址建管與地方主管機關個案確認']
    if ranked.empty:issues.append('尚未提供可評比的商圈資料')
    status='blocked' if needs>config['budget'] else 'pass_with_conditions'
    plan=['# 03｜開店流程與跨角色審查','',f"店型：{config['shop']}；地點：{config['city']}",
         '','## Agent 1 市場資料結論',f"候選地點：{len(ranked)}；資料狀態：{market['status']}",
         '','## Agent 2 法規待辦', *[f"- [ ] {x['item']}｜{x['authority']}｜{x['action_required']}｜{x['source']}" for x in legal_doc['items']],
         '','## Agent 3 排程（工作天為示例假設，可並行項目未扣除）',
         '|階段|工作|主管機關／窗口|假設工作天|','|---|---|---|---:|',
         *[f'|{n}|{task}|{org}|{days}|' for n,task,org,days in steps],
         '','## 開辦資金假設',f'- 初期項目合計：NT$ {needs:,.0f}（押金、裝潢、設備、預備金）',
         f"- 可用預算：NT$ {config['budget']:,.0f}",f"- 月度情境損益：NT$ {sim['monthly_profit']:,.0f}",
         '','## 稽核及待補事項', *[f'- {q}' for q in issues],
         '','**本系統未完成實際法規許可審核；所有市場排名及日營運推演均為示範性決策工具。**']
    audit={'status':status,'market_rows':len(ranked),'legal_items':len(legal_doc['items']),
           'high_risks_linked':all(x.get('source') and x.get('authority') and x.get('action_required') for x in legal_doc['items'] if x['risk']=='high'),
           'budget_coverage_check':needs<=config['budget'],'estimated_upfront_cost':needs,
           'financial_formula_check':abs(sim['revenue']-sim['monthly_cost']-sim['monthly_profit'])<0.01,
           'needs_authority_confirmation':True,'issues':issues,'actual_skill_auto_trigger_tested':False}
    return market,legal_doc,'\n'.join(plan),audit,sim,ranked

def save_artifacts(folder,artifacts):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    market,legal,plan,audit,sim,ranked=artifacts
    (folder/'01_market_report.json').write_text(json.dumps(market,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'02_legal_checklist.json').write_text(json.dumps(legal,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'03_store_opening_plan.md').write_text(plan,encoding='utf-8')
    (folder/'04_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'05_finance.json').write_text(json.dumps(sim,ensure_ascii=False,indent=2),encoding='utf-8')
    if not ranked.empty:ranked.to_csv(folder/'06_location_ranking.csv',index=False,encoding='utf-8-sig')

DECISIONS={
    '一般營業':{'orders_factor':1.0,'extra_cost':0,'description':'維持今日原定營運方案'},
    '社群廣告':{'orders_factor':1.16,'extra_cost':1200,'description':'投放 NT$1,200 行銷費；模擬增加訂單 16%'},
    '增加尖峰人力':{'orders_factor':1.10,'extra_cost':850,'description':'額外花 NT$850；模擬提高接單能力 10%'},
    '推出限時折扣':{'orders_factor':1.23,'extra_cost':0,'price_factor':0.90,'description':'模擬提升訂單 23%，但客單價降低 10%'},
    '控制庫存耗損':{'orders_factor':0.96,'extra_cost':0,'variable_factor':0.94,'description':'模擬訂單略降 4%，每筆直接成本降低 6%'}
}

def play_one_day(config,history=None,choice='一般營業',seed=42):
    """User decisions drive a deterministic, clearly synthetic turn-based scenario."""
    if choice not in DECISIONS:raise ValueError('未知決策')
    history=list(history or [])
    idx=len(history)
    if idx>=365:raise ValueError('逐日決策最多 365 天')
    rnd=random.Random(seed+idx*7919)
    event,impact=rnd.choices([('一般日',1),('地方活動',1.30),('下雨',.80),('設備故障',.55),('顧客推薦',1.16)],weights=[65,10,12,5,8])[0]
    dec=DECISIONS[choice]
    price=float(config['price'])*dec.get('price_factor',1)
    variable=float(config['variable'])*dec.get('variable_factor',1)
    orders=round(float(config['daily'])*impact*dec['orders_factor']*rnd.uniform(.92,1.08))
    fixed=(float(config['rent'])+float(config['payroll'])+float(config['fixed_other']))/max(1,int(config['days']))
    fee=orders*float(config['delivery_share'])*(price*float(config['commission'])+float(config['delivery_packaging']))
    profit=orders*(price-variable)-fixed-fee-dec['extra_cost']
    past_cash=history[-1]['cash'] if history else float(config['budget'])
    row={'day':idx+1,'decision':choice,'event':event,'orders':orders,
         'revenue':round(orders*price,2),'profit':round(profit,2),'cash':round(past_cash+profit,2),
         'is_simulation':True,'day_description':dec['description']}
    return history+[row]
