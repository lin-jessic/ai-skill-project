import unittest,sys,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.agents/skills/store-opening-advisor/scripts'))
from engine import *
from run import init,stage,NAMES,AGENT_NOTES,revalidate_notes
from prepare_data import prepare
from download_official import allowed
class Tests(unittest.TestCase):
    def test_clean(self):
        rows,q=clean(ROOT/'sample-data/market_demo.csv','synthetic');self.assertEqual(q['rows'],5);self.assertEqual(len(rows),5)
    def test_bad_values(self):
        for val in ('','NaN','inf','-1','abc'):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'x.csv';p.write_text(f'district,population,competitors,footfall,rent\nA,{val},2,3,4\n');self.assertRaises(ValueError,clean,p)
    def test_missing_column(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';p.write_text('district,population\nA,1\n');self.assertRaises(ValueError,clean,p)
    def test_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';p.write_text('district,population,competitors,footfall,rent\nA,1,2,3,4\nA,1,2,3,4\n');self.assertEqual(clean(p)[1]['duplicates_removed'],1);p.write_text(p.read_text()+'A,2,2,3,4\n');self.assertRaises(ValueError,clean,p)
    def test_weights(self):
        self.assertRaises(ValueError,weights,dict(population=100,footfall=1,competitors=0,rent=0));rows,_=clean(ROOT/'sample-data/market_demo.csv');r=rank(rows,DEFAULT_WEIGHTS);self.assertAlmostEqual(r[0]['score'],sum(r[0]['contributions'].values()));self.assertEqual(rank(rows[:1],DEFAULT_WEIGHTS),[])
    def test_config(self):
        c=read_json(ROOT/'sample-data/config_demo.json');c['days']=0;self.assertRaises(ValueError,config,c);c['days']=26;c['budget_twd']=1500000;self.assertEqual(config(c)['budget_twd'],1500000)
    def test_finance(self):
        c=config(read_json(ROOT/'sample-data/config_demo.json'));c.update(rent=39000,deposit=78000);f=finance(c);self.assertAlmostEqual(f['scenarios'][1]['profit'],(65-25-.2*(65*.3+5))*150*26-(39000+85000+18000));c['price']=1;self.assertIsNone(finance(c)['breakeven_daily']);self.assertEqual(simulate(c,f),simulate(c,f))
    def test_staffing_estimate_changes_with_count(self):
        raw=read_json(ROOT/'sample-data/config_demo.json');raw.update(staff_count=3);c=config(raw);c.update(rent=39000,deposit=78000);f=finance(c)
        self.assertEqual(f['staffing']['staff_count'],3)
        self.assertEqual(f['staffing']['payroll_source'],'estimated_mixed_teaching_default')
        self.assertGreater(f['staffing']['payroll'],0)
        self.assertEqual(f['inputs']['payroll'],f['staffing']['payroll'])
        raw['staff_count']=2;c2=config(raw);c2.update(rent=39000,deposit=78000);self.assertNotEqual(finance(c2)['inputs']['payroll'],f['inputs']['payroll'])
    def test_explicit_payroll_is_preserved(self):
        raw=read_json(ROOT/'sample-data/config_demo.json');raw.update(staff_count=3,payroll=120000);c=config(raw);c.update(rent=39000,deposit=78000);f=finance(c)
        self.assertEqual(f['inputs']['payroll'],120000)
        self.assertEqual(f['staffing']['payroll_source'],'user_input')
    def test_explicit_staffing_mix_is_estimated(self):
        raw=read_json(ROOT/'sample-data/config_demo.json');raw.update(full_time_count=1,part_time_count=2,full_time_salary=32000,part_time_hourly_wage=210,part_time_hours_per_month=60,employer_burden_rate=.2);c=config(raw);c.update(rent=39000,deposit=78000);f=finance(c)
        self.assertEqual(f['staffing']['staff_count'],3)
        self.assertEqual(f['staffing']['full_time_count'],1)
        self.assertEqual(f['staffing']['part_time_count'],2)
        self.assertAlmostEqual(f['inputs']['payroll'],(32000+2*210*60)*1.2)
    def test_full_a2_finance_regression(self):
        raw=read_json(ROOT/'sample-data/config_demo.json');raw.update(budget_twd=1200000,price=75,daily=180,days=26,staff_count=3,delivery_share=.3);raw.pop('payroll',None);c=config(raw);c.update(rent=39000,deposit=78000);f=finance(c)
        self.assertAlmostEqual(f['inputs']['payroll'],87400)
        self.assertAlmostEqual(f['scenarios'][1]['revenue'],351000)
        self.assertAlmostEqual(f['scenarios'][1]['profit'],50990)
        self.assertEqual(f['breakeven_daily'],134)
        self.assertTrue(all('下界' not in x['assumption'] and '上界' not in x['assumption'] for x in f['staffing']['sensitivity']))
    def test_pipeline_flags_staffing_mismatch_and_rows(self):
        with tempfile.TemporaryDirectory() as d:
            raw=read_json(ROOT/'sample-data/config_demo.json');raw.update(staff_count=3,payroll=85000);p=Path(d)/'c.json';write_json(p,raw);folder=init(p,ROOT/'sample-data/market_demo.csv','synthetic',Path(d)/'r')
            for i in range(1,6): stage(folder,i)
            market=read_json(folder/NAMES[0]);audit=read_json(folder/NAMES[4])['result']
            self.assertEqual(market['result']['quality']['rows_original'],5)
            self.assertEqual(market['result']['quality']['rows'],5)
            self.assertEqual(market['result']['quality']['rows_analyzed'],2)
            self.assertTrue(any(x['check']=='員工人數與人事成本一致性' and not x['pass'] for x in audit['checks']))
            self.assertFalse(audit['ai_notes']['complete'])
    def test_revalidate_notes_after_stage5(self):
        with tempfile.TemporaryDirectory() as d:
            folder=init(ROOT/'sample-data/config_demo.json',ROOT/'sample-data/market_demo.csv','synthetic',Path(d)/'r')
            for i in range(1,6): stage(folder,i)
            for name in AGENT_NOTES:
                (folder/name).write_text('# 實際輸入\n上游成果\n工具結果\n分析判斷\n假設與限制\n交接事項\n',encoding='utf-8')
            audit=revalidate_notes(folder);self.assertTrue(audit['result']['ai_notes']['complete']);self.assertTrue(next(x for x in audit['result']['checks'] if x['check']=='AI角色分析紀錄完整')['pass']);self.assertIn('agent_notes 狀態：True',(folder/'06_final_report.md').read_text(encoding='utf-8'))
    def test_etl(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.csv';prepare(read_json(ROOT/'sample-data/etl_mapping_demo.json'),ROOT/'sample-data',p);self.assertEqual(len(clean(p,'derived')[0]),2)
    def test_urls(self):
        self.assertTrue(allowed('https://data.gov.tw/dataset/9400'));self.assertFalse(allowed('https://gov.tw.evil.com/'));self.assertFalse(allowed('http://data.gov.tw/'))
    def test_pipeline_and_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            folder=init(ROOT/'sample-data/config_demo.json',ROOT/'sample-data/market_demo.csv','synthetic',Path(d)/'r');
            for i in range(1,6):stage(folder,i)
            self.assertTrue(all((folder/n).exists() for n in NAMES));a=read_json(folder/NAMES[4]);self.assertEqual(a['result']['audit_status'],'pass_with_conditions');self.assertFalse(a['result']['actual_skill_auto_trigger_tested']);self.assertTrue((folder/'06_final_report.md').exists());(folder/NAMES[0]).write_text('{}');self.assertRaises((ValueError,KeyError),stage,folder,5)
    def test_budget_block(self):
        with tempfile.TemporaryDirectory() as d:
            c=read_json(ROOT/'sample-data/config_demo.json');c['budget_twd']=10000;p=Path(d)/'c.json';write_json(p,c);folder=init(p,ROOT/'sample-data/market_demo.csv','synthetic',Path(d)/'r');
            for i in range(1,6):stage(folder,i)
            self.assertEqual(read_json(folder/NAMES[4])['result']['audit_status'],'blocked')
if __name__=='__main__':unittest.main()
