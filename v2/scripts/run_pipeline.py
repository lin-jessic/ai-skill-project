"""Three-role audited, reproducible single-configuration pipeline."""
import argparse,datetime,json,sys
from pathlib import Path
from scripts.logic import *

def run(config):
    OUT.mkdir(parents=True,exist_ok=True)
    shop=config['shop'];city=clean_city(config['city'])
    print('[Agent 1] 法規與營運檢查')
    legal=legal_checklist(shop,city);ops=operations_plan(shop)
    (OUT/'01_legal.json').write_text(json.dumps(legal,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'01_operations.json').write_text(json.dumps(ops,ensure_ascii=False,indent=2),encoding='utf-8')
    print('[Agent 2] 官方資料可用性與市場分析')
    status=availability();stats={}
    for key in ('population','metro','industry'):
        if not status[key]['present']:stats[key]='未取得官方資料';continue
        try:
            d=read_any(RAW/SOURCES[key]['file'])
            if key=='population':
                p=population_summary(d);sub=p[p.city==city];stats['人口資料']=f'{int(sub.population.sum()):,} 人（已解析範圍：{city}，請確認月份及重複資料）' if len(sub) else '此資料無該城市'
            elif key=='industry':
                x=industry_summary(d);sub=x[x.city==city];stats['商業登記']=f'{int(sub.restaurants.sum()):,} 家（官方歷史月份，不代表現況）' if len(sub) else '此資料無該城市'
            else:
                x=metro_summary(d);stats['桃園捷運']=f'{len(x)} 站可用運量資料；注意站體運量不是店鋪人流'
        except Exception as e:stats[key]=f'解析失敗：{e}'
    (OUT/'02_market.json').write_text(json.dumps({'stats':stats,'sources':status},ensure_ascii=False,indent=2),encoding='utf-8')
    print('[Agent 3] 情境模擬及公式審查')
    sim=money_sim(**config['finance']);config['date']=datetime.date.today().isoformat()
    (OUT/'03_finance.json').write_text(json.dumps(sim,ensure_ascii=False,indent=2),encoding='utf-8')
    report=build_report(config,sim,stats,legal)
    (OUT/'03_business_report.md').write_text(report,encoding='utf-8')
    assert abs(sim['revenue']-config['finance']['price']*config['finance']['daily']*config['finance'].get('days',26))<0.01
    audit={'financial_formula':'PASS','legal_clearance':'NOT_VERIFIED','official_data_status':{k:v['present'] for k,v in status.items()},'report':'03_business_report.md','disclaimer':'PASS 只代表計算一致性，非法律或商業可行性核准'}
    (OUT/'04_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('完成：',OUT,'｜財務算式核對 PASS；法規未核准。');return audit
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default=str(ROOT/'config_example.json'));a=p.parse_args()
    config=json.loads(Path(a.config).read_text(encoding='utf-8'));run(config)
