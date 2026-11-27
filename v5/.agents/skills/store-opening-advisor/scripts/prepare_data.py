"""依明確欄位映射整合不同來源；不猜測官方原始資料格式。"""
import argparse, json, csv, sys
from pathlib import Path
from engine import table,num,sha,write_json,csv_out,now,clean

def prepare(spec,base,output):
    period=spec['period'];geo=spec['geography'];city=spec['city'];areas=spec['districts']
    if not all((period,geo,city,areas)) or len(set(areas))!=len(areas):raise ValueError('須明確指定期間、地理粒度、城市與不重複候選地點')
    result={a:{'district':a,'period':period,'geography':geo,'data_source':'衍生資料；來源詳見 ETL manifest'} for a in areas};sources=[]
    for metric in ('population','competitors','footfall','rent'):
        cfg=spec['metrics'][metric];p=(base/cfg['file']).resolve();rows=table(p)
        if cfg.get('period')!=period or cfg.get('geography')!=geo or cfg.get('city')!=city:raise ValueError(metric+' 來源口徑不一致')
        if not cfg.get('unit') or not cfg.get('source'):raise ValueError(metric+' 缺少單位／來源')
        groups={a:[] for a in areas};seen=set()
        for r in rows:
            if cfg.get('city_column') and r[cfg['city_column']]!=city:continue
            if cfg.get('period_column') and r[cfg['period_column']]!=period:continue
            key=r[cfg['district_column']];key=cfg.get('district_map',{}).get(key,key)
            if key not in groups:continue
            record_id=tuple(str(r[k]) for k in cfg.get('unique_columns',[]))
            if record_id:
                if record_id in seen:raise ValueError(metric+' 重複原始識別欄位')
                seen.add(record_id)
            groups[key].append(num(r[cfg['value_column']],metric) if cfg['aggregate']!='count' else 1)
        for a,vals in groups.items():
            if not vals:raise ValueError(f'{metric} 缺少 {a} 資料，不補零')
            method=cfg['aggregate']
            if method=='single' and len(vals)==1:v=vals[0]
            elif method in ('sum','count') and cfg.get('unique_columns'):v=sum(vals)
            elif method=='mean' and cfg.get('unique_columns'):v=sum(vals)/len(vals)
            else:raise ValueError('聚合方式或唯一識別欄位不充分')
            result[a][metric]=v
        sources.append({'metric':metric,'file':cfg['file'],'sha256':sha(p),'source':cfg['source'],'period':period,'unit':cfg['unit'],'aggregation':cfg['aggregate'],'verification':'mapping_supplied_not_authenticated'})
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('輸出已存在')
    csv_out(output,list(result.values()));clean(output,'derived',period,geo);write_json(output.with_suffix('.manifest.json'),{'generated_at':now(),'city':city,'period':period,'geography':geo,'sources':sources,'output_sha256':sha(output)});return output
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mapping',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    try: f=Path(a.mapping);print(prepare(json.loads(f.read_text(encoding='utf-8-sig')),f.parent,Path(a.output)))
    except (ValueError,KeyError,OSError,TypeError) as e: print(e,file=sys.stderr);sys.exit(1)
