'use strict';
const $=id=>document.getElementById(id);
const money=n=>'NT$ '+Math.round(Number(n)||0).toLocaleString('zh-TW');
const text=(el,txt)=>{if(el)el.textContent=String(txt??'');};
const mk=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=String(txt);return e;};
const state={catalog:[],decisions:{},links:{},config:{},file:null,analysis:null,history:[],choice:'一般營業',weights:[.40,.35,.25],legalChecks:{},opsChecks:{}};
let toastTimer;
function toast(message){const box=$('toast');text(box,message);box.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>box.classList.remove('show'),3600);}
async function api(path,opt={}){let r;try{r=await fetch(path,{cache:'no-store',...opt});}catch(e){throw Error('無法連接本機分析伺服器。離線時可開啟介面，但資料分析需恢復連線。');}
 let j=await r.json().catch(()=>({}));if(!r.ok){let d=j.detail;throw Error(typeof d==='string'?d:JSON.stringify(d||'服務出錯'));}return j;}
function send(path,obj){return api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});}
function show(name){const view=$('view-'+name);if(!view)return;
 document.querySelectorAll('.view').forEach(e=>e.classList.toggle('active',e===view));
 document.querySelectorAll('[data-nav]').forEach(e=>{if(e.closest('.bottom-nav'))e.classList.toggle('nav-active',e.dataset.nav===name);});
 if(name==='legal')renderLegal();if(name==='locations')renderRanking();if(name==='report')renderReport();if(name==='finance')updateFinance();
 window.scrollTo({top:0,behavior:'instant'});history.replaceState(null,'','#'+name);
}
function initNavigation(){document.addEventListener('click',e=>{let btn=e.target.closest('[data-nav]');if(btn)show(btn.dataset.nav);});let key=location.hash.slice(1);if($('view-'+key))show(key);}
function currentConfig(){const c=structuredClone(state.config);const field={shop:'shopInput',city:'cityInput',district:'districtInput',floor_area_sqm:'areaInput',budget:'budgetInput',opening_target_date:'dateInput',price:'priceInput',variable:'variableInput',daily:'dailyInput',rent:'rentInput',payroll:'payrollInput',fixed_other:'otherInput',days:'daysInput',delivery_packaging:'packInput'};
 for(const [k,id] of Object.entries(field)){const e=$(id);if(e&&e.value!==''){c[k]=e.type==='number'?Number(e.value):e.value;}}
 c.floor_area_sqm=Number($('areaInput').value)*3.305785;
 c.dinein_share=Number($('dineInput').value)/100;c.delivery_share=Number($('deliveryInput').value)/100;c.commission=Number($('commInput').value)/100;
 return c;}
function refreshShopPreview(){text($('previewShopTitle'),$('shopInput').value);text($('previewShopPlace'),$('cityInput').value+' · '+$('districtInput').value);text($('previewBudget'),money($('budgetInput').value));let shop=state.catalog.find(x=>x.name===$('shopInput').value);text($('previewShopIcon'),shop?.icon||'🏪');}
function fillShops(reset=true){const category=$('categoryInput').value;const select=$('shopInput');const previous=select.value;select.replaceChildren();state.catalog.filter(s=>s.category===category).forEach(s=>{const op=mk('option','',s.icon+' '+s.name);op.value=s.name;select.appendChild(op);});if(!reset&&[...select.options].some(x=>x.value===previous))select.value=previous;else if(!reset&&[...select.options].some(x=>x.value===state.config.shop))select.value=state.config.shop;
 syncShopDefaults();}
function syncShopDefaults(){const shop=state.catalog.find(x=>x.name===$('shopInput').value);if(!shop)return;
 [['priceInput',shop.price],['variableInput',shop.variable],['dailyInput',shop.daily]].forEach(([id,val])=>{$(id).value=val;});refreshShopPreview();}
function localCsvRows(raw){
 const lines=String(raw).replace(/^\uFEFF/,'').trim().split(/\r?\n/).filter(Boolean);
 if(lines.length<2)throw Error('CSV 至少需要標題列與一筆資料');
 const split=line=>line.split(',').map(v=>v.trim().replace(/^"|"$/g,''));
 const headers=split(lines[0]);
 return lines.slice(1).map(line=>{const values=split(line);return Object.fromEntries(headers.map((h,i)=>[h,values[i]??'']));});
}
function localNum(row,names){const key=Object.keys(row).find(k=>names.includes(k.toLowerCase())||names.includes(k));const value=key?Number(String(row[key]).replace(/,/g,'')):NaN;return Number.isFinite(value)?value:0;}
async function localAnalyze(file){
 const raw=await file.text();let rows;
 if(file.name.toLowerCase().endsWith('.json')){const parsed=JSON.parse(raw);rows=Array.isArray(parsed)?parsed:(parsed.records||parsed.data||[]);}
 else rows=localCsvRows(raw);
 if(!rows.length)throw Error('檔案沒有可分析的資料列');
 const ranked=rows.map(r=>({district:String(r.district||r['行政區']||r['商圈']||r['候選地點']||'未命名地點'),population:localNum(r,['population','人口','人口數']),competitors:localNum(r,['competitors','同業數','競爭店家數']),footfall:localNum(r,['footfall','人流指標','交通量','旅運量']),rent:localNum(r,['rent','租金','月租金'])}));
 const norm=(field,reverse=false)=>{const vals=ranked.map(r=>r[field]),lo=Math.min(...vals),hi=Math.max(...vals);return r=>{const n=hi===lo?.5:(r[field]-lo)/(hi-lo);return reverse?1-n:n;};};
 const np=norm('population'),nf=norm('footfall'),nc=norm('competitors',true),nr=norm('rent',true);
 ranked.forEach(r=>r.score=100*(np(r)*.4+nf(r)*.35+(nc(r)*.6+nr(r)*.4)*.25));ranked.sort((a,b)=>b.score-a.score);
 const budget=Number($('budgetInput').value)||0,price=Number($('priceInput').value)||0,daily=Number($('dailyInput').value)||0,days=Number($('daysInput').value)||26;
 const revenue=price*daily*days,monthlyCost=(Number($('rentInput').value)||0)+(Number($('payrollInput').value)||0)+(Number($('otherInput').value)||0),profit=revenue-monthlyCost;
 const quality={filename:file.name,rows:ranked.length,sha256:'file-mode-local-preview',warnings:['直接開檔模式由瀏覽器解析，完整驗證請啟動 START_V4.cmd']};
 const legal={agent:'02_legal_advisor',status:'partial',needs_authority_confirmation:true,items:[{item:'土地使用與建築用途',risk:'high',action_required:'向所在地都發／建管機關確認用途與裝修條件',source:'https://www.gov.tw/'},{item:'商業登記與稅籍',risk:'medium',action_required:'依組織型態辦理商業或公司設立及稅籍登記',source:'https://onestop.nat.gov.tw/'},{item:'食品業者登錄（如適用）',risk:'high',action_required:'餐飲業向食藥署／所在地衛生局確認登錄要求',source:'https://www.fda.gov.tw/'}]};
 const audit={status:budget>=150000?'pass_with_conditions':'blocked',market_rows:ranked.length,legal_items:legal.items.length,budget_coverage_check:budget>=150000,needs_authority_confirmation:true,actual_skill_auto_trigger_tested:false,issues:['離線預覽未執行 Python 後端法規與資料品質驗證']};
 return {market:{agent:'01_market_analyst',status:'complete',ranked_areas:ranked,score_is_relative_heuristic:true},legal,plan:'# 03｜開店流程與跨角色審查\n\n離線預覽：請啟動 START_V4.cmd 取得完整申辦排程。',audit,finance:{revenue,monthly_cost:monthlyCost,monthly_profit:profit,breakeven_daily:null},ranked,quality,source_status:'瀏覽器離線解析，尚未獨立證明為官方資料',notes:['離線預覽僅供介面展示','正式結果請以 Python 分析服務為準']};
}
function setupShop(){text($('previewBudget'),money(state.config.budget));$('categoryInput').value=state.catalog.find(s=>s.name===state.config.shop)?.category||'餐飲';fillShops(false);
 for(const [key,id] of Object.entries({city:'cityInput',district:'districtInput',budget:'budgetInput',opening_target_date:'dateInput',price:'priceInput',variable:'variableInput',daily:'dailyInput',rent:'rentInput',payroll:'payrollInput',fixed_other:'otherInput',days:'daysInput',delivery_packaging:'packInput'})){$(id).value=state.config[key];}
 $('areaInput').value=Math.round(state.config.floor_area_sqm/3.305785);
 $('dineInput').value=Math.round(state.config.dinein_share*100);$('deliveryInput').value=Math.round(state.config.delivery_share*100);$('commInput').value=Math.round(state.config.commission*100);
 $('categoryInput').addEventListener('change',()=>{fillShops();refreshShopPreview();});$('shopInput').addEventListener('change',()=>{syncShopDefaults();state.analysis=null;});
 for(const id of ['cityInput','districtInput','budgetInput'])$(id).addEventListener('input',refreshShopPreview);
 $('saveShop').addEventListener('click',()=>{try{state.config=currentConfig();state.analysis=null;state.history=[];toast('店鋪設定已更新；舊的分析結果已清除，請重新上傳資料驗證。');}catch(e){toast(e.message);}});
 refreshShopPreview();}
function setAgentStatuses(msg){['agent1Status','agent2Status','agent3Status'].forEach(id=>text($(id),msg));}
function setupUpload(){const f=$('fileInput');f.addEventListener('change',()=>{state.file=f.files[0]||null;text($('fileMeta'),state.file?`${state.file.name} · ${(state.file.size/1024).toFixed(1)} KB`:'尚未選擇檔案');$('runBtn').disabled=!state.file;});
 const drop=$('dropZone');['dragenter','dragover'].forEach(name=>drop.addEventListener(name,e=>{e.preventDefault();drop.classList.add('drag');}));['dragleave','drop'].forEach(name=>drop.addEventListener(name,e=>{e.preventDefault();drop.classList.remove('drag');}));
 drop.addEventListener('drop',e=>{const file=e.dataTransfer.files[0];if(!file)return;state.file=file;f.value='';text($('fileMeta'),file.name+' · '+(file.size/1024).toFixed(1)+' KB');$('runBtn').disabled=false;});
 $('runBtn').addEventListener('click',async()=>{if(!state.file)return;const btn=$('runBtn');btn.disabled=true;text(btn,'正在分析…');setAgentStatuses('分析中');
 try{state.config=currentConfig();
 if(window.location.protocol==='file:') state.analysis=await localAnalyze(state.file);
 else {const form=new FormData();form.append('file',state.file,state.file.name);form.append('config',JSON.stringify(state.config));state.analysis=await api('/api/analyze',{method:'POST',body:form});}
 setAgentStatuses('完成');renderUploadResult();toast(window.location.protocol==='file:'?'離線示範分析完成；正式驗證請啟動 START_V4.cmd。':'三角色分析已完成。可查看排行與審查結果。');
 }catch(e){setAgentStatuses('待重試');toast('檔案分析失敗：'+e.message);}finally{btn.disabled=false;text(btn,'▶ 執行三角色完整分析');}});}
function renderUploadResult(){const a=state.analysis;if(!a)return;$('uploadResult').hidden=false;text($('auditStatus'),a.audit.status);const rows=[['有效候選地點',a.quality.rows],['資料檔案',a.quality.filename],['文件 SHA-256',a.quality.sha256.slice(0,16)+'…'],['法規事項',a.legal.items.length]];
 const box=$('uploadStats');box.replaceChildren();rows.forEach(([key,value])=>{const item=mk('div','stat-tile');item.append(mk('span','',key),mk('strong','',value));box.appendChild(item);});}
function renderRanking(){const container=$('locationChart');container.replaceChildren();if(!state.analysis){container.append(mk('p','empty','請先匯入商圈資料，再執行三角色審查。'));return;}
 const pop=+$('weightPop').value,foot=+$('weightFoot').value;
 if(pop+foot>100){container.append(mk('p','empty','人口與交通權重總和不可超過100%。'));return;}
 const rows=state.analysis.ranked;if(!rows.length){container.append(mk('p','empty','沒有可排名的地區。'));return;}
 // Recalculate from raw attributes when available. Engine default ranked stores all relevant fields.
 const norm=(field,val,reverse)=>{let a=rows.map(r=>Number(r[field]||0));const lo=Math.min(...a),hi=Math.max(...a);let v=hi===lo?.5:(val-lo)/(hi-lo);return reverse?1-v:v;};
 const ranked=rows.map(r=>({...r,score:100*(norm('population',r.population)*pop/100+norm('footfall',r.footfall)*foot/100+(norm('competitors',r.competitors,true)*.6+norm('rent',r.rent,true)*.4)*(100-pop-foot)/100)})).sort((a,b)=>b.score-a.score);
 ranked.forEach((r,i)=>{const row=mk('div','ranking-row');row.append(mk('span','rank-rank',i===0?'🥇':String(i+1)),mk('strong','',r.district));const track=mk('div','rank-track'),bar=mk('div','rank-bar');bar.style.width=Math.max(0,Math.min(100,r.score))+'%';track.append(bar);row.append(track,mk('b','',r.score.toFixed(1)));container.append(row);});}
function setupWeights(){const update=()=>{let a=+$('weightPop').value,b=+$('weightFoot').value;if(a+b>100){const changed=document.activeElement.id;if(changed==='weightPop'){$('weightFoot').value=100-a;b=100-a;}else{$('weightPop').value=100-b;a=100-b;}}text($('weightPopLabel'),a+'%');text($('weightFootLabel'),b+'%');text($('weightRestLabel'),(100-a-b)+'%');renderRanking();};['weightPop','weightFoot'].forEach(id=>$(id).addEventListener('input',update));}
function renderLegal(){const legal=state.analysis?.legal;let list=legal?.items||[];const box=$('legalList');box.replaceChildren();if(!list.length){box.append(mk('p','empty','請先完成資料挑戰，才會顯示對應店型的法規檢核。'));}
 let done=0;list.forEach((it,i)=>{const key='l'+i,task=mk('label','task'),check=mk('input');check.type='checkbox';check.checked=!!state.legalChecks[key];if(check.checked)done++;check.addEventListener('change',()=>{state.legalChecks[key]=check.checked;renderLegal();});
 const desc=mk('div');desc.append(mk('strong','',it.item),mk('p','',it.action_required||it.action));if(/^https:\/\//.test(it.source||'')){const a=mk('a','', '↗ 查看官方入口（需核對適用版本）');a.href=it.source;a.target='_blank';a.rel='noopener noreferrer';desc.appendChild(a);}const risk=mk('span','risk',it.risk==='high'?'高風險':'待確認');task.append(check,desc,risk);box.appendChild(task);});
 $('legalProgress').style.width=(list.length?100*done/list.length:0)+'%';text($('legalCount'),`已自行檢查 ${done}/${list.length} 項，並非官方核准`);
 const ops=$('opsList');ops.replaceChildren();let tasks=['確認商品或設備進貨來源','確認現場清潔與交班紀錄','建立員工工時、保險及薪資檢核'];if(state.config.shop&&['手搖飲店','咖啡廳','早餐店','甜點店','便當店','拉麵店','火鍋店','麵包店','冰品店'].includes(state.config.shop))tasks.push('檢查食材保存、冷鏈與交叉污染防治');
 tasks.forEach((t,i)=>{const row=mk('label','task'),cb=mk('input');cb.type='checkbox';cb.checked=!!state.opsChecks[i];cb.addEventListener('change',()=>state.opsChecks[i]=cb.checked);row.append(cb,mk('strong','',t));ops.appendChild(row);});}
function setupChannels(){function update(changed){let a=+$('dineInput').value,b=+$('deliveryInput').value;if(a+b>100){if(changed==='dineInput'){$('deliveryInput').value=100-a;b=100-a;}else{$('dineInput').value=100-b;a=100-b;}}let take=100-a-b;let com=+$('commInput').value;
 text($('dineLabel'),a+'%');text($('deliveryLabel'),b+'%');text($('commLabel'),com+'%');text($('dineLegend'),a+'%');text($('takeLegend'),take+'%');text($('deliveryLegend'),b+'%');$('channelDonut').style.background=`conic-gradient(#9dd3b2 0 ${a}%,#f0ae93 ${a}% ${a+take}%,#b9abe2 ${a+take}% 100%)`;
 state.config.dinein_share=a/100;state.config.delivery_share=b/100;state.config.commission=com/100;}
 ['dineInput','deliveryInput','commInput'].forEach(id=>$(id).addEventListener('input',()=>update(id)));update();}
function setupDecisions(){const box=$('decisionCards');for(const [name,detail] of Object.entries(state.decisions)){const b=mk('button','decision-card');b.type='button';b.dataset.choice=name;b.setAttribute('aria-pressed',name===state.choice?'true':'false');b.append(mk('strong','',name),mk('small','',detail.description));b.addEventListener('click',()=>{state.choice=name;document.querySelectorAll('[data-choice]').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.choice===name)));});box.appendChild(b);}
 $('nextDay').addEventListener('click',async()=>{const btn=$('nextDay');btn.disabled=true;try{state.config=currentConfig();const o=await send('/api/day',{config:state.config,history:state.history.map(({decision})=>({decision})),choice:state.choice,seed:42});state.history=o.history;renderDay();}catch(e){toast(e.message);}finally{btn.disabled=false;}});
 $('resetDays').addEventListener('click',()=>{state.history=[];renderDay();toast('新的一局已開始');});$('exportDays').addEventListener('click',()=>{if(!state.history.length)return toast('目前尚未有每日模擬結果');const headers=['day','decision','event','orders','revenue','profit','cash','is_simulation'];const esc=v=>'"'+String(v??'').replaceAll('"','""')+'"';const csv='\uFEFF'+[headers.join(','),...state.history.map(r=>headers.map(k=>esc(r[k])).join(','))].join('\r\n');download('OpenShop_daily_SIMULATION.csv',csv,'text/csv');});}
function svgCurve(values,color='#8174aa'){if(!values.length)return mk('p','empty','暫無資料');const w=650,h=230,p=33,min=Math.min(...values,0),max=Math.max(...values,0),span=max-min||1;const pts=values.map((v,i)=>[p+(w-2*p)*i/Math.max(1,values.length-1),h-p-(v-min)/span*(h-2*p)]);const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox',`0 0 ${w} ${h}`);svg.setAttribute('role','img');svg.setAttribute('aria-label','數值趨勢圖');
 const line=document.createElementNS('http://www.w3.org/2000/svg','polyline');line.setAttribute('points',pts.map(v=>v.join(',')).join(' '));line.setAttribute('fill','none');line.setAttribute('stroke',color);line.setAttribute('stroke-width','4');line.setAttribute('stroke-linejoin','round');line.setAttribute('stroke-linecap','round');svg.append(line);
 for(let i=0;i<3;i++){const y=p+i*(h-2*p)/2;const g=document.createElementNS('http://www.w3.org/2000/svg','line');for(let [k,v] of Object.entries({x1:p,x2:w-p,y1:y,y2:y,stroke:'#e6dcd5','stroke-dasharray':'4 6'}))g.setAttribute(k,v);svg.insertBefore(g,line);}return svg;}
function renderDay(){let h=state.history,box=$('dayLog');text($('dayNumber'),'DAY '+String(h.length+1).padStart(2,'0'));const last=h.at(-1);text($('dayEvent'),last?last.event:'開店第一天');text($('dayStory'),last?`${last.decision} · ${last.orders} 筆交易 · 今日損益 ${money(last.profit)}`:'今天要做什麼？選一張經營決策卡。');text($('dayCash'),money(last?.cash??state.config.budget));box.replaceChildren();$('cashChart').replaceChildren();if(!h.length){box.append(mk('p','empty','尚無營業紀錄'));$('cashChart').append(mk('p','empty','結算第一天後顯示曲線'));return;} $('cashChart').append(svgCurve(h.map(d=>d.cash)));
 [...h].reverse().slice(0,30).forEach(r=>{const row=mk('div','journal-row');row.append(mk('b','',`Day ${r.day}｜${r.event}`),mk('span','',`${r.decision} · ${r.orders} 單 · 盈虧 ${money(r.profit)} · 現金 ${money(r.cash)}`));box.append(row);});}
async function updateFinance(){try{state.config=currentConfig();const r=await send('/api/preview',{config:state.config});const f=r.finance,box=$('financeTiles');box.replaceChildren();for(const [name,value] of [['每月營業收入',money(f.revenue)],['每月總成本',money(f.monthly_cost)],['每月簡化損益',money(f.monthly_profit)],['每日損益兩平',f.breakeven_daily===null?'無法達成':f.breakeven_daily+' 筆']]){const item=mk('div','stat-tile');item.append(mk('span','',name),mk('strong','',value));box.append(item);}const chart=$('financeChart');chart.replaceChildren();const points=[];for(let d=0;d<=Math.max(30,state.config.daily*2);d+=Math.max(1,Math.round(state.config.daily/8)||5)){const unit=(state.config.price-state.config.variable-state.config.delivery_share*(state.config.price*state.config.commission+state.config.delivery_packaging));points.push(unit*d*state.config.days-state.config.rent-state.config.payroll-state.config.fixed_other);}chart.append(svgCurve(points,'#b2849c'));
 }catch(e){toast('無法計算財務：'+e.message);}}
function download(filename,content,mime){const blob=new Blob([content],{type:mime||'application/octet-stream'});const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(u),800);}
function renderReport(){const a=state.analysis;const ev=$('evidenceInfo'),cards=$('artifactCards');ev.replaceChildren();cards.replaceChildren();if(!a){ev.append(mk('p','empty','尚未完成分析，請先上傳 CSV／JSON。'));return;}
 for(const [k,v] of [['檔案名稱',a.quality.filename],['資料列數',a.quality.rows],['SHA-256',a.quality.sha256],['審查狀態',a.audit.status],['市場排行',a.ranked.length],['來源狀態',a.source_status]]){const item=mk('div','evidence-item');item.append(mk('span','',k),mk('strong','',v));ev.append(item);}
 for(const [name,content] of [['01_market_report.json',a.market],['02_legal_checklist.json',a.legal],['03_store_opening_plan.md',a.plan],['04_audit.json',a.audit],['05_finance.json',a.finance]]){const card=mk('div','artifact-card');card.append(mk('strong','',name),mk('span','',name.startsWith('01')?'Agent 1':name.startsWith('02')?'Agent 2':'Agent 3／審查'));
 const b=mk('button','btn btn-outline','↓ 下載');b.addEventListener('click',()=>download(name,typeof content==='string'?content:JSON.stringify(content,null,2),'text/plain;charset=utf-8'));card.append(b);cards.append(card);}}
function setupStaleGuard(){
 const tracked=new Set(['categoryInput','shopInput','cityInput','districtInput','areaInput','budgetInput','dateInput','priceInput','variableInput','dailyInput','rentInput','payrollInput','otherInput','daysInput','packInput','dineInput','deliveryInput','commInput']);
 document.addEventListener('change',event=>{if(!tracked.has(event.target?.id))return;
  if(state.analysis){state.analysis=null;$('uploadResult').hidden=true;setAgentStatuses('設定已變更');toast('設定已變更，舊的三角色分析失效；請在「資料挑戰」重新執行。');}
  if(state.history.length){state.history=[];renderDay();}
 });
}
function setupInstall(){let prompt=null;window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();prompt=e;$('installBtn').hidden=false;});$('installBtn').addEventListener('click',async()=>{if(prompt){prompt.prompt();await prompt.userChoice;prompt=null;$('installBtn').hidden=true;}else toast('iOS Safari：分享 → 加入主畫面');});if('serviceWorker'in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(e=>console.warn('SW registration unavailable',e)));}}
async function boot(){initNavigation();setupInstall();try{const d=await api('/api/catalog');state.catalog=d.shops;state.decisions=d.decisions;state.links=d.links;state.config=d.defaults;setupShop();setupUpload();setupWeights();setupChannels();setupDecisions();setupStaleGuard();renderDay();$('updateFinance').addEventListener('click',updateFinance);$('exportAll').addEventListener('click',()=>{if(!state.analysis)return toast('請先完成三角色分析');download('OpenShop_agent_results.json',JSON.stringify({...state.analysis,simulated_days:state.history},null,2),'application/json');});updateFinance();}
 catch(e){
  // Keep the visual demo usable when index.html is opened directly from disk.
  // Full analysis still requires START_V4.cmd (the local FastAPI service).
  if(window.location.protocol==='file:'){
   state.catalog=[
    {name:'手搖飲店',category:'餐飲',icon:'🧋',price:65,variable:25,daily:70},
    {name:'咖啡廳',category:'餐飲',icon:'☕',price:110,variable:38,daily:45},
    {name:'早餐店',category:'餐飲',icon:'🥪',price:80,variable:30,daily:80},
    {name:'服飾店',category:'零售',icon:'👕',price:850,variable:360,daily:12},
    {name:'選物店',category:'零售',icon:'🧺',price:680,variable:260,daily:14},
    {name:'美髮沙龍',category:'服務',icon:'✂️',price:1200,variable:180,daily:8}
   ];
   state.decisions={一般營業:{description:'維持日常服務與基本宣傳。'},尖峰促銷:{description:'用折扣換取更多交易筆數。'},品質升級:{description:'提高體驗與單筆消費，但增加成本。'}};
   state.config={shop:'手搖飲店',city:'桃園市',district:'中壢區',floor_area_sqm:66.1,budget:800000,price:65,variable:25,daily:70,rent:38000,payroll:85000,fixed_other:18000,days:26,delivery_share:.2,dinein_share:.3,commission:.3,delivery_packaging:5,opening_target_date:'2027-03-01'};
   setupShop();setupUpload();setupWeights();setupChannels();setupDecisions();setupStaleGuard();renderDay();$('updateFinance').addEventListener('click',()=>toast('直接開檔模式僅提供版面預覽；請用 START_V4.cmd 啟用財務試算。'));$('exportAll').addEventListener('click',()=>toast('請用 START_V4.cmd 完成分析後再匯出。'));$('financeTiles').innerHTML='<p class="empty">請用 START_V4.cmd 啟用本機分析伺服器。</p>';
   toast('已載入離線版面預覽；完整分析請啟動 START_V4.cmd。');
  }else toast(e.message);
 }
}
boot();
