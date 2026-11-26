"""OpenShop AI v2. Official-data-only analytics; editable simulation assumptions."""
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scripts.logic import (ROOT,RAW,OUT,SOURCES,CITIES,SHOP_TYPES,FOOD,availability,read_any,population_summary,metro_summary,industry_summary,tax_competitors,count_tax_zip_by_city,legal_checklist,operations_plan,money_sim,build_report)

st.set_page_config(page_title='OpenShop Studio | 創業實驗室',page_icon='◈',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
:root{--ink:#18303a;--teal:#0b716c} html,body,[data-testid="stAppViewContainer"]{font-family:'DM Sans','Noto Sans TC',sans-serif}
[data-testid="stAppViewContainer"]{background:#f5f7f7;color:#172d35}
[data-testid="stSidebar"]{background:#eaf0ef}
.block-container{padding-top:2rem;max-width:1450px}
.brand{font-size:.85rem;font-weight:700;letter-spacing:.14em;color:#13766d}.hero{font-size:2.55rem;font-weight:700;line-height:1.18;letter-spacing:-.04em;color:#173039;margin:.5rem 0}
.sub{color:#627a81;font-size:1rem;line-height:1.7}.note{padding:.8rem 1rem;background:#e5efec;border-left:3px solid #15746d;border-radius:4px;font-size:.85rem;color:#2e595a}
.eyebrow{font-size:.76rem;letter-spacing:.1em;text-transform:uppercase;color:#61837e;font-weight:700}
div[data-testid="stMetric"]{background:white;border:1px solid #e0e9e7;border-radius:14px;padding:13px 18px;box-shadow:0 8px 25px #173e3b08}
div[data-testid="stVerticalBlockBorderWrapper"]{border-color:#e0e8e6}
.stButton>button[kind="primary"]{background:#126d67;border:0}
</style>''',unsafe_allow_html=True)

def nice(n):return f'{n:,.0f}' if n is not None else '—'

def heading(index,title,sub):st.markdown(f'<div class="eyebrow">{index} / OPENSHOP LAB</div><h2 style="margin:4px 0 8px">{title}</h2><p class="sub">{sub}</p>',unsafe_allow_html=True)

@st.cache_data(show_spinner=False,ttl=1800)
def get_source(key):
    path=RAW/SOURCES[key]['file']
    if not path.exists():return pd.DataFrame(),f'尚未下載：{path.relative_to(ROOT)}'
    try:return read_any(path),None
    except Exception as e:return pd.DataFrame(),f'無法讀取 {path.name}：{e}'

status=availability()
with st.sidebar:
    st.markdown('<div class="brand">◈ OPENSHOP / STUDIO</div>',unsafe_allow_html=True)
    st.caption('TAIWAN BUSINESS INTELLIGENCE · v2')
    st.divider()
    shop=st.selectbox('創業店型',SHOP_TYPES,index=0)
    city=st.selectbox('預計設立縣市',CITIES,index=CITIES.index('桃園市'))
    budget=st.number_input('初期可運用資金 NT$',min_value=0,max_value=100000000,value=800000,step=50000)
    st.divider()
    view=st.radio('工作空間',['01  /  創業總覽','02  /  法規與員工','03  /  商圈與競爭','04  /  外送與消費模式','05  /  財務決策實驗室','06  /  報告與驗證'],label_visibility='collapsed')
    st.divider()
    st.caption(f'官方資料已就緒：{sum(i["present"] for i in status.values())} / {len(status)} 組')
    st.caption('無實際來源的數據一律不補假值')

if 'sim' not in st.session_state:
    st.session_state.sim={'price':65,'variable':25,'daily':100,'rent':35000,'payroll':75000,'fixed_other':20000,'days':26,'dinein_share':0.2,'delivery_share':0.25,'commission':0.3,'delivery_packaging':4}

st.markdown('<div class="brand">OPENSHOP AI  /  ENTREPRENEURSHIP INTELLIGENCE</div>',unsafe_allow_html=True)
st.markdown('<div class="hero">你的第一間店，開得起來嗎？</div>',unsafe_allow_html=True)
st.markdown(f'<div class="sub">{city} · {shop} · 合規 × 商圈 × 營運 × 財務｜真實官方資料與使用者假設分開呈現</div>',unsafe_allow_html=True)
st.write('')

if view.startswith('01'):
    heading('01','創業控制台','先看完整資料狀態，再開始你自己的開店情境。')
    a,b,c,d=st.columns(4)
    a.metric('創業啟動資金',f'NT$ {nice(budget)}')
    b.metric('已取得官方來源',f'{sum(s["present"] for s in status.values())} / {len(status)}')
    c.metric('規劃模組','6 modules')
    d.metric('核心分析角色','3 agents')
    st.write('')
    left,right=st.columns([1.1,1])
    with left:
        st.subheader('你的創業路徑')
        for n,title,desc in [('A1','法規與店務','開店資格、衛生、員工與設備'),('A2','選址情報','人口、業別登記、車站活動'),('A3','經營決策','成本與外送、內用、外帶情境')]:
            with st.container(border=True):st.markdown(f'**{n} · {title}**  \n{desc}')
        st.info('這是情境規劃工具，不是主管機關核發許可，也不保證商業獲利。')
    with right:
        st.subheader('官方資料雷達')
        for key,s in status.items():
            st.markdown(f"{'🟢' if s['present'] else '⚪'} **{s['title']}**  \n<small>{'已下載 · '+nice(s['bytes'])+' bytes' if s['present'] else '未取得，這項統計不會顯示假數字'}</small>",unsafe_allow_html=True)
        st.caption('Windows 雙擊「下載官方資料.cmd」取得資料，或依 README 手動下載。')

elif view.startswith('02'):
    heading('02','法規與現場營運','法規核對清單與員工工作流程，依店型自動切換。')
    st.warning('法規適用性依實際地址、營業態樣、規模而定。全部預設「待核實」，請逐項向主管機關確認。')
    legal=legal_checklist(shop,city)
    left,right=st.columns([1.3,1])
    with left:
        st.subheader('Agent 1 · 開店法遵清單')
        for k,x in enumerate(legal):
            with st.expander(f"{k+1:02d}　{x['item']} · {x['status']}",expanded=k==0):
                st.write(x['action']);st.markdown(f"[官方查詢入口]({x['source']})")
    with right:
        st.subheader('人員與設備 · 每日檢核')
        for i,task in enumerate(operations_plan(shop)):
            st.checkbox(task,key=f'task_{shop}_{i}')
        st.caption('勾選僅為本機操作紀錄，不等於已通過政府查驗。')
    st.download_button('下載法遵清單 JSON',json.dumps(legal,ensure_ascii=False,indent=2),file_name='legal_checklist.json',mime='application/json')

elif view.startswith('03'):
    heading('03','商圈情報與競爭比較','以資料中的真實縣市、人口、登記家數和運量比較，不用虛構熱區排名。')
    pop,e_pop=get_source('population');ind,e_ind=get_source('industry');metro,e_metro=get_source('metro')
    tab1,tab2,tab3=st.tabs(['人口結構','登記店家','桃園捷運運量'])
    with tab1:
        if e_pop:st.info(e_pop)
        else:
            try:
                p=population_summary(pop);p=p[p.city==city]
                if p.empty:st.warning('原始人口資料沒有此城市可辨識的地區欄位。')
                else:
                    st.metric('資料覆蓋村里的人口加總',nice(p.population.sum()))
                    st.caption('僅統計資料已覆蓋的村里，不代表所有可到店顧客。請確認月份、城市名稱與資料完整性。')
                    fig=px.bar(p.sort_values('population',ascending=False).head(20),x='district',y='population',labels={'district':'行政區','population':'人口數'},color_discrete_sequence=['#128078'])
                    fig.update_layout(plot_bgcolor='white',paper_bgcolor='white',height=420);st.plotly_chart(fig,use_container_width=True)
                    st.dataframe(p,use_container_width=True,hide_index=True)
            except Exception as e:st.error(f'人口原始資料格式尚未相容：{e}')
    with tab2:
        if e_ind:st.info(e_ind)
        else:
            try:
                x=industry_summary(ind)
                st.warning('商業登記家數為 2026/02 月份快照；僅涵蓋商業登記且「住宿及餐飲業」是大類，不等於目前手搖飲同業數量。')
                st.dataframe(x.sort_values('restaurants',ascending=False),use_container_width=True,hide_index=True)
                st.caption('住宿及餐飲業是大類，不能當成手搖飲店的直接競爭店家數。')
            except Exception as e:st.error(str(e))
        st.subheader('全國稅籍資料 · 指定城市登記列數')
        st.caption('原始 ZIP 可能很大。這裡只做登記地址包含城市名稱的計數，不把登記數視為實際營業店家。')
        if not status['tax']['present']:st.info('尚未有稅籍原始檔，請下載 BGMOPEN1.zip。')
        elif st.button('讀取稅籍 ZIP 並統計（大量資料可能需要數分鐘）'):
            try:
                n=count_tax_zip_by_city(RAW/SOURCES['tax']['file'],city);st.metric('登記資料列（地區文字比對）',nice(n))
            except Exception as e:st.error(f'稅籍分析尚未完成：{e}')
    with tab3:
        if e_metro:st.info(e_metro)
        else:
            try:
                x=metro_summary(metro)
                if x.empty:st.info('無可比較的車站資料')
                else:
                    st.caption('每站平均日運量是車站資料，不代表街道行人或來店人數。')
                    x=x.head(20);fig=px.bar(x.sort_values('daily_riders'),x='daily_riders',y='station',orientation='h',labels={'daily_riders':'平均日運量','station':'車站'},color_discrete_sequence=['#0c7770']);fig.update_layout(height=570,plot_bgcolor='white');st.plotly_chart(fig,use_container_width=True)
            except Exception as e:st.error(f'捷運資料欄位尚未相容：{e}')

elif view.startswith('04'):
    heading('04','外送通路與消費模式','沒有公開區域訂單數就不會硬預測；以用戶假設研究策略差異。')
    st.subheader('外送服務範圍 · 官方與平台網站查核')
    st.markdown('**平台公開查詢**： [foodpanda 服務範圍](https://pandarider.foodpanda.com.tw/deliveryRange) · [Uber Eats 台灣說明](https://www.uber.com/tw/zh-tw/blog/delivery-partner-area-and-time/)')
    st.warning('此專案尚未連線至平台即時地理覆蓋 API，因此不會將「某區可外送」顯示為已驗證。請輸入地址於平台自行確認。')
    st.write('')
    st.subheader('通路比例與平台費率（假設值）')
    s=st.session_state.sim
    c1,c2,c3=st.columns(3)
    dine=c1.slider('內用占比',0,100,round(s['dinein_share']*100),5,key='dine_slider')
    delivery=c2.slider('外送占比',0,100,round(s['delivery_share']*100),5,key='delivery_slider')
    if dine+delivery>100:
        st.error('內用＋外送占比超過 100%，請調整。');st.stop()
    s['dinein_share']=dine/100;s['delivery_share']=delivery/100
    commission=c3.slider('平台抽成情境',0,50,round(s['commission']*100),1,key='commission_slider');s['commission']=commission/100
    s['delivery_packaging']=st.number_input('每筆外送額外包裝成本',min_value=0,max_value=200,value=s['delivery_packaging'])
    shares={'通路':['內用','外帶','外送'],'比例':[dine,100-dine-delivery,delivery]}
    fig=px.pie(shares,names='通路',values='比例',hole=.65,color_discrete_sequence=['#0b7771','#b6d0c9','#e59b70']);fig.update_layout(height=340,margin=dict(l=0,r=0,t=10,b=10));st.plotly_chart(fig,use_container_width=True)
    st.info('以上比例是你自行設定的「情境參數」，不是透過人口資料推估的真實偏好。')

elif view.startswith('05'):
    heading('05','經營決策實驗室','移動一個參數，立即檢視不同通路組合下的財務後果。')
    s=st.session_state.sim
    with st.container(border=True):
        c1,c2,c3=st.columns(3)
        s['price']=c1.number_input('平均客單價 NT$',min_value=1,max_value=5000,value=s['price'],step=5)
        s['variable']=c2.number_input('每筆商品變動成本 NT$',min_value=0,max_value=5000,value=s['variable'],step=5)
        s['daily']=c3.number_input('每日總訂單數（假設）',min_value=0,max_value=100000,value=s['daily'],step=10)
        a,b,c,d=st.columns(4)
        s['rent']=a.number_input('月租',min_value=0,max_value=2000000,value=s['rent'],step=5000)
        s['payroll']=b.number_input('月人事費用',min_value=0,max_value=2000000,value=s['payroll'],step=5000)
        s['fixed_other']=c.number_input('其他月固定費',min_value=0,max_value=2000000,value=s['fixed_other'],step=5000)
        s['days']=d.number_input('每月營業天數',min_value=1,max_value=31,value=s['days'])
    sim=money_sim(**s,initial=budget)
    x1,x2,x3,x4=st.columns(4)
    x1.metric('月預估營收',f"NT$ {nice(sim['revenue'])}")
    x2.metric('月預估成本',f"NT$ {nice(sim['monthly_cost'])}")
    x3.metric('月損益',f"NT$ {nice(sim['monthly_profit'])}")
    x4.metric('每日損益平衡訂單',str(sim['breakeven_daily']) if sim['breakeven_daily'] is not None else '無法達成')
    c1,c2=st.columns([1.1,1])
    with c1:
        fig=go.Figure();fig.add_trace(go.Bar(name='營收',x=['每月'],y=[sim['revenue']],marker_color='#0d8075'));fig.add_trace(go.Bar(name='成本',x=['每月'],y=[sim['monthly_cost']],marker_color='#d99977'));fig.update_layout(barmode='group',height=360,plot_bgcolor='white',paper_bgcolor='white',font=dict(size=13));st.plotly_chart(fig,use_container_width=True)
    with c2:
        results=[]
        for scale in [0.6,0.8,1,1.2,1.4]:
            settings={**s,'daily':int(s['daily']*scale)};z=money_sim(**settings,initial=budget)
            results.append({'訂單情境':f'{scale:.0%}','每日訂單':settings['daily'],'月損益':z['monthly_profit']})
        st.subheader('訂單量敏感度')
        st.dataframe(pd.DataFrame(results),hide_index=True,use_container_width=True)
        st.caption('這是 ±40% 的自訂情境，不是 AI 預測。')
    st.info(sim['notes'])

elif view.startswith('06'):
    heading('06','成果報告與三角色驗證','每一個數字都可回溯來源；不足的部分如實標記。')
    sim=money_sim(**st.session_state.sim,initial=budget)
    legal=legal_checklist(shop,city)
    stats={k:('已取得原始檔（尚須欄位驗證）' if v['present'] else '尚未取得') for k,v in status.items()}
    config={'shop':shop,'city':city,'finance':{**st.session_state.sim,'initial':budget}}
    report=build_report(config,sim,stats,legal)
    t1,t2=st.tabs(['創業報告','可追溯資料來源'])
    with t1:
        st.markdown(report)
        st.download_button('下載 Markdown 報告',report,file_name='OpenShop_business_plan.md',mime='text/markdown',type='primary')
        st.download_button('下載財務 JSON',json.dumps(sim,ensure_ascii=False,indent=2),file_name='OpenShop_finance.json',mime='application/json')
    with t2:
        table=pd.DataFrame([{'資料':v['title'],'狀態':'已下載' if v['present'] else '待下載','官方資料集':f'https://data.gov.tw/dataset/{v["dataset"]}','本機位置':v['file']} for v in status.values()]);st.dataframe(table,use_container_width=True,hide_index=True)
        st.markdown('**稽核原則**：只有財務算式可自動核對；法規合法性須人工／主管機關核實，外送服務和顧客偏好尚無直接可驗證輸入。')
        st.code('python -m scripts.download_official\npython -m pytest -q\npython -m scripts.run_pipeline',language='bash')
