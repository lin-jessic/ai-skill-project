"""Only synthetic fixtures for automated pipeline checking; never displayed as government data."""
import json, subprocess, sys
from pathlib import Path

def test_multi_source_pipeline(tmp_path):
    root = Path(__file__).resolve().parents[1]
    files=[]
    for year in (113,114):
        f=tmp_path / f'test_{year}.json'
        f.write_text(json.dumps([{'發生年度': str(year),'發生月份':'11','發生日期':'2','發生時間':'09:30','發生地點':'桃園市測試路口','天候名稱':'晴','經度':'121.29','緯度':'24.99','事故類別名稱':'A1'}],ensure_ascii=False),encoding='utf-8')
        files.append(str(f))
    out=tmp_path/'result'
    run=subprocess.run([sys.executable,str(root/'scripts'/'run_pipeline.py'),'--input',*files,'--out',str(out)],capture_output=True,text=True)
    assert run.returncode == 0,run.stdout+'\n'+run.stderr
    quality=json.loads((out/'01_quality.json').read_text(encoding='utf-8'))
    assert quality['input_rows']==2 and len(quality['sources'])==2
    assert json.loads((out/'03_audit.json').read_text(encoding='utf-8'))['status']=='PASS'
    import pandas as pd
    years=set(pd.read_csv(out/'01_normalized.csv').year.dropna().astype(int))
    assert years == {2024,2025}
