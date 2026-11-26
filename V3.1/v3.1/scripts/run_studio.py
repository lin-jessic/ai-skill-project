"""Command line professor-file demo runner. Supports CSV and JSON."""
import argparse,json
from pathlib import Path
from scripts.studio_engine import parse_upload,create_artifacts,save_artifacts,STORE_CATALOG

def main():
    parser=argparse.ArgumentParser(description='市場→法規→開店程序及審查，使用教師提供的 CSV/JSON')
    parser.add_argument('--input',required=True,help='CSV 或 JSON 商圈檔案')
    parser.add_argument('--shop',default='手搖飲店',choices=list(STORE_CATALOG))
    parser.add_argument('--city',default='桃園市')
    parser.add_argument('--output',default='outputs/studio_cli')
    args=parser.parse_args()
    p=Path(args.input);df,q=parse_upload(p.read_bytes(),p.name)
    config={'shop':args.shop,'city':args.city,'district':'未指定','floor_area_sqm':66.1,
            'budget':800000,'price':65,'variable':25,'daily':70,'rent':38000,'payroll':85000,
            'fixed_other':18000,'days':26,'delivery_share':.20,'dinein_share':.30,
            'commission':.30,'delivery_packaging':5,'opening_target_date':'2027-03-01'}
    a=create_artifacts(config,df,q);save_artifacts(args.output,a)
    print('Agent 1 MARKET: ',a[0]['status'])
    print('Agent 2 LEGAL: ',len(a[1]['items']),'items awaiting authority confirmation')
    print('Agent 3 OPENING AUDIT: ',a[3]['status'])
    print('Outputs:',Path(args.output).resolve())
    print('Important: input evidence and assumptions are not authenticated government statistics.')
    if a[3]['status']=='blocked':raise SystemExit(2)
if __name__=='__main__':main()
