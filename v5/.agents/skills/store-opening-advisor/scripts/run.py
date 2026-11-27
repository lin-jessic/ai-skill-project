"""Stage-by-stage CLI for Codex. Python runs are calculation evidence, not trigger evidence."""
import argparse, json, sys, shutil, uuid, math
from pathlib import Path
from engine import *
ROOT=Path(__file__).resolve().parents[4]
NAMES=['01_market_report.json','02_legal_checklist.json','03_financial_report.json','04_business_plan.json','05_audit_report.json']
AGENT_NOTES=[f'agent_notes_{i:02}.md' for i in range(1,6)]
NOTE_REQUIRED_MARKERS=('實際輸入','上游','工具','分析','假設','交接')

def log(folder,event,**kw):
    p=folder/'execution_log.json'; records=read_json(p) if p.exists() else []
    records.append({'timestamp':now(),'event':event,**kw});write_json(p,records)

def note_status(folder):
    """Validate AI-authored notes without generating or filling them."""
    present=[];missing=[];empty=[];invalid=[];details=[]
    for name in AGENT_NOTES:
        p=folder/name
        if not p.exists(): missing.append(name)
        else:
            content=p.read_text(encoding='utf-8').strip()
            if not content: empty.append(name)
            else:
                absent=[marker for marker in NOTE_REQUIRED_MARKERS if marker not in content]
                if absent: invalid.append({'file':name,'missing_markers':absent})
                else: present.append(name)
                details.append({'file':name,'sha256':sha(p),'bytes':p.stat().st_size})
    return {'required':AGENT_NOTES,'present':present,'missing':missing,'empty':empty,'invalid':invalid,'details':details,'complete':not missing and not empty and not invalid}

def revalidate_notes(folder):
    """Re-check notes after Agent 5 has written its own note.

    This mutates only the audit envelope and generated Markdown report.  It
    never creates note files or changes any upstream calculation artifact.
    """
    audit_path=folder/NAMES[4]
    if not audit_path.exists(): raise ValueError('尚未完成 Stage 5，無法重驗證 notes')
    audit=read_json(audit_path); result=audit.get('result',{}); notes=note_status(folder)
    result['ai_notes']=notes
    checks=result.get('checks',[]); found=False
    for item in checks:
        if item.get('check')=='AI角色分析紀錄完整':
            item['pass']=notes['complete'];item['detail']=notes;found=True
    if not found: checks.append({'check':'AI角色分析紀錄完整','pass':notes['complete'],'detail':notes})
    result['checks']=checks
    warning='缺少完整 agent_notes；Python 工具不會代填 AI 分析'
    if notes['complete']:
        result['issues']=[x for x in result.get('issues',[]) if x!=warning]
    elif warning not in result.get('issues',[]): result.setdefault('issues',[]).append(warning)
    audit['result']=result;audit['validation']['checks']=checks
    write_json(audit_path,audit);log(folder,'ai_notes_revalidated',**notes);report(folder)
    print(f"AI notes revalidated: {'complete' if notes['complete'] else 'incomplete'} -> {audit_path}")
    return audit

def envelope(folder,c,i,result,status,questions=(),sources=(),checks=(),issues=()):
    upstream=[{'file':n,'sha256':sha(folder/n),'status':read_json(folder/n)['status']} for n in NAMES[:i-1]]
    return {'run_id':folder.name,'agent_id':f'{i:02}','status':status,'project_context':{k:c.get(k) for k in ('business_type','location','district','floor_area_sqm','budget_twd','opening_target_date','staff_count','payroll','full_time_count','part_time_count','assumptions')},'upstream_artifacts':upstream,'sources':list(sources),'open_questions':list(questions),'needs_authority_confirmation':i>=2,'result':result,'validation':{'checks':list(checks),'issues':list(issues)}}
def stage(folder,i):
    c=read_json(folder/'config.json'); log(folder,'stage_started',stage=i,mode='deterministic_python_tool')
    prior=[]
    for j,n in enumerate(NAMES[:i-1]):
        a=read_json(folder/n)
        if a['run_id']!=folder.name or a['agent_id']!=f'{j+1:02}': raise ValueError('上游 run_id 或角色不符')
        for u in a['upstream_artifacts']:
            if sha(folder/u['file'])!=u['sha256']: raise ValueError('上游已變更，請重新執行受影響階段')
        prior.append(a)
    # 同一次執行不允許偷偷改設定；更改需求應建立新 run。
    meta=read_json(folder/'run_manifest.json')
    if sha(folder/'config.json')!=meta['config_sha256']: raise ValueError('設定已變更；請建立新 run')
    if i==1:
        rows=[];q={'rows':0,'warnings':[]};sources=[];questions=[]
        if meta['input']:
            p=folder/meta['input']; sources=[{'file':p.name,'sha256':sha(p),'type':meta['source_type'],'period':c.get('data_period'),'acquired_at':meta['created_at'],'verification':'not_authenticated'}]
            if sha(p)!=meta['input_sha256']: raise ValueError('原始資料已變更')
            try: rows,q=clean(p,meta['source_type'],c.get('data_period'),c.get('geography'))
            except ValueError as e: q['warnings'].append(str(e));questions.append('修正資料後重新建立 run')
        else: questions.append('未提供候選商圈資料')
        if rows:
            csv_out(folder/'cleaned_market.csv',rows)
            if c.get('candidates'):
                requested=set(c['candidates']); rows=[r for r in rows if r['district'] in requested]
                if requested!={r['district'] for r in rows}: questions.append('部分指定商圈缺資料')
        q['rows_analyzed']=len(rows)
        ranked=rank(rows,c['weights']); sensitivity={}
        for label,w in [('預設',DEFAULT_WEIGHTS),('交通優先',{'population':25,'footfall':50,'competitors':15,'rent':10}),('租金優先',{'population':25,'footfall':20,'competitors':15,'rent':40})]:
            sensitivity[label]=[r['district'] for r in rank(rows,w)]
        if ranked: csv_out(folder/'market_comparison.csv',[{**{k:v for k,v in r.items() if k!='contributions'},**{k+'_points':v for k,v in r['contributions'].items()}} for r in ranked])
        chosen=next((r for r in rows if r['district']==c.get('district')),None)
        if not chosen and not c.get('district') and ranked: chosen=next(r for r in rows if r['district']==ranked[0]['district']);questions.append('推薦商圈暫作試算選址，尚未確認租約')
        if c.get('district') and not chosen: questions.append('指定地點沒有可用商圈資料')
        result={'quality':q,'candidates':rows,'ranked':ranked,'weights':c['weights'],'sensitivity':sensitivity,'selected':chosen,'recommendation':ranked[0]['district'] if ranked else None,'customer_assumptions':'人口及交通僅為潛在客群代理；年齡與實際消費偏好未知','method':'min-max；同值 0.5；競品與租金反向；加權分數 0–100，非成功率'}
        questions+=q['warnings']; status='complete' if ranked and not questions else 'partial';a=envelope(folder,c,i,result,status,questions,sources)
    elif i==2:
        rows=legal(c); a=envelope(folder,c,i,{'items':rows},'partial',['需取得實際地址、規模及最新法規；官方入口尚未逐條核實'],[{'url':r['source'],'period':None,'acquired_at':None,'verification':'reference_only'} for r in rows])
    elif i==3:
        selected=prior[0]['result']['selected']; c=dict(c); origin='user input' if c.get('rent') is not None else None
        if c.get('rent') is None and selected: c['rent']=selected['rent'];origin='market candidate assumption';c['assumptions']+=['租金取自候選地點資料，未核實租約']
        if c.get('deposit') is None and c.get('rent') is not None and c.get('allow_assumptions'): c['deposit']=2*c['rent'];c['assumptions']+=['押金假設為兩個月租金']
        f=finance(c);c=f.get('effective_config',c);f['rent_origin']=origin;f['legal_costs_pending']=[x['item'] for x in prior[1]['result']['items'] if x['possible_cost'] is None];f['effective_config']=c
        if f['scenarios']: csv_out(folder/'finance_scenarios.csv',f['scenarios'])
        a=envelope(folder,c,i,f,'partial' if f.get('missing') or f['legal_costs_pending'] else 'complete',f.get('missing',[])+['實際法規設備成本待確認'])
    elif i==4:
        f=prior[2]['result']; c=f['effective_config']; shop=c['business_type']; food=shop in FOOD or c.get('food_business') is True
        equipment=['收銀與紀錄設備','安全與清潔設備']+(['冷藏、食品接觸器具、洗手清潔設備'] if food else ['依業態確認專用設備'])
        if shop=='手搖飲店': equipment+=['封口機、製冰機、茶飲製備設備']
        steps=[{'id':str(j+1),'item':r['item'],'authority':r['authority'],'action':r['action_required'],'documents':r['documents'],'prerequisites':r['prerequisites'],'estimated_workdays':r['estimated_workdays'],'depends_on':[]} for j,r in enumerate(prior[1]['result']['items'])]
        steps.append({'id':'final','item':'開幕前稽核','authority':'創業者及適用主管機關','action':'確認高風險項目與預算後方可定案','documents':None,'prerequisites':'所有適用查核完成','estimated_workdays':None,'depends_on':[r['id'] for r in steps]})
        sim=simulate(c,f);csv_out(folder/'daily_simulation.csv',sim)
        result={'positioning':f'{shop}；依選址與客群假設調整商品','equipment':equipment,'staff_count':c.get('staff_count'),'staff_sop':['交班與訂單紀錄','清潔與安全檢查','工時與教育訓練','客訴與異常通報']+(['食材保存、來源及交叉污染防制'] if food else []),'channels':f.get('shares'),'operating_hours':c.get('operating_hours'),'products':c.get('products'),'schedule':steps,'simulation':{'seed':c.get('seed'),'days':len(sim),'rows':sim,'limitation':'假設事件及交易量；每列為營業日，非真實預測'},'cost_change_required':False}
        (folder/'04_opening_schedule.md').write_text('# 開店條件式排程\n\n工作天與文件未查證，暫不推估開幕日期。\n\n|工作|機關|行動|前置條件|工作天|\n|---|---|---|---|---|\n'+'\n'.join(f"|{r['item']}|{r['authority']}|{r['action']}|{r['prerequisites'] or '待確認'}|待確認|" for r in steps),encoding='utf-8')
        a=envelope(folder,c,i,result,'partial',['實際設備報價、人員配置、營業時間、文件及開幕日需確認'])
    else:
        m,l,f,b=[x['result'] for x in prior]; checks=[]; issues=[]; blocking=[]
        def check(name,ok,detail,blocking_check=True):
            checks.append({'check':name,'pass':bool(ok),'detail':detail})
            if not ok and blocking_check: blocking.append(name)
        check('上游檔案完整',all(x['run_id']==folder.name for x in prior),'同 run_id 且 SHA-256 交接已驗證')
        if m['ranked']:
            rows=m['candidates'];top=m['ranked'][0]; row=next(r for r in rows if r['district']==top['district']); total=0
            for k,w in m['weights'].items():
                vals=[r[k] for r in rows];lo,hi=min(vals),max(vals);fraction=.5 if lo==hi else ((hi-row[k]) if k in ('rent','competitors') else (row[k]-lo))/(hi-lo);total+=fraction*w
            check('商圈最高分重算',abs(total-top['score'])<1e-8,{'recomputed':total,'reported':top['score']})
            raw,_=clean(folder/meta['input'],meta['source_type'],c.get('data_period'),c.get('geography'))
            rawrow=next(r for r in raw if r['district']==row['district']);check('原始資料抽查',rawrow['population']==row['population'],{'district':row['district'],'population':rawrow['population']})
        else: issues.append('商圈資料不足，未能重新計分')
        check('高風險法規行動矩陣',all(x['authority'] and x['action_required'] and any(s['item']==x['item'] for s in b['schedule']) for x in l['items'] if x['risk']=='high'),'逐項核對')
        if f['scenarios']:
            x=f['inputs'];q=f['scenarios'][1]['daily'];d=x['days']; revenue=x['price']*q*d; cost=x['rent']+x['payroll']+x['fixed_other']+q*d*x['variable']+q*d*x['delivery_share']*(x['price']*x['commission']+x['delivery_packaging']);profit=revenue-cost
            check('一般情境財務獨立重算',abs(profit-f['scenarios'][1]['profit'])<.011,{'recomputed':profit,'reported':f['scenarios'][1]['profit']})
            check('預算及預備金覆蓋',f['budget_gap']==0,{'gap':f['budget_gap']})
            check('通路比例',abs(sum(f['shares'].values())-1)<1e-8,'合計 100%')
        else: issues.append('財務參數不足，未能重新驗算')
        staff=f.get('staffing',{})
        staff_ok=staff.get('consistency')=='ok'
        check('員工人數與人事成本一致性',staff_ok,staff,blocking_check=bool(staff.get('hard_issues')))
        if not staff_ok: issues.append('人事成本需依員工類型、工時及雇主負擔確認')
        floor_ok=c.get('floor_area_sqm') is not None
        check('坪數與裝修成本假設',floor_ok,{'floor_area_sqm':c.get('floor_area_sqm'),'fitout':f.get('effective_config',{}).get('fitout'),'detail':'未提供坪數時，裝修費僅為教學假設'},blocking_check=False)
        if not floor_ok: issues.append('坪數未提供，裝修成本無法做單位成本檢核')
        expected_equipment=bool(b.get('equipment')) and (c.get('business_type') not in FOOD or any('冷藏' in str(x) for x in b.get('equipment',[])))
        check('店型與設備需求一致性',expected_equipment,{'business_type':c.get('business_type'),'equipment':b.get('equipment')},blocking_check=False)
        legal_costs_ok=not f.get('legal_costs_pending')
        check('法規限制與成本時程關聯',legal_costs_ok,{'pending_cost_items':f.get('legal_costs_pending',[])},blocking_check=False)
        if not legal_costs_ok: issues.append('法規相關成本與時程尚未查證')
        user_fields=('budget_twd','price','daily','days','delivery_share','staff_count')
        effective=f.get('effective_config',{})
        input_ok=all(c.get(k) is None or effective.get(k)==c.get(k) for k in user_fields)
        check('使用者原始輸入與最終報告一致',input_ok,{k:{'input':c.get(k),'effective':effective.get(k)} for k in user_fields},blocking_check=True)
        quality=m.get('quality',{})
        rows_ok=quality.get('rows_original') is not None and quality.get('rows_analyzed') is not None and quality['rows_analyzed']<=quality['rows_original']
        check('原始資料筆數與分析筆數分開呈現',rows_ok,{'rows_original':quality.get('rows_original'),'rows_cleaned':quality.get('rows'),'rows_analyzed':quality.get('rows_analyzed')},blocking_check=False)
        notes=note_status(folder)
        log(folder,'ai_notes_checked',**notes)
        check('AI角色分析紀錄完整',notes['complete'],notes,blocking_check=False)
        if not notes['complete']: issues.append('缺少完整 agent_notes；Python 工具不會代填 AI 分析')
        issues+=['法規仍需個案確認','財務及客流屬情境假設']
        status='blocked' if blocking else 'pass_with_conditions'
        a=envelope(folder,c,i,{'audit_status':status,'checks':checks,'blocking':blocking,'issues':issues,'repair_rounds':0,'repair_instruction':'若有錯誤，建立新 run 修正輸入並重跑；不自動捏造數值','actual_skill_auto_trigger_tested':False,'ai_notes':notes},'blocked' if blocking else 'partial',issues,checks=checks,issues=blocking)
    write_json(folder/NAMES[i-1],a);log(folder,'stage_completed',stage=i,artifact=NAMES[i-1],sha256=sha(folder/NAMES[i-1]),status=a['status']);print(f'Stage {i}: {a["status"]} -> {folder/NAMES[i-1]}')
    if i==5: report(folder)
    return a

def report(folder):
    m,l,f,b,a=[read_json(folder/n)['result'] for n in NAMES]; c=read_json(folder/'config.json')
    lines=['# OpenShop AI V5｜開店可行性報告','',f"店型：{c['business_type']}｜地點：{c['location']}｜預算：{c.get('budget_twd')} 元",f"審查：**{a['audit_status']}**（非官方核准）",'本報告為 Python 工具成果，非 AI 自動觸發證據。','## 市場與資料品質',f"原始資料筆數：{m['quality'].get('rows_original','未提供')}；清理後筆數：{m['quality'].get('rows','未提供')}；實際分析筆數：{m['quality'].get('rows_analyzed','未提供')}；來源類型：{m['quality'].get('source_type','未提供')}",*['- '+x for x in m['quality']['warnings']],m['method'],'|商圈|分數|月租金|','|---|---:|---:|',*[f"|{r['district']}|{r['score']:.2f}|{r['rent']:,.0f}|" for r in m['ranked']],f"客群：{m['customer_assumptions']}",f"權重敏感度：{m['sensitivity']}",'## 法規與證照（待確認）',*[f"- {r['item']}：{r['action_required']}；{r['authority']}；{r['source']}" for r in l['items']],'## 財務與成本']
    if f['scenarios']:
        lines += [f"初期支出 {f['initial_spend']:,.0f}；剩餘現金 {f['cash_after_setup']:,.0f}；預算缺口 {f['budget_gap']:,.0f}；每日損益兩平 {f['breakeven_daily']}", '|情境|每日交易|月營收|月成本|月損益|','|---|---:|---:|---:|---:|',*[f"|{r['scenario']}|{r['daily']}|{r['revenue']:,.0f}|{r['cost']:,.0f}|{r['profit']:,.0f}|" for r in f['scenarios']],*['- '+x for x in f['limitations']]]
    else: lines+=['缺少參數：'+', '.join(f['missing'])]
    staff=f.get('staffing',{})
    staffing_lines=[f"人事成本：{f.get('inputs',{}).get('payroll','未計算')} 元／月；來源：{staff.get('payroll_source','未提供')}"]
    if staff.get('sensitivity'):
        staffing_lines += ['人事成本敏感度：','|情境|月人事成本|說明|','|---|---:|---|'] + [f"|{x['scenario']}|{x['payroll']:,.0f}|{x['assumption']}|" for x in staff['sensitivity']]
    lines+=['## 營運及開店程序',b['positioning'],f"設備：{'、'.join(b['equipment'])}；人數：{b['staff_count']}",*staffing_lines,'見 04_opening_schedule.md、daily_simulation.csv（如有）。','## 假設與審查',*['- '+str(x) for x in f['effective_config']['assumptions']],*['- '+str(x) for x in staff.get('warnings',[])],*['- '+str(x) for x in a['issues']],*['- 阻擋：'+x for x in a['blocking']],'## 檢核紀錄',*[f"- {x['check']}：{'通過' if x['pass'] else '需確認'}；{x['detail']}" for x in a['checks']], '## AI 分析紀錄',f"agent_notes 狀態：{a.get('ai_notes',{}).get('complete',False)}；Python 工具不會自動產生或填寫 AI notes。","正式 AI 工作流程完成五份 notes 後，另由 AI 產出 07_ai_business_advice.md。"]
    (folder/'06_final_report.md').write_text('\n\n'.join(lines),encoding='utf-8');log(folder,'report_written',file='06_final_report.md')
    try:
        import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
        charts=folder/'charts';charts.mkdir(exist_ok=True)
        if m['ranked']:
            plt.bar(range(len(m['ranked'])),[r['score'] for r in m['ranked']]);plt.xticks(range(len(m['ranked'])),[str(i+1) for i in range(len(m['ranked']))]);plt.ylabel('Relative score');plt.xlabel('Rank (see market_comparison.csv)');plt.ylim(0,100);plt.tight_layout();plt.savefig(charts/'market_scores.png',dpi=160);plt.close()
        if f['scenarios']:
            plt.bar(['Conservative','Base','Optimistic'],[r['profit'] for r in f['scenarios']]);plt.axhline(0);plt.ylabel('Monthly profit (TWD)');plt.tight_layout();plt.savefig(charts/'profit_scenarios.png',dpi=160);plt.close()
        if b['simulation']['rows']:
            plt.plot([r['day'] for r in b['simulation']['rows']],[r['cash'] for r in b['simulation']['rows']],marker='o');plt.xlabel('Simulated operating day');plt.ylabel('Cash (TWD)');plt.tight_layout();plt.savefig(charts/'cash_simulation.png',dpi=160);plt.close()
        log(folder,'charts_written',files=[p.name for p in charts.glob('*.png')])
    except ImportError: log(folder,'charts_skipped',reason='matplotlib not installed')

def init(config_path,input_path,source_type,output):
    c=config(read_json(config_path));folder=Path(output).resolve() if output else ROOT/'outputs'/uuid.uuid4().hex[:12]
    folder.mkdir(parents=True,exist_ok=False);write_json(folder/'config.json',c)
    dest=None
    if input_path:
        p=Path(input_path);dest='original'+p.suffix.lower();shutil.copyfile(p,folder/dest)
    write_json(folder/'run_manifest.json',{'created_at':now(),'config_sha256':sha(folder/'config.json'),'input':dest,'input_sha256':sha(folder/dest) if dest else None,'source_type':source_type});log(folder,'initialized',mode='deterministic_python_tool',skill_trigger='not_tested');print(folder);return folder

def main():
    p=argparse.ArgumentParser();sp=p.add_subparsers(dest='cmd',required=True)
    for cmd in ('init','all'):
        x=sp.add_parser(cmd);x.add_argument('--config',required=True);x.add_argument('--input');x.add_argument('--source-type',choices=['user','synthetic','derived'],default='user');x.add_argument('--output')
    x=sp.add_parser('stage');x.add_argument('--run',required=True);x.add_argument('--number',type=int,choices=range(1,6),required=True)
    x=sp.add_parser('validate-notes');x.add_argument('--run',required=True)
    args=p.parse_args()
    try:
        if args.cmd=='stage':
            folder=Path(args.run).resolve();i=args.number
            if any((folder/n).exists() for n in NAMES[i-1:]): raise ValueError('已有此階段或下游輸出；請建立新 run 保留歷史')
            stage(folder,i)
        elif args.cmd=='validate-notes':
            revalidate_notes(Path(args.run).resolve())
        else:
            folder=init(args.config,args.input,args.source_type,args.output)
            if args.cmd=='all':
                for i in range(1,6): stage(folder,i)
    except (ValueError,OSError,KeyError,TypeError) as e:
        print(f'ERROR: {e}',file=sys.stderr);return 1
    return 0
if __name__=='__main__': sys.exit(main())
