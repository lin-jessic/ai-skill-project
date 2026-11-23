"""SafeRoad Studio | official historical collision data explorer (no synthetic rows)."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'outputs'
ACCENT = '#f16b56'
INK = '#182838'
TEAL = '#087f7b'
BLUE = '#426b91'
BG = '#f5f6f5'

st.set_page_config(page_title='SafeRoad Studio｜道路資料探索', page_icon='◈', layout='wide', initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap');
html,body,[class*="css"],.stApp {font-family:'DM Sans','Noto Sans TC',sans-serif!important}
.stApp {background:#f5f6f5;color:#182838}
.block-container {max-width:1550px;padding:2rem 3.5rem 4rem}
[data-testid="stSidebar"] {background:#eef0ef;border-right:1px solid #e0e4e2}
[data-testid="stSidebar"] .block-container {padding:1.2rem}
[data-testid="stSidebar"] label {font-weight:650!important;font-size:.82rem!important}
[data-testid="stMetric"] {background:#fff;border:1px solid #e4e9e6;border-radius:8px;padding:16px 18px;min-height:115px;box-shadow:0 3px 8px #152f2c08}
[data-testid="stMetricLabel"] {color:#71817f;font-weight:600}
[data-testid="stMetricValue"] {font-size:1.8rem;color:#182838;font-weight:700;letter-spacing:-1.1px}
[data-testid="stTabs"] button {font-weight:650;font-size:14px;padding:13px 15px;color:#637573}
[data-testid="stTabs"] [aria-selected="true"] {color:#0f5253!important}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{background:#0c7774}
h1,h2,h3 {color:#182838;letter-spacing:-.04em}
h2{font-size:1.35rem!important;margin:1rem 0 .6rem!important}
h3{font-size:1.03rem!important}
p {line-height:1.65}
div[data-testid="stDataFrame"] {border-radius:9px;overflow:hidden}
[data-testid="stButton"] button[kind="primary"]{background:#0d7772;border:none;border-radius:7px}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:10px}
.hero {padding:30px 34px;border:1px solid #e4e9e6;background:#fff;border-radius:12px;margin:0 0 19px;position:relative;overflow:hidden}
.hero:before {content:'';position:absolute;left:0;top:0;bottom:0;width:7px;background:#0d7772}
.eyebrow {font-size:11px;letter-spacing:2.2px;font-weight:700;color:#147b77}
.hero h1 {font-size:35px!important;font-weight:800;margin:10px 0!important}
.hero p {max-width:800px;margin:0;color:#627371;font-size:14px}
.smallprint{font-size:12px;color:#7b8987}
.section-kicker {color:#087f7b;font-weight:800;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-top:20px}
.insight {background:#eaf3f1;border-left:3px solid #0d7772;padding:15px 17px;border-radius:5px;color:#315c57;font-size:14px;line-height:1.7;margin:10px 0}
.story {background:#fff;padding:18px 20px;border:1px solid #e5e9e6;border-radius:9px;min-height:135px}
.story .num {color:#0e7b76;font-size:12px;font-weight:800;letter-spacing:1px}
.story .txt {font-weight:700;color:#223d43;font-size:17px;margin-top:8px}
.story .desc {font-size:12px;color:#7a8582;margin-top:8px}
.v-note{background:#fff5ef;border:1px solid #f2d5c9;padding:11px 15px;color:#8c5946;border-radius:8px;font-size:12px}
hr {border-color:#e3e9e5!important}
@media (max-width:900px) {.block-container{padding:1.1rem}.hero{padding:20px}.hero h1{font-size:26px!important}}
</style>''', unsafe_allow_html=True)

required = ['01_normalized.csv','01_quality.json','03_audit.json']
if not all((OUT/f).exists() for f in required):
    st.error('找不到真實事故資料分析成果，請先執行三角色資料流程。本系統不使用假資料。')
    st.code('python scripts\\run_all.py\npython -m streamlit run app_v3.py',language='powershell')
    st.stop()

@st.cache_data(show_spinner=False)
def load():
    df=pd.read_csv(OUT/'01_normalized.csv',encoding='utf-8-sig',low_memory=False)
    q=json.loads((OUT/'01_quality.json').read_text(encoding='utf-8'))
    a=json.loads((OUT/'03_audit.json').read_text(encoding='utf-8'))
    for c in ('year','month','day','hour','lat','lon'):
        df[c]=pd.to_numeric(df[c],errors='coerce')
    for c in ('city','weather','cause','category','location'):
        df[c]=df[c].astype('string').fillna('未提供').replace({'nan':'未提供','<NA>':'未提供'})
    df['city']=df.city.str.replace('台','臺',regex=False)
    df['map_valid']=df.lat.between(21.5,25.5)&df.lon.between(119,123)
    return df,q,a

df,quality,audit=load()
if audit.get('status')!='PASS':
    st.error('Agent 3 尚未驗證通過。請檢查 outputs/03_audit.json，禁止使用未審查成功的資料。')
    st.stop()

st.markdown('''<div class="hero"><div class="eyebrow">SAFEROAD STUDIO  /  OPEN DATA EXPLORER</div>
<h1>每一個路口，都有一段數據故事。</h1>
<p>以台灣官方交通事故紀錄探索時空分布、事故集中區與道路情境。這是一個可驗證的歷史資料實驗室，而非即時導航或事故機率預測系統。</p></div>''',unsafe_allow_html=True)

all_years=sorted(df.year.dropna().astype(int).unique().tolist())
all_cities=sorted(x for x in df.city.dropna().unique().tolist() if x!='未提供')
all_categories=sorted(x for x in df.category.dropna().unique().tolist() if x!='未提供')
with st.sidebar:
    st.markdown('#### ◈ SafeRoad Studio')
    st.caption('資料查詢台｜所有頁籤共用篩選')
    selected_years=st.multiselect('年度',all_years,default=all_years)
    selected_cities=st.multiselect('縣市',all_cities,placeholder='全部縣市')
    selected_months=st.multiselect('月份',list(range(1,13)),placeholder='全年')
    selected_categories=st.multiselect('事故類別',all_categories,placeholder='全部類別')
    keyword=st.text_input('道路／路口文字搜尋',placeholder='例如 中正路、民族路')
    st.divider()
    st.markdown('**資料可追溯性**')
    st.caption('涵蓋年份：'+', '.join(map(str,all_years)))
    st.caption('資料來源：政府公開事故資料（原始下載檔保存在 data/raw）')
    st.caption('代理流程驗證：'+audit.get('status','未知'))
    st.caption('原始資料沒有可靠的唯一事故 ID，統計單位是「來源列數」，可能包含同案多位當事者。')
    st.divider()
    st.caption('開源資料探索 · 非事故即時警示 · 請勿作為急救／導航依據')

mask=df.year.isin(selected_years)
if selected_cities:mask &= df.city.isin(selected_cities)
if selected_months:mask &= df.month.isin(selected_months)
if selected_categories:mask &= df.category.isin(selected_categories)
if keyword:mask &= df.location.str.contains(keyword,regex=False,case=False,na=False)
f=df.loc[mask]
geo=f.loc[f.map_valid]

if len(f)==0:
    st.warning('目前篩選條件沒有紀錄，請調整縣市、年份或搜尋字詞。')
    st.stop()

valid_hours=f.hour.notna().sum()
peak_hour=int(f.hour.dropna().value_counts().idxmax()) if valid_hours else None
leader_city=str(f.city.value_counts().index[0]) if len(f) else '—'
sc=st.columns(4)
sc[0].metric('符合條件的來源列',f'{len(f):,}')
sc[1].metric('可定位紀錄',f'{len(geo):,}',f'{len(geo)/len(f):.1%} 有效座標')
sc[2].metric('紀錄最集中小時',f'{peak_hour:02d}:00' if peak_hour is not None else '未提供')
sc[3].metric('資料涵蓋年度',f'{f.year.nunique()} 年')
st.caption('來源列數 ≠ 獨立事故件數；當事者重複紀錄與年度資料涵蓋不完整可能影響比較。')

T0,T1,T2,T3,T4,T5=st.tabs(['◈ 全局總覽','◉ 事故地圖','▥ 時間解碼','≋ 道路探索','↗ 地區比較','✓ 方法與驗證'])

def plot_cfg(fig,height=340):
    fig.update_layout(template='plotly_white',height=height,margin=dict(l=10,r=10,t=20,b=20),
        font=dict(family='Noto Sans TC, Arial',color=INK,size=12),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(bgcolor='#fff',font_size=12))
    fig.update_xaxes(showgrid=False,zeroline=False)
    fig.update_yaxes(gridcolor='#edf0ee',zeroline=False)
    return fig

def chartbar(data,x,y,orientation='v',color=TEAL,height=330):
    fig=px.bar(data,x=x,y=y,orientation=orientation,color_discrete_sequence=[color])
    fig.update_traces(marker_line_width=0,hovertemplate='%{x}｜%{y}<extra></extra>')
    return plot_cfg(fig,height)

with T0:
    st.markdown('<div class="section-kicker">01 / INSIGHT BRIEFING</div>',unsafe_allow_html=True)
    st.subheader('先看懂這份資料')
    colA,colB,colC=st.columns(3)
    insights=[('01','時段分布',f'紀錄最集中的小時為 {peak_hour:02d}:00' if peak_hour is not None else '來源未提供足夠時間資料','只反映目前篩選的來源列數，不是通行事故率'),
              ('02','地區觀察',f'目前最多來源列的縣市是 {leader_city}','縣市交通量與資料涵蓋差異可能影響比較'),
              ('03','位置完整度',f'{len(geo)/len(f):.1%} 的篩選紀錄具有效座標','無效座標不參與地理分析')]
    for col,(num,head,statement,sub) in zip((colA,colB,colC),insights):
        with col:st.markdown(f'<div class="story"><div class="num">{num} / {head}</div><div class="txt">{statement}</div><div class="desc">{sub}</div></div>',unsafe_allow_html=True)
    l,r=st.columns([1.15,1])
    with l:
        st.subheader('年度紀錄趨勢')
        years=f.dropna(subset=['year']).groupby('year').size().reset_index(name='來源列數');years.year=years.year.astype(int).astype(str)
        fig=px.bar(years,x='year',y='來源列數',color_discrete_sequence=[TEAL]);st.plotly_chart(plot_cfg(fig,335),use_container_width=True)
        st.caption('不同年度可能是部分年度或不同資料涵蓋，不能直接推論事故真實增減。')
    with r:
        st.subheader('事故類別組成')
        cats=f.category.value_counts().head(8).reset_index();cats.columns=['事故類別','來源列數']
        fig=px.pie(cats,names='事故類別',values='來源列數',hole=.66,color_discrete_sequence=[TEAL,'#e7a078',BLUE,'#d9cfa6','#798c83','#d55d5a']);fig.update_traces(textinfo='percent',textposition='outside')
        st.plotly_chart(plot_cfg(fig,335),use_container_width=True)
    st.markdown('<div class="insight">試著篩選「桃園市」與「2024–2026」，再比較不同月份與時段。每個數字都會使用同一批官方來源列重新計算，而不是事先寫死的展示結果。</div>',unsafe_allow_html=True)

with T1:
    st.markdown('<div class="section-kicker">02 / GEOSPATIAL EXPLORER</div>',unsafe_allow_html=True)
    st.subheader('事故空間分布')
    c1,c2,c3=st.columns([1.1,1,1])
    with c1:map_mode=st.radio('呈現方式',['事故群聚','密度格網'],horizontal=True)
    with c2:maximum=st.select_slider('地圖點數上限（群聚模式）',options=[500,1000,2000,4000],value=2000)
    with c3:grid_scale=st.selectbox('格網精度',[(0.005,'約 0.5 公里'),(0.01,'約 1 公里'),(0.02,'約 2 公里')],format_func=lambda x:x[1],index=1)
    if len(geo):
        try:
            import folium
            from folium.plugins import FastMarkerCluster
            from streamlit_folium import st_folium
            map_sample=geo.sample(min(maximum,len(geo)),random_state=2026) if len(geo)>maximum else geo
            center=[float(geo.lat.median()),float(geo.lon.median())]
            fmap=folium.Map(location=center,zoom_start=10,tiles='OpenStreetMap',control_scale=True,prefer_canvas=True)
            if map_mode=='密度格網':
                step=grid_scale[0]
                g=geo.assign(y=np.floor(geo.lat/step)*step,x=np.floor(geo.lon/step)*step).groupby(['y','x']).size().reset_index(name='n')
                maxn=max(float(g.n.quantile(.98)),1.)
                for rec in g.itertuples(index=False):
                    n=int(rec.n);t=min(n/maxn,1)
                    clr='#2b8b84' if t<.2 else '#e4a251' if t<.5 else '#e16a51' if t<.8 else '#ad3439'
                    folium.Rectangle([[rec.y,rec.x],[rec.y+step,rec.x+step]],color='#ffffff',weight=.7,
                        fill=True,fill_color=clr,fill_opacity=.27+.5*t,tooltip=f'歷史來源列 {n:,} 筆').add_to(fmap)
                st.caption(f'格網依目前 {len(geo):,} 筆有效座標的紀錄計算，邊線為分析網格，不是行政區界。')
            else:
                FastMarkerCluster(map_sample[['lat','lon']].values.tolist(),options={'maxClusterRadius':55}).add_to(fmap)
                st.caption(f'群聚顯示固定抽樣 {len(map_sample):,}／{len(geo):,} 筆，完整統計仍使用所有符合條件的紀錄。')
            boundary=ROOT/'data'/'boundaries'/'townships.geojson'
            if boundary.exists():
                folium.GeoJson(str(boundary),name='真實行政區界',style_function=lambda _:dict(fillOpacity=0,color='#1c618a',weight=1.4)).add_to(fmap)
                folium.LayerControl().add_to(fmap)
            st_folium(fmap,height=520,use_container_width=True,returned_objects=[])
        except Exception as exc:
            st.warning(f'地圖組件載入失敗：{exc}，下方統計表仍可使用。')
        st.subheader('事故集中網格 TOP 10')
        g=geo.assign(lat_grid=(np.floor(geo.lat/.01)*.01).round(3),lon_grid=(np.floor(geo.lon/.01)*.01).round(3))
        rank=g.groupby(['lat_grid','lon_grid']).size().nlargest(10).reset_index(name='來源列數')
        rank=rank.rename(columns={'lat_grid':'緯度起點','lon_grid':'經度起點'})
        st.dataframe(rank,use_container_width=True,hide_index=True)
        st.caption('固定 0.01° 格網；不等同於道路安全評分。')
    else:st.info('目前篩選沒有有效座標。')

with T2:
    st.markdown('<div class="section-kicker">03 / TEMPORAL PATTERNS</div>',unsafe_allow_html=True)
    st.subheader('什麼時候的事故紀錄較集中？')
    hourly=f.hour.dropna().astype(int).value_counts().reindex(range(24),fill_value=0).reset_index();hourly.columns=['小時','來源列數']
    fig=px.area(hourly,x='小時',y='來源列數',markers=True,color_discrete_sequence=[TEAL]);fig.update_traces(fillcolor='rgba(13,119,114,.16)',line_width=2)
    fig.update_xaxes(dtick=2)
    st.plotly_chart(plot_cfg(fig,340),use_container_width=True)
    a,b=st.columns([1.2,1])
    with a:
        st.subheader('年 × 月時序熱力圖')
        tmp=f.dropna(subset=['year','month']).copy()
        if len(tmp):
            tmp['year']=tmp.year.astype(int);tmp['month']=tmp.month.astype(int)
            pivot=tmp.groupby(['year','month']).size().unstack(fill_value=0).reindex(columns=range(1,13),fill_value=0).sort_index()
            fig=go.Figure(go.Heatmap(z=pivot.values,x=[f'{i}月' for i in pivot.columns],y=[str(i) for i in pivot.index],colorscale=[[0,'#edf4f1'],[.5,'#75aaa1'],[1,'#0b716c']],hovertemplate='年份 %{y}<br>%{x}<br>來源列 %{z:,}<extra></extra>'))
            st.plotly_chart(plot_cfg(fig,320),use_container_width=True)
        else:st.info('缺少可用的年月資料')
    with b:
        st.subheader('天候條件')
        d=f.weather.value_counts().head(9).sort_values().reset_index();d.columns=['天候','來源列數']
        st.plotly_chart(chartbar(d,'來源列數','天候','h',BLUE,320),use_container_width=True)
    st.markdown('<div class="v-note">注意：雨天事故「件數較少」不等於「雨天更安全」。要比較相對風險，需取得各天候的交通流量或用路時間等暴露量。</div>',unsafe_allow_html=True)

with T3:
    st.markdown('<div class="section-kicker">04 / STREET-LEVEL EXPLORATION</div>',unsafe_allow_html=True)
    st.subheader('從一條道路開始探索')
    st.caption('先在左側輸入路名；也可以直接檢視目前篩選下出現頻繁的地點文字。此工具是歷史紀錄查詢，不是道路風險預測。')
    a,b=st.columns([1.3,1])
    with a:
        st.subheader('熱門事故地點（文字完全相同）')
        d=f.location.value_counts().head(15).reset_index();d.columns=['事故地點','來源列數']
        st.dataframe(d,use_container_width=True,hide_index=True,height=470)
    with b:
        st.subheader('來源肇因分類')
        d=f.cause.value_counts().head(12).sort_values().reset_index();d.columns=['肇因文字','來源列數']
        st.plotly_chart(chartbar(d,'來源列數','肇因文字','h',ACCENT,465),use_container_width=True)
    st.subheader('地點紀錄搜尋結果')
    keep=['year','month','day','hour','city','location','weather','category','cause']
    top=f[keep].copy().head(100)
    st.dataframe(top,use_container_width=True,hide_index=True)
    st.caption('相同地點字串可能描述不同的里程或方向；本版不自動合併為同一事故，也不提供實時道路警告。')

with T4:
    st.markdown('<div class="section-kicker">05 / COMPARATIVE EXPLORER</div>',unsafe_allow_html=True)
    st.subheader('縣市與年度比較')
    city_ct=f.city.value_counts().head(15).sort_values().reset_index();city_ct.columns=['縣市','來源列數']
    st.plotly_chart(chartbar(city_ct,'來源列數','縣市','h',TEAL,440),use_container_width=True)
    st.caption('這是來源列數排行，未經人口、車流量或道路里程標準化，不表示事故率排名。')
    if f.year.nunique()>1:
        st.subheader('各縣市分年度紀錄')
        group=f.dropna(subset=['year']).copy();group['year']=group.year.astype(int).astype(str)
        hottest=f.city.value_counts().head(8).index.tolist();group=group[group.city.isin(hottest)]
        pivot=group.groupby(['city','year']).size().reset_index(name='來源列數')
        fig=px.bar(pivot,x='city',y='來源列數',color='year',barmode='group',color_discrete_sequence=[TEAL,ACCENT,BLUE,'#aaa28b'])
        st.plotly_chart(plot_cfg(fig,390),use_container_width=True)
        st.markdown('<div class="v-note">比較前請先核對每個年度收錄的月份。2026 可能尚未完整結束，不應以年度總數直接判斷事故改善幅度。</div>',unsafe_allow_html=True)

with T5:
    st.markdown('<div class="section-kicker">06 / TRANSPARENCY & QUALITY</div>',unsafe_allow_html=True)
    st.subheader('每個數字都有來處')
    c1,c2,c3=st.columns(3)
    c1.metric('Inspector｜匯入來源列',f"{quality.get('input_rows',0):,}")
    c2.metric('Analyst｜正規化列',f"{quality.get('normalized_rows',0):,}")
    c3.metric('Auditor｜品質檢核',audit.get('status','UNKNOWN'))
    st.markdown('**流程**：官方原始檔 → Agent 1 檢查欄位與座標 → Agent 2 統計與地圖 → Agent 3 獨立核對 → Dashboard')
    l,r=st.columns(2)
    with l:
        with st.expander('Agent 1 · 資料檢查與來源紀錄',expanded=False):st.json(quality)
    with r:
        with st.expander('Agent 3 · 獨立數值驗證',expanded=False):st.json(audit)
    st.divider()
    st.subheader('下載結果與重現')
    st.download_button('下載目前篩選 CSV',f.to_csv(index=False).encode('utf-8-sig'),file_name='saferoad_studio_filtered.csv',mime='text/csv',type='primary')
    st.caption('下載的是正規化資料列，非警方原始檔案；可用 scripts/run_all.py 從 data/raw 重新生成。')
    st.markdown('**分析限制**：無法憑此資料確認傷者是否送醫、實際送往醫院、即時道路安全，或個別通行事故機率。')
    st.markdown('官方來源：[A1 事故資料](https://data.gov.tw/dataset/57023) ｜ [A2 事故資料](https://data.gov.tw/dataset/57024) ｜ [114 年事故資料](https://data.gov.tw/dataset/177136)')

st.markdown('<div class="smallprint" style="margin-top:30px;border-top:1px solid #dfe5e1;padding-top:15px">SAFEROAD STUDIO · Historical data intelligence · Government Open Data · Verifiable three-stage workflow</div>',unsafe_allow_html=True)
