"""OpenShop V5: deterministic calculation tools, not AI agents."""
import csv, json, math, hashlib, random, io
from pathlib import Path
from datetime import datetime, timezone

FIELDS=('district','population','competitors','footfall','rent')
ALIASES={'district':('行政區','商圈','候選地點','area'),'population':('人口','人口數'),'competitors':('同業數','競爭店家數'),'footfall':('人流指標','交通量','旅運量'),'rent':('租金','月租金')}
CATALOG={'手搖飲店':(65,25,70),'咖啡廳':(145,52,45),'早餐店':(90,36,85),'甜點店':(180,76,38),'便當店':(125,69,75),'拉麵店':(240,110,38),'火鍋店':(420,205,30),'麵包店':(120,54,65),'冰品店':(110,42,55),'服飾店':(680,390,12),'花店':(850,450,10),'文具店':(190,105,36),'書店':(420,280,14),'寵物用品店':(510,320,18),'手機配件店':(360,170,22),'美甲工作室':(1100,230,6),'美髮沙龍':(850,200,12),'自助洗衣店':(120,30,40),'健身工作室':(500,130,15),'花藝教室':(950,360,8)}
FOOD=set(list(CATALOG)[:9]); SERVICE=set(list(CATALOG)[15:])
DEFAULT_WEIGHTS={'population':40,'footfall':35,'competitors':15,'rent':10}

# Staffing inputs are optional.  ``staff_count`` and ``payroll`` remain
# backward-compatible top-level fields, while the additional fields let an
# AI or user describe a mixed team without forcing every worker to be full
# time.  Payroll is always a monthly TWD amount.
STAFFING_FIELDS=(
    'staff_count','full_time_count','part_time_count','full_time_salary',
    'part_time_hourly_wage','part_time_hours_per_month','employer_burden_rate',
)

def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write_json(p,obj): Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def num(v,name):
    if isinstance(v,bool) or v is None: raise ValueError(f'{name}: 非有效數值')
    try: x=float(str(v).replace(',',''))
    except (ValueError,TypeError): raise ValueError(f'{name}: 非有效數值') from None
    if not math.isfinite(x) or x<0: raise ValueError(f'{name}: 必須為非負有限數值')
    return x

def table(p):
    p=Path(p)
    if p.stat().st_size>20*1024**2: raise ValueError('檔案超過 20MB，請先依區域取樣')
    b=p.read_bytes()
    if p.suffix.lower()=='.json':
        rows=json.loads(b.decode('utf-8-sig'))
        if isinstance(rows,dict): rows=rows.get('records',rows.get('data'))
    elif p.suffix.lower()=='.csv':
        for enc in ('utf-8-sig','cp950','big5'):
            try: s=b.decode(enc);break
            except UnicodeDecodeError: continue
        else: raise ValueError('無法辨識 CSV 編碼')
        reader=csv.DictReader(io.StringIO(s)); names=reader.fieldnames or []
        if len(names)!=len(set(names)): raise ValueError('重複欄名')
        rows=list(reader)
    else: raise ValueError('僅接受 CSV/JSON')
    if not isinstance(rows,list) or not rows or len(rows)>10000 or not all(isinstance(r,dict) for r in rows): raise ValueError('資料須為 1–10000 筆紀錄')
    return rows

def clean(p, source_type='user', period=None, geography=None):
    if source_type not in ('user','synthetic','derived'): raise ValueError('原始官方檔須先 ETL；不得自行標為已驗證官方')
    rows=table(p); result=[]; seen={}; duplicates=0
    for i,row in enumerate(rows,1):
        row={str(k).strip():v for k,v in row.items() if k is not None}
        out={}
        for k in FIELDS:
            keys=[x for x in (k,*ALIASES.get(k,())) if x in row]
            if len(keys)!=1: raise ValueError(f'第 {i} 筆：缺少或重複欄位 {k}')
            v=row[keys[0]]
            if k=='district':
                if not isinstance(v,str) or not v.strip(): raise ValueError(f'第 {i} 筆：地區空白')
                out[k]=v.strip()
            else: out[k]=num(v,f'第 {i} 筆 {k}')
        for k in ('period','geography','data_source'):
            out[k]=row.get(k) or (period if k=='period' else geography if k=='geography' else source_type)
        key=out['district']
        if key in seen:
            if out!=seen[key]: raise ValueError(f'{key}: 重複地點數值矛盾')
            duplicates+=1;continue
        seen[key]=out;result.append(out)
    for k in ('period','geography'):
        vals={r[k] for r in result if r[k]}
        if len(vals)>1 or (vals and any(not r[k] for r in result)): raise ValueError(f'{k} 不一致或部分缺漏，停止排名')
    return result,{'rows_original':len(rows),'rows':len(result),'duplicates_removed':duplicates,'sha256':sha(p),'source_type':source_type,'period':period,'geography':geography,'warnings':['人口與交通是代理指標，非實際來客數']+(['期間或地理粒度未確認；僅條件式比較'] if not all(result[0][k] for k in ('period','geography')) else [])}

def weights(w):
    if set(w)!=set(DEFAULT_WEIGHTS): raise ValueError('必須提供四項權重')
    w={k:num(v,k) for k,v in w.items()}
    if abs(sum(w.values())-100)>1e-7: raise ValueError('權重總和須為 100')
    return w

def rank(rows,w):
    w=weights(w); out=[]
    if len(rows)<2: return []
    for row in rows:
        scores={}
        for k in w:
            lo=min(r[k] for r in rows);hi=max(r[k] for r in rows)
            x=.5 if hi==lo else (row[k]-lo)/(hi-lo)
            if k in ('competitors','rent'): x=1-x
            scores[k]=x*w[k]
        out.append({'district':row['district'],'score':sum(scores.values()),'contributions':scores,**{k:row[k] for k in w}})
    return sorted(out,key=lambda r:(-r['score'],r['district']))

def config(raw):
    c=dict(raw); assumptions=list(c.get('assumptions',[]))
    for k in ('business_type','location'):
        if not isinstance(c.get(k),str) or not c[k].strip(): raise ValueError(f'缺少 {k}')
    defaults=dict(zip(('price','variable','daily'),CATALOG.get(c['business_type'],(100,45,40))))
    defaults.update(
        days=26, fixed_other=18000, dinein_share=.3, delivery_share=.2,
        commission=.3, delivery_packaging=5, fitout=150000, equipment=120000,
        reserve=150000, registration=10000, safety_equipment=20000,
        initial_stock=20000, seed=42, simulation_days=7,
        full_time_salary=30000, part_time_hourly_wage=200,
        part_time_hours_per_month=80, employer_burden_rate=.15,
    )
    explicit_staffing=any(c.get(k) is not None for k in ('staff_count','full_time_count','part_time_count'))
    explicit_payroll=c.get('payroll') is not None
    if c.get('allow_assumptions') is True:
        for k,v in defaults.items():
            if c.get(k) is None: c[k]=v;assumptions.append(f'{k}={v}（教學假設）')
        # Preserve the historical demo result only when the user supplied no
        # staffing information at all.  Once staff_count is supplied, payroll
        # is resolved from staffing inputs instead of silently staying at 85k.
        if not explicit_staffing and not explicit_payroll:
            c['staff_count']=2
            c['payroll']=85000
            c['staffing_source']='legacy_teaching_default'
            c['payroll_source']='legacy_teaching_default'
            assumptions += [
                'staff_count=2（舊版教學假設；需補充全職／兼職組成）',
                'payroll=85000（舊版教學假設；需確認是否含雇主負擔）',
            ]
    for k in ('budget_twd','floor_area_sqm','price','variable','daily','rent','payroll','fixed_other','days','dinein_share','delivery_share','commission','delivery_packaging','fitout','equipment','reserve','registration','safety_equipment','initial_stock','deposit',*STAFFING_FIELDS,'seed','simulation_days'):
        if c.get(k) is not None: c[k]=num(c[k],k)
    for k in ('days','staff_count','full_time_count','part_time_count','seed','simulation_days'):
        if c.get(k) is not None and c[k]!=int(c[k]): raise ValueError(f'{k} 必須為整數')
        if c.get(k) is not None: c[k]=int(c[k])
    if c.get('days') is not None and not 1<=c['days']<=31: raise ValueError('days 須為 1–31')
    if c.get('price')==0: raise ValueError('price 必須大於 0')
    if c.get('floor_area_sqm')==0: raise ValueError('坪數須大於 0')
    for k in ('staff_count','full_time_count','part_time_count'):
        if c.get(k) is not None and c[k] < 0: raise ValueError(f'{k} 不得為負數')
    if c.get('staff_count')==0: raise ValueError('staff_count 必須大於 0')
    for k in ('dinein_share','delivery_share','commission'):
        if c.get(k) is not None and c[k]>1: raise ValueError(f'{k} 須為 0–1')
    if all(c.get(k) is not None for k in ('dinein_share','delivery_share')) and c['dinein_share']+c['delivery_share']>1: raise ValueError('通路比例超過 100%')
    if c.get('simulation_days') is not None and not 1<=c['simulation_days']<=365: raise ValueError('模擬天數 1–365')
    c['assumptions']=assumptions;c['weights']=weights(c.get('weights',DEFAULT_WEIGHTS))
    return c

FIN=('budget_twd','price','variable','daily','rent','payroll','fixed_other','days','dinein_share','delivery_share','commission','delivery_packaging','fitout','equipment','reserve','registration','safety_equipment','initial_stock','deposit')

def staffing(c):
    """Resolve payroll without treating an unspecified team as all full-time.

    Explicit payroll is never overwritten.  If only staff_count is known, a
    mixed teaching model is used and a sensitivity range is returned.  The
    result is intentionally descriptive so an AI role can explain or replace
    it in a new run.
    """
    staff_count=c.get('staff_count')
    ft=c.get('full_time_count')
    pt=c.get('part_time_count')
    ft_salary=c.get('full_time_salary',30000)
    pt_wage=c.get('part_time_hourly_wage',200)
    pt_hours=c.get('part_time_hours_per_month',80)
    burden=c.get('employer_burden_rate',.15)
    warnings=[]; hard_issues=[]; source=c.get('payroll_source')
    if staff_count is None and ft is not None and pt is not None:
        staff_count=ft+pt
    if ft is not None and pt is not None and staff_count is not None and ft+pt != staff_count:
        hard_issues.append('全職與兼職人數合計不等於 staff_count')
    if staff_count is not None and staff_count < 1:
        hard_issues.append('staff_count 必須大於 0')
    explicit_payroll=c.get('payroll') is not None
    if explicit_payroll:
        payroll=float(c['payroll']); source=source or 'user_input'
        if staff_count:
            per_person=payroll/staff_count
            warnings.append('人事總成本由使用者提供；需確認是否包含雇主負擔、加班、獎金及福利')
        else: per_person=None
        if ft is not None and pt is not None:
            modeled=(ft*ft_salary + pt*pt_wage*pt_hours)*(1+burden)
            if modeled and abs(payroll-modeled)/modeled > .2:
                warnings.append('使用者人事總成本與全職／兼職參數估算差異超過 20%，需確認口徑')
        base=payroll
    elif staff_count:
        if ft is None and pt is None:
            # Mixed default: one lead full-time and the remainder part-time.
            ft=1 if staff_count == 1 else staff_count-1
            pt=staff_count-ft
            warnings.append('未提供全職／兼職組成，採混合教學假設；不得視為實際排班或法規結論')
            source='estimated_mixed_teaching_default'
        elif ft is None: ft=staff_count-pt
        elif pt is None: pt=staff_count-ft
        if ft < 0 or pt < 0 or ft+pt != staff_count:
            hard_issues.append('全職／兼職人數無法與 staff_count 對齊')
        base=(ft*ft_salary + pt*pt_wage*pt_hours)*(1+burden)
        warnings.append('人事成本為估算值；需以實際薪資、工時、保險與雇主負擔重算')
    else:
        base=None; source='insufficient_staffing_data'; warnings.append('缺少 staff_count 或人事成本，無法可靠估算')
    consistency='warning' if warnings or hard_issues else 'ok'
    sensitivity=[]
    if staff_count:
        sensitivity=[
            {'scenario':'全兼職參考','payroll':round(staff_count*pt_wage*pt_hours*(1+burden),2),'assumption':'所有人以兼職時數估算；只是參考情境，實際可能更低或更高'},
            {'scenario':'混合基準','payroll':round(base,2) if base is not None else None,'assumption':'依目前全職／兼職組成或混合教學假設'},
            {'scenario':'全職參考','payroll':round(staff_count*ft_salary*(1+burden),2),'assumption':'所有人以全職月薪估算；只是參考情境，實際可能更低或更高'},
        ]
    return {
        'staff_count':staff_count,'full_time_count':ft,'part_time_count':pt,
        'full_time_salary':ft_salary,'part_time_hourly_wage':pt_wage,
        'part_time_hours_per_month':pt_hours,'employer_burden_rate':burden,
        'payroll':round(base,2) if base is not None else None,'payroll_source':source,
        'consistency':consistency if base is not None else 'insufficient_data',
        'warnings':warnings,'hard_issues':hard_issues,'sensitivity':sensitivity,
    }

def finance(c):
    effective=dict(c); staff=staffing(effective)
    if staff['payroll'] is not None: effective['payroll']=staff['payroll']
    if staff['full_time_count'] is not None: effective['full_time_count']=staff['full_time_count']
    if staff['part_time_count'] is not None: effective['part_time_count']=staff['part_time_count']
    missing=[k for k in FIN if effective.get(k) is None]
    if missing: return {'missing':missing,'scenarios':[],'staffing':staff,'effective_config':effective}
    c=effective; fixed=c['rent']+c['payroll']+c['fixed_other']; p=c['price'];v=c['variable'];s=c['delivery_share'];r=c['commission'];pack=c['delivery_packaging'];d=c['days']
    contribution=p-v-s*(p*r+pack)
    initial=sum(c[k] for k in ('fitout','equipment','registration','safety_equipment','initial_stock','deposit'))
    cash=c['budget_twd']-initial;gap=max(0,c['reserve']-cash)
    scenarios=[]
    for label,factor in [('保守',.7),('一般',1),('樂觀',1.3)]:
        q=round(c['daily']*factor);rev=p*q*d;cost=(v+s*(p*r+pack))*q*d+fixed;profit=rev-cost
        scenarios.append({'scenario':label,'daily':q,'revenue':round(rev,2),'cost':round(cost,2),'profit':round(profit,2),'runway_months':round(max(0,cash)/(-profit),2) if profit<0 else None,'payback_months':round(initial/profit,2) if profit>0 else None})
    return {'inputs':{k:c[k] for k in FIN},'staffing':staff,'initial_spend':initial,'cash_after_setup':cash,'reserve_target':c['reserve'],'budget_gap':gap,'contribution':contribution,'fixed_cost':fixed,'breakeven_daily':math.ceil(fixed/(contribution*d)) if contribution>0 else None,'shares':{'dinein':c['dinein_share'],'takeaway':1-c['dinein_share']-s,'delivery':s},'scenarios':scenarios,'limitations':['交易量三情境為假設，非預測','未計稅、折舊、利息及業主薪資（除非已列入成本）','預備金為保留現金，非重複支出'],'effective_config':c}

LEGAL=[('商業或公司設立登記','https://onestop.nat.gov.tw/','所在地商業登記主管機關','確認組織型態及登記義務','medium'),('稅籍及稅務','https://www.etax.nat.gov.tw/','所在地國稅局','確認稅籍、發票及申報','medium'),('土地使用與建管消防','https://www.gov.tw/','所在地都發／建管／消防機關','依地址、用途、面積查核','high'),('僱用與勞動條件','https://laws.mol.gov.tw/','所在地勞工主管機關','確認工時、薪資、保險','medium')]
def legal(c):
    rows=list(LEGAL)
    if c['business_type'] in FOOD or c.get('food_business') is True: rows += [('食品業者登錄','https://www.fda.gov.tw/','所在地衛生局','確認登錄適用對象','high'),('食品衛生／GHP','https://www.fda.gov.tw/TC/siteContent.aspx?sid=3077','所在地衛生局','確認場域、設備及衛生作業','medium')]
    if c['business_type'] in SERVICE or c['business_type'] not in CATALOG: rows += [('特殊業別適用性','https://www.gov.tw/','所在地業務主管機關','確認資格與特殊許可','high')]
    return [{'item':a,'source':b,'source_date':None,'source_date_missing':True,'checked_at':None,'risk':e,'authority':f"{c['location']}／{d}",'action_required':f,'documents':None,'prerequisites':None,'estimated_workdays':None,'needs_authority_confirmation':True,'verification':'reference_only_not_live_checked','possible_cost':None} for a,b,d,f,e in rows]

def simulate(c,f):
    if not f['scenarios'] or c.get('simulation_days') is None or c.get('seed') is None: return []
    rnd=random.Random(c['seed']);cash=f['cash_after_setup'];out=[]
    for day in range(1,c['simulation_days']+1):
        event,factor=rnd.choice([('一般營業',1)]*7+[('地方活動',1.35),('雨天',.77),('設備維修',.6)])
        q=round(c['daily']*factor*rnd.uniform(.91,1.09));profit=q*f['contribution']-f['fixed_cost']/c['days'];cash+=profit
        out.append({'day':day,'event':event,'orders':q,'revenue':round(q*c['price'],2),'profit':round(profit,2),'cash':round(cash,2),'simulated':True})
    return out

def csv_out(p,rows):
    if not rows:return
    with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
