import pandas as pd
import pytest
from scripts.logic import money_sim,population_summary,metro_summary,industry_summary,legal_checklist,read_any

def test_profit():
    x=money_sim(price=100,variable=40,daily=10,days=10,rent=1000,payroll=0,fixed_other=0,dinein_share=0,delivery_share=0)
    assert x['revenue']==10000 and x['monthly_profit']==5000 and x['breakeven_daily']==2

def test_delivery_cost():
    a=money_sim(dinein_share=0,delivery_share=0)
    b=money_sim(dinein_share=0,delivery_share=1)
    assert a['monthly_profit']>b['monthly_profit']

def test_invalid_shares():
    with pytest.raises(ValueError):money_sim(dinein_share=.7,delivery_share=.5)

def test_zero_contribution():
    assert money_sim(price=20,variable=25)['breakeven_daily'] is None

def test_population():
    d=pd.DataFrame({'區域別':['桃園市中壢區','桃園市中壢區','新北市板橋區'],'人口數':[100,200,300]})
    r=population_summary(d)
    assert r.loc[r.city=='桃園市','population'].sum()==300

def test_metro():
    d=pd.DataFrame({'捷運站別':['A','B'],'平均日運量':['1,200','100']})
    assert metro_summary(d).iloc[0]['daily_riders']==1200

def test_industry():
    d=pd.DataFrame({'縣市別':['桃園市'],'住宿及餐飲業家數':['1,234'],'總計家數':['2,345']})
    assert industry_summary(d).iloc[0]['restaurants']==1234

def test_legal_food():
    assert any(x['item']=='食品業者登錄' for x in legal_checklist('咖啡廳','桃園市'))
    assert not any(x['item']=='食品業者登錄' for x in legal_checklist('服飾店','桃園市'))
