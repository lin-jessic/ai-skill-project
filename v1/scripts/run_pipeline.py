"""Orchestrate three *sequential role modules*, with independent audit stage."""
import sys,argparse,json
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from core import load_file,normalize,summary,audit,digest

ROOT=Path(__file__).resolve().parents[1]
def write_json(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True,nargs='+',help='可輸入多個官方 JSON/CSV/ZIP，合併年度');ap.add_argument('--out',default=str(ROOT/'outputs'));args=ap.parse_args()
    sources=[Path(x).resolve() for x in args.input];out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    print('Agent 1 | Inspect sources:', ', '.join(x.name for x in sources),flush=True)
    frames=[load_file(src) for src in sources]
    raw=pd.concat(frames,ignore_index=True,sort=False)
    norm,quality=normalize(raw)
    provenance=[{'file':p.name,'sha256':digest(p),'rows':len(df)} for p,df in zip(sources,frames)]
    quality.update({'source_file':', '.join(x.name for x in sources),'source_sha256':__import__('hashlib').sha256(''.join(x['sha256'] for x in provenance).encode()).hexdigest() if len(sources)>1 else digest(sources[0]),'sources':provenance,'processed_utc':datetime.now(timezone.utc).isoformat(),'provided_file_not_automatically_verified_as_government':True})
    norm.to_csv(out/'01_normalized.csv',index=False,encoding='utf-8-sig')
    write_json(out/'01_quality.json',quality)
    print('Agent 2 | Analyze records & spatial grid',flush=True)
    stats,cells=summary(norm)
    write_json(out/'02_summary.json',stats);cells.to_csv(out/'02_hotspots.csv',index=False,encoding='utf-8-sig')
    # Fully standalone HTML; Plotly CDN is optional and app itself works offline after pip install.
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        fig=go.Figure()
        subset=norm.loc[norm.map_valid,['lat','lon','location','category']].head(2500)
        if len(subset):
            fig.add_trace(go.Scattermap(lat=subset.lat,lon=subset.lon,mode='markers',marker={'size':7,'color':'#e94f54','opacity':0.6},text=subset.location.fillna('位置未提供'),name='歷史事故紀錄'))
            fig.update_layout(map={'style':'open-street-map','center':{'lat':float(subset.lat.median()),'lon':float(subset.lon.median())},'zoom':9})
        fig.update_layout(title='Historical collision records (mapped subset, not live alerts)',margin={'l':0,'r':0,'b':0,'t':50})
        fig.write_html(out/'dashboard.html',include_plotlyjs=True)
    except ImportError:
        (out/'dashboard.html').write_text('<h1>Please install requirements.txt to render maps.</h1>',encoding='utf-8')
    print('Agent 3 | Independently audit totals',flush=True)
    # reload from on-disk handoff to check file interoperability, not just in-memory pass
    reloaded=pd.read_csv(out/'01_normalized.csv',encoding='utf-8-sig',low_memory=False)
    reloaded['map_valid']=reloaded.map_valid.astype(str).str.lower().eq('true')
    checks=audit(reloaded,quality,stats,cells)
    write_json(out/'03_audit.json',checks)
    lines=['# 臺灣道路事故歷史資料分析','', '## 摘要',f"- 來源檔案：`{quality['source_file']}`",f"- SHA256：`{quality['source_sha256']}`",f"- 原始資料列數：{len(raw):,}",f"- 可用於地圖的資料列：{stats['map_record_count']:,}",'','## 主要內容',f"- 無有效座標列數：{stats['excluded_coordinate_count']:,}",f"- 事故類型統計：{stats['categories']}",f"- 熱點格網：0.005 度；非真正路段、非事故發生機率。",'','## 結論與建議','- 使用官方資料作歷史事故集中程度探索，請勿作為即時安全或救護派遣判斷。','', '## 資料品質與限制',f"- 審查狀態：**{checks['status']}**",f"- 問題：{checks['issues']}",'- 統計口徑為資料列；若同一事故多筆當事者紀錄，不能直接視作獨立事故件數。','- 無個案送醫醫院或就醫紀錄。']
    (out/'03_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'input_rows':len(raw),'mapped_rows':stats['map_record_count'],'audit':checks['status'],'outputs':str(out)},ensure_ascii=False,indent=2))
    if checks['status']!='PASS':raise SystemExit(3)
if __name__=='__main__':main()
