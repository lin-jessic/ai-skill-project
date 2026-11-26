"""OpenShop Life Studio. File-first three-agent demonstration, business sandbox."""
from __future__ import annotations
import io,json,zipfile
from datetime import date
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scripts.logic import ROOT
from scripts.studio_engine import (STORE_CATALOG,FOOD,LEGAL_LINKS,parse_upload,create_artifacts,
                                  daily_simulation,save_artifacts,rank_places,play_one_day,DECISIONS)

st.set_page_config(page_title='OpenShop LIFE | 開店人生',page_icon='🏙️',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
:root{--coffee:#342d3a;--plum:#734d82;--berry:#df7894;--cream:#fff9f0;--mint:#92d5b9;--yellow:#ffd78d}
html,body,[class*="css"]{font-family:'Nunito','Noto Sans TC',sans-serif}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 85% 8%,#fce8df 0,transparent 36%),radial-gradient(ellipse at 15% 28%,#edf4e9 0,transparent 38%),#fffaf5;color:#332d37}
[data-testid="stSidebar"]{background:#f5eaf0;border-right:1px solid #eadbe5}
.block-container{padding-top:1.25rem;max-width:1600px;padding-bottom:3rem}
.hero{background:linear-gradient(116deg,#534064 0%,#84618f 57%,#bd87aa 100%);border-radius:26px;padding:30px 34px;color:#fff;box-shadow:0 18px 40px #342d3a22;position:relative;overflow:hidden}
.hero:after{content:'✦   ✳   ✦';position:absolute;right:34px;top:16px;color:#ffffff50;font-size:42px;letter-spacing:16px;transform:rotate(-14deg)}
.hero h1{font-size:2.5rem;margin:0 0 9px;font-weight:900;letter-spacing:-.04em}.hero p{font-size:1.05rem;color:#fceff5;max-width:730px;margin:0}
.kicker{letter-spacing:.21em;font-size:.75rem;font-weight:900;opacity:.84;margin-bottom:12px}
.smallpill{display:inline-block;padding:5px 12px;border-radius:40px;background:#ffffff22;color:white;font-size:.8rem;margin-top:15px}
.step{padding:16px;border-radius:18px;background:#fff;border:1px solid #eee3e8;min-height:110px;box-shadow:0 8px 25px #3e30500a}
.step b{color:#62466f}.step p{font-size:.86rem;color:#766b7c;margin:6px 0}
.module-header{font-size:1.5rem;font-weight:900;color:#4e3a59;margin:12px 0}
.note{border-left:4px solid #c884a6;background:#fff1f4;border-radius:9px;padding:12px;color:#69516a;font-size:.88rem}
div[data-testid="stMetric"]{border-radius:18px;padding:17px 18px;background:white;border:1px solid #efdfeb;box-shadow:0 12px 35px #4f2f550b}
[data-testid="stMetricLabel"]{color:#816e83}[data-testid="stMetricValue"]{color:#493553}
.stButton>button[kind="primary"]{background:#754f85;border:0;border-radius:13px;font-weight:800}
.stButton>button{border-radius:12px;font-weight:800}
.stTabs [data-baseweb="tab-list"]{gap:6px;flex-wrap:wrap;background:#fff7f7;padding:9px;border-radius:18px}
.stTabs [data-baseweb="tab"]{border-radius:10px;padding:10px 17px;color:#695570;font-weight:800}
.stTabs [aria-selected="true"]{background:#795a87;color:white}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:#eee0ea;border-radius:18px}
</style>''',unsafe_allow_html=True)

MONEY=lambda n:f'NT$ {n:,.0f}'
def fig_style(fig,height=360):
    fig.update_layout(height=height,margin=dict(l=20,r=20,t=38,b=25),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(family='Noto Sans TC',color='#514357'),legend=dict(orientation='h',y=-.22))
    return fig

def format_json(x):return json.dumps(x,ensure_ascii=False,indent=2)
def read_demo():
    p=ROOT/'examples'/'DEMO_商圈資料_情境假設_非官方.csv'
    b=p.read_bytes();return parse_upload(b,p.name),b

if 'df' not in st.session_state:st.session_state.df=None
if 'quality' not in st.session_state:st.session_state.quality=None
if 'raw_uploaded' not in st.session_state:st.session_state.raw_uploaded=None
if 'run' not in st.session_state:st.session_state.run=None
if 'daily' not in st.session_state:st.session_state.daily=None

with st.sidebar:
    st.markdown('### 🏡 OPENSHOP LIFE')
    st.caption('MY FIRST STORE • TAIWAN EDITION')
    st.markdown('#### 🧩 建立你的店鋪')
    category=st.selectbox('產業分類',['餐飲','零售','服務'])
    choices=[name for name,(kind,*_) in STORE_CATALOG.items() if kind==category]
    shop=st.selectbox('店鋪類型',choices)
    city=st.selectbox('開店縣市',['桃園市','臺北市','新北市','臺中市','臺南市','高雄市','新竹市','新竹縣','基隆市','苗栗縣','彰化縣','宜蘭縣','花蓮縣','嘉義市','嘉義縣','屏東縣','南投縣','雲林縣','臺東縣','澎湖縣','金門縣','連江縣'])
    district=st.text_input('行政區或商圈','中壢區')
    floor_area=st.number_input('預估坪數（坪）',min_value=1,max_value=600,value=20)
    budget=st.number_input('創業資金（NT$）',min_value=10000,max_value=100000000,step=50000,value=800000)
    launch=st.date_input('目標開幕日期',value=date(2027,3,1))
    st.markdown('---')
    st.markdown('#### 📊 經營假設')
    _,icon,default_price,default_variable,default_daily=STORE_CATALOG[shop]
    price=st.number_input('每筆平均交易金額',min_value=1,max_value=100000,value=default_price,step=5)
    variable=st.number_input('每筆直接成本',min_value=0,max_value=100000,value=default_variable,step=5)
    daily=st.slider('平日預計交易筆數',min_value=0,max_value=500,value=default_daily,step=5)
    rent=st.number_input('每月租金',min_value=0,max_value=2000000,value=38000,step=1000)
    payroll=st.number_input('每月人事總成本（自訂）',min_value=0,max_value=2000000,value=85000,step=5000)
    fixed_other=st.number_input('每月其他固定費用',min_value=0,max_value=2000000,value=18000,step=1000)
    days=st.slider('每月營業天數',min_value=1,max_value=31,value=26)
    delivery=st.slider('外送訂單比例（情境假設）',0,100,20,5)
    dinein=st.slider('內用訂單比例（情境假設）',0,100,30,5)
    commission=st.slider('平台費率（自行確認後填入）',0,50,30,1)
    package=st.number_input('每份外送額外包材成本',min_value=0,max_value=1000,value=5)
    st.caption('所有預設售價、訂單數、人事費、租金皆是**教學假設**，不是市場調查數據。')

if dinein+delivery>100:
    st.error('內用與外送比例合計超過 100%。請在左側修正，外帶比例才可正確計算。')
    st.stop()

config={'shop':shop,'city':city,'district':district,'floor_area_sqm':round(floor_area*3.305785,2),
        'budget':budget,'price':price,'variable':variable,'daily':daily,'rent':rent,
        'payroll':payroll,'fixed_other':fixed_other,'days':days,'delivery_share':delivery/100,
        'dinein_share':dinein/100,'commission':commission/100,'delivery_packaging':package,
        'opening_target_date':str(launch),'fitout':150000,'equipment':120000,'reserve':150000}

st.markdown(f'''<div class="hero"><div class="kicker">OPENSHOP LIFE / TAIWAN BUSINESS SANDBOX</div>
<h1>🏙️ 你的開店人生，現在開始。</h1><p>選一個產業、匯入一份真實資料，讓三位專業角色陪你挑商圈、檢視合法條件，再把店經營到第 30 天。</p>
<span class="smallpill">{icon} {shop}　·　📍 {city}{district}　·　🧪 情境模擬 × 證據審查</span></div>''',unsafe_allow_html=True)
st.write('')
cols=st.columns(3)
for col,letter,title,desc in zip(cols,['01','02','03'],['MARKET / 市場分析','LEGAL / 法規合規','OPEN / 開店程序與審查'],
                                  ['資料上傳、競爭密度、商圈排行','土地、消防、食安、勞動等逐項確認','開辦資金、排程、每日經營與稽核']):
    with col:st.markdown(f'<div class="step"><b>AGENT {letter} · {title}</b><p>{desc}</p></div>',unsafe_allow_html=True)
st.write('')
tabs=st.tabs(['📤 01 資料挑戰','🏆 02 商圈 PK','📜 03 法規通關','🪑 04 店面策略','🎮 05 每日經營','📈 06 老闆財務','📦 07 報告／測試'])

with tabs[0]:
    st.markdown('<div class="module-header">📤 老師丟一個檔案，就開始實戰</div>',unsafe_allow_html=True)
    st.markdown('先匯入 **CSV 或 JSON** 的候選商圈資料；程式檢查欄位、缺值、重複和數值，再交給市場→法規→程序三位角色。')
    sample=(ROOT/'examples'/'DEMO_商圈資料_情境假設_非官方.csv').read_bytes()
    st.download_button('⬇️ 下載資料格式範例（明確標記非官方）',sample,'DEMO_商圈資料_情境假設_非官方.csv','text/csv')
    file=st.file_uploader('將教授提供的檔案放進來',type=['csv','json'],help='CSV/JSON；必須有 district, population, competitors, footfall, rent 欄位')
    b1,b2=st.columns([1,1])
    with b1:
        if st.button('✨ 使用教學範例載入（模擬資料）',use_container_width=True):
            (frame,quality),_ = read_demo();st.session_state.df=frame;st.session_state.quality=quality;st.session_state.raw_uploaded=sample;st.session_state.run=None
    with b2:
        if file is not None and st.button('📄 驗證並匯入上傳檔案',type='primary',use_container_width=True):
            try:
                raw=file.getvalue();frame,q=parse_upload(raw,file.name)
                st.session_state.df=frame;st.session_state.quality=q;st.session_state.raw_uploaded=raw;st.session_state.run=None
                st.success(f'成功匯入 {len(frame)} 個候選地點，未修改或虛構原始數值。')
            except Exception as e:st.error(f'匯入失敗：{e}')
    if st.session_state.df is not None:
        q=st.session_state.quality;df=st.session_state.df
        st.info('資料已就緒：'+q['filename']+'｜'+str(q['rows'])+' 筆｜SHA-256 '+q['sha256'][:16]+'…')
        for w in q['warnings']:st.caption('⚠ '+w)
        st.dataframe(df,use_container_width=True,hide_index=True)
        if st.button('🚀 開始三角色完整審查',type='primary',use_container_width=True):
            artifacts=create_artifacts(config,df,q)
            st.session_state.run=artifacts
            save_artifacts(ROOT/'outputs'/'studio_latest',artifacts)
            st.success('已完成市場 → 法規 → 開店程序／稽核；報告儲存在 outputs/studio_latest。')
            st.rerun()
    else:st.warning('尚未匯入商圈資料，後續排名不會顯示假裝是真實的結果。')

with tabs[1]:
    st.markdown('<div class="module-header">🏆 商圈 PK｜你會在哪裡開店？</div>',unsafe_allow_html=True)
    if st.session_state.df is None:
        st.info('先到「資料挑戰」上傳地區資料，才會顯示排名。')
    else:
        weights=st.slider('人口吸引力權重 (%)｜交通比重自動補足',10,65,40)
        foot=st.slider('交通指標權重 (%)',10,70,35)
        remain=100-weights-foot
        if remain<0:st.warning('權重合計須低於 100%，剩餘部分會分給競爭與租金。')
        else:
            ranking=rank_places(st.session_state.df,(weights/100,foot/100,remain/100))
            winner=ranking.iloc[0]
            a,b,c=st.columns(3)
            a.metric('🥇 目前領先地點',winner['district'])
            b.metric('相對情境分數',f"{winner['情境分數']:.1f} / 100")
            c.metric('參賽商圈數',len(ranking))
            fig=px.bar(ranking,x='情境分數',y='district',orientation='h',color='情境分數',color_continuous_scale=['#f8d2a0','#e5a0af','#785c99'],text='情境分數')
            fig.update_traces(texttemplate='%{text:.1f}',textposition='outside');fig.update_yaxes(autorange='reversed');fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_style(fig,360),use_container_width=True)
            st.dataframe(ranking[['district','population','competitors','footfall','rent','情境分數','data_source']],hide_index=True,use_container_width=True)
            st.caption('分數是相對正規化與使用者設定權重的啟發式比較，不是獲利機率或官方認證排名。')

with tabs[2]:
    st.markdown('<div class="module-header">📜 法規通關｜開店前還缺什麼？</div>',unsafe_allow_html=True)
    st.markdown('<div class="note">每一關預設「待主管機關核實」。勾選代表完成自我檢查，並不代表官方已核發許可；實際要求依地址、樓層、規模與營業態樣判定。</div>',unsafe_allow_html=True)
    run=st.session_state.run
    items=run[1]['items'] if run else []
    if not items:
        items=create_artifacts(config,None,{} )[1]['items']
    completion=0
    for i,item in enumerate(items):
        with st.expander(f"{'🟠' if item['risk']=='high' else '🟡'} {item['item']} · {item['risk'].upper()}",expanded=i==0):
            checked=st.checkbox('已自行核對相關資料／準備文件',key=f"check_{shop}_{i}")
            completion+=int(checked)
            st.write(item['action_required'])
            st.caption('窗口：'+item['authority']+'｜狀態：仍須個案確認')
            st.link_button('↗ 官方查核入口',item['source'])
    st.progress(completion/max(1,len(items)),text=f'自我檢核進度：{completion}/{len(items)}，非正式核准進度')
    st.markdown('#### 🧤 員工與設備任務')
    tasks=['確認進貨與設備來源','做好庫存與交班記錄','建立職安與清潔程序','確認人員薪資、保險及工時']
    if shop in FOOD:tasks+=['核對冷鏈保存條件','食品衛生、交叉污染防治與清潔','食品標示及過敏原提示']
    if category=='服務':tasks+=['專業資格、消毒及設備安全查核']
    for i,t in enumerate(tasks):st.checkbox(t,key=f'ops_{shop}_{i}')

with tabs[3]:
    st.markdown('<div class="module-header">🪑 店面策略｜內用、外帶與外送實驗室</div>',unsafe_allow_html=True)
    st.info('比例由你在側邊欄設定。這裡是營運配置模擬，不是當地消費者偏好的實測調查。')
    takeaway=100-dinein-delivery
    x,y=st.columns([1,1])
    with x:
        fig=px.pie(names=['內用','外帶','外送'],values=[dinein,takeaway,delivery],hole=.66,color_discrete_sequence=['#a5dfc1','#f5c882','#c899cb'])
        fig.update_traces(textinfo='label+percent',textfont_size=14)
        st.plotly_chart(fig_style(fig,345),use_container_width=True)
    with y:
        st.markdown('#### 店面配置提示（情境）')
        st.metric('內用訂單比例',f'{dinein}%')
        st.metric('外帶訂單比例',f'{takeaway}%')
        st.metric('外送訂單比例',f'{delivery}%')
        st.write('內用比重高：先確認座位、廁所、動線與場地用途；外帶比重高：重視取餐窗口與尖峰動線；外送比重高：檢查外送包材、流程和實際平台費率。')
        st.caption('未取得平台店家密度及區域訂單公開資料，不展示虛構平台需求排行。')

with tabs[4]:
    st.markdown('<div class="module-header">🎮 開店第 1 天 → 第 30 天｜你的營運日誌</div>',unsafe_allow_html=True)
    st.markdown('模擬市民式的經營遊戲：事件會改變來客量，但**整個日誌是由參數與固定亂數種子生成的模擬，不是真實商店歷史**。')
    x,y,z=st.columns(3)
    with x:seed=st.number_input('劇本種子（同種子可重現）',min_value=0,max_value=99999,value=42)
    with y:duration=st.slider('模擬營運天數',7,120,30)
    with z:use_events=st.toggle('啟用隨機事件',value=True)
    if st.button('▶ 開始營業 / 重新模擬',type='primary',use_container_width=True):
        st.session_state.daily=daily_simulation(config,seed,duration,use_events)
    if st.session_state.daily is not None:
        d=st.session_state.daily.copy()
        a,b,c,dcol=st.columns(4)
        a.metric('模擬總訂單',f"{d.orders.sum():,}")
        b.metric('模擬總營收',MONEY(d.revenue.sum()))
        c.metric('模擬總損益',MONEY(d.profit.sum()))
        dcol.metric('最終預估現金',MONEY(d.cash.iloc[-1]))
        fig=go.Figure()
        fig.add_scatter(x=d.day,y=d.cash,mode='lines+markers',line=dict(color='#8b64a0',width=3),name='現金餘額')
        st.plotly_chart(fig_style(fig,350),use_container_width=True)
        fig2=px.bar(d,x='day',y='profit',color='event',title='每日模擬損益與特殊事件')
        st.plotly_chart(fig_style(fig2,310),use_container_width=True)
        selected=st.slider('🔎 查看第幾天日誌',1,len(d),min(3,len(d)))
        r=d.iloc[selected-1]
        st.success(f"📅 Day {selected} · {r['date']}｜{r['event']}｜{r['orders']} 筆交易｜當日損益 {MONEY(r['profit'])}")
        st.dataframe(d,hide_index=True,use_container_width=True)
        st.download_button('下載模擬營運日誌 CSV',d.to_csv(index=False).encode('utf-8-sig'),'daily_simulation_SYNTHETIC.csv','text/csv')
    else:st.caption('按下「開始營業」即可展開你的第一個月。')

    st.markdown('#### 🕹️ 經營決策回合｜一天一天經營')
    choice=st.selectbox('今天老闆要做什麼？',list(DECISIONS),format_func=lambda x:x+'｜'+DECISIONS[x]['description'])
    left,right=st.columns(2)
    with left:
        if st.button('🌞 開始下一個營業日',type='primary',use_container_width=True):
            try:
                st.session_state.turns=play_one_day(config,st.session_state.get('turns',[]),choice,int(seed))
            except Exception as e:st.error(str(e))
    with right:
        if st.button('↻ 重新開店（清空回合）',use_container_width=True):st.session_state.turns=[]
    if st.session_state.get('turns'):
        history=pd.DataFrame(st.session_state.turns);last=history.iloc[-1]
        st.success(f"Day {int(last['day'])}｜{last['event']}｜決策：{last['decision']}｜本日盈虧 {MONEY(last['profit'])}｜剩餘資金 {MONEY(last['cash'])}")
        st.plotly_chart(fig_style(px.line(history,x='day',y='cash',markers=True,title='你的逐日決策現金曲線'),260),use_container_width=True)
        st.dataframe(history,hide_index=True,use_container_width=True)
        st.download_button('下載逐日決策紀錄（模擬）',history.to_csv(index=False).encode('utf-8-sig'),'turn_based_decisions_SYNTHETIC.csv','text/csv')

with tabs[5]:
    st.markdown('<div class="module-header">📈 老闆財務室｜今天這個決定賺錢嗎？</div>',unsafe_allow_html=True)
    artifacts=create_artifacts(config,st.session_state.df,st.session_state.quality)
    sim=artifacts[4];a,b,c,d=st.columns(4)
    a.metric('每月預估營收',MONEY(sim['revenue']))
    b.metric('每月簡化成本',MONEY(sim['monthly_cost']))
    c.metric('每月簡化損益',MONEY(sim['monthly_profit']))
    d.metric('每日損益兩平',f"{sim['breakeven_daily']} 筆" if sim['breakeven_daily'] is not None else '無法達成')
    revenue_data=pd.DataFrame([{'項目':'營收','金額':sim['revenue']},{'項目':'原料與直接成本','金額':sim['variable_cost']},
        {'項目':'固定成本','金額':sim['fixed_cost']},{'項目':'外送平台費','金額':sim['delivery_fee']},
        {'項目':'外送包材','金額':sim['packaging']}])
    st.plotly_chart(fig_style(px.bar(revenue_data,x='項目',y='金額',color='項目',color_discrete_sequence=['#a6d7b9','#d3a0cd','#ffe2ad','#ec9b99','#9bb9e5']),330),use_container_width=True)
    col1,col2=st.columns(2)
    with col1:
        st.markdown('#### 訂單量敏感度（同一組成本假設）')
        rows=[]
        for n in range(max(0,daily-60),daily+65,15):
            cfg=dict(config);cfg['daily']=n
            s=create_artifacts(cfg,None,{} )[4]
            rows.append({'每日交易筆數':n,'月損益':s['monthly_profit']})
        chart=px.line(pd.DataFrame(rows),x='每日交易筆數',y='月損益',markers=True)
        st.plotly_chart(fig_style(chart,290),use_container_width=True)
    with col2:
        st.markdown('#### 假設與資金風險')
        st.write('每月營業天數：',days)
        st.write('平均每單貢獻：',MONEY(sim['contribution_per_order']))
        st.write('簡化資金可支撐月份：',f"{sim['runway_months']} 個月" if sim['runway_months'] is not None else '目前情境不虧損（不代表現金無風險）')
        st.caption('啟動裝潢、押金、設備、稅負、折舊、負債、業主薪資及許可等另須核算。此頁是情境工具，非營收預測。')

with tabs[6]:
    st.markdown('<div class="module-header">📦 驗收控制台｜每個角色產出一份可查核證據</div>',unsafe_allow_html=True)
    if st.session_state.run is None:
        st.warning('先到「資料挑戰」匯入檔案並按「開始三角色完整審查」，才能產生真正的本次執行紀錄。')
    else:
        market,legal,plan,audit,sim,ranked=st.session_state.run
        cols=st.columns(3)
        for col,name,label,obj in zip(cols,['01_market_report.json','02_legal_checklist.json','03_store_opening_plan.md'],
                                     ['Agent 1 · 市場','Agent 2 · 合規','Agent 3 · 程序稽核'],[market,legal,plan]):
            with col:
                with st.container(border=True):
                    st.markdown(f'**{label}**')
                    st.caption(name)
                    st.download_button('下載階段成果',format_json(obj) if isinstance(obj,dict) else obj,name,'application/json' if isinstance(obj,dict) else 'text/markdown',key=name)
        st.markdown(f"**審查狀態：{audit['status'].upper()}** · 人工確認仍有 {len(audit['issues'])} 項事項")
        st.json(audit)
        all_files={'01_market_report.json':format_json(market),'02_legal_checklist.json':format_json(legal),
                   '03_store_opening_plan.md':plan,'04_audit.json':format_json(audit),'05_finance.json':format_json(sim)}
        if not ranked.empty:all_files['06_location_ranking.csv']=ranked.to_csv(index=False)
        if st.session_state.daily is not None:all_files['07_daily_simulation_SYNTHETIC.csv']=st.session_state.daily.to_csv(index=False)
        f=io.BytesIO()
        with zipfile.ZipFile(f,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for name,contents in all_files.items():z.writestr(name,contents.encode('utf-8-sig') if name.endswith('.csv') else contents.encode('utf-8'))
        st.download_button('📦 一次下載完整成果 ZIP',f.getvalue(),'OpenShop_AI_three_agent_outputs.zip','application/zip',type='primary')
    with st.expander('🧪 教授 Skill 啟動 A／B／C 測試（需在真正載入 Skill 的 AI 環境執行）'):
        st.markdown('**A 必須啟動：**「我要在桃園開手搖飲店，請比較商圈、法規、開店流程。」\n\n**B 改寫仍須啟動：**「手上有 80 萬，想租一間咖啡店，不知道客群、證照和準備順序。」\n\n**C 不應啟動：**「幫我寫一篇貓咪的生日祝福文。」')
        st.warning('網站執行 Python 三階段工作流程 ≠ AI 模型已自動識別、載入 Skill。正式作業必須另錄 AI 工具自動啟動證據，且不可將人工選單操作冒充自動觸發。')
    st.markdown('#### 資料與法規追溯')
    for label,url in LEGAL_LINKS.items():st.markdown(f'- [{label}]({url})')
    st.caption('只使用官方入口。個別店址、營業型態、勞動條件需最新主管機關個案確認。')
