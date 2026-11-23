"""Unit-only artificial fixtures; NEVER used as real dashboard accident records."""
import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from core import normalize,summary,audit,read_bytes

def fixture():
 # Unit-test-only artificial values. Not distributed as source/demo analytics.
 return pd.DataFrame([{'發生年度':'114','發生月份':'2','發生日期':'3','發生時間':'08:10','事故類別名稱':'A1','發生地點':'桃園市某路口','天候名稱':'晴','經度':'121.3','緯度':'24.9'},
 {'發生年度':'114','發生月份':'2','發生日期':'3','發生時間':'2500','事故類別名稱':'A1','發生地點':'桃園市某路口','天候名稱':'雨','經度':'999','緯度':'24.9'}])

def test_quality_and_hours():
 clean,q=normalize(fixture());assert len(clean)==2;assert q['coordinate_excluded_rows']==1
 assert clean.year.iloc[0]==2025;assert clean.hour.iloc[0]==8;assert pd.isna(clean.hour.iloc[1])
 stat,hot=summary(clean);assert stat['record_count']==2;assert stat['map_record_count']==1
 assert audit(clean,q,stat,hot)['status']=='PASS'

def test_audit_detects_tamper():
 clean,q=normalize(fixture());stat,hot=summary(clean);stat['record_count']=500
 assert audit(clean,q,stat,hot)['status']=='FAIL'

def test_empty_rejected():
 with pytest.raises(ValueError):normalize(pd.DataFrame())

def test_unknown_json_rejected():
 with pytest.raises(ValueError):read_bytes(b'{"unexpected":1}','.json')


def test_nullable_year_with_missing_values():
    data=fixture()
    data.loc[1,'發生年度']=None
    norm,quality=normalize(data)
    assert str(norm.year.dtype)=='Int64'
    stats,cells=summary(norm)
    assert stats['years']['未提供']==1
    assert stats['years']['2025']==1
    assert audit(norm,quality,stats,cells)['status']=='PASS'
