import json
import pytest
from scripts.studio_engine import parse_upload,rank_places,daily_simulation,play_one_day,create_artifacts

CONFIG={'shop':'手搖飲店','city':'桃園市','district':'中壢區','floor_area_sqm':60,'budget':800000,'price':65,
        'variable':25,'daily':80,'rent':35000,'payroll':75000,'fixed_other':20000,'days':26,
        'delivery_share':.2,'dinein_share':.3,'commission':.3,'delivery_packaging':5}

def data():
    return b'district,population,competitors,footfall,rent,data_source\nA,10000,12,8000,30000,user\nB,20000,33,12000,45000,user\n'

def test_upload_and_hash():
    df,q=parse_upload(data(),'case.csv');assert len(df)==2 and len(q['sha256'])==64

def test_bad_values_rejected():
    with pytest.raises(ValueError):parse_upload(b'district,population,competitors,footfall,rent\nA,-1,2,3,4\n','bad.csv')

def test_missing_columns_rejected():
    with pytest.raises(ValueError):parse_upload(b'district,population\nA,1\n','bad.csv')

def test_rank_stable():
    df,_=parse_upload(data(),'case.csv');assert len(rank_places(df))==2

def test_daily_sim_reproducible():
    x=daily_simulation(CONFIG,seed=99);y=daily_simulation(CONFIG,seed=99);assert x.equals(y)

def test_turn_decision_changes_outcome():
    x=play_one_day(CONFIG,choice='一般營業');y=play_one_day(CONFIG,choice='社群廣告');assert x[0]['profit']!=y[0]['profit']

def test_artifacts_linked():
    df,q=parse_upload(data(),'case.csv');m,l,p,a,sim,r=create_artifacts(CONFIG,df,q)
    assert m['status']=='complete' and l['upstream']=='01_market_report.json' and a['financial_formula_check']

def test_blocked_when_budget_low():
    cfg={**CONFIG,'budget':1000};m,l,p,a,s,r=create_artifacts(cfg,None,{})
    assert a['status']=='blocked'
