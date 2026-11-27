# OpenShop AI V5｜智慧開店可行性評估 Skill

以原始 skill.zip 的五角色規格為基礎，依 GitHub V4 的程式介面及資料規則重作獨立命令列工具。無須網站、FastAPI 或 API Key；Python 3.10+。本版不變更舊版本。原始規格逐字保存於 docs/SKILL_original.md；部署版 SKILL.md 新增實際 CLI 指引。

## 快速開始（Windows CMD）

解壓後以 VS Code **直接開啟 v5 資料夾**（不要把整個歷史 Repo 當 Demo 工作區）。在 CMD 中執行：

```cmd
python -m pip install -r requirements.txt
CHECK_V5.cmd
```

純計算、CSV、JSON、Markdown 與 unittest 不依賴第三方套件；matplotlib 為圖表選用依賴。沒有套件仍可執行主流程。不要使用舊版網站的指令。

## Codex 操作

1. 開啟 v5 工作區後，確認 Codex 的 Skills 清單可辨識 store-opening-advisor（可用平台的 Skills UI 或 `/skills`，依版本而異）。若未辨識，確認工作目錄與 `.agents/skills/store-opening-advisor/SKILL.md` 是否存在，重新開啟工作區。只部署一份同用途 Skill。
2. 依 CODEX_DEMO_PROMPT.txt 的 A/B/C 分別建立全新對話。不可先把 SKILL.md 貼給 Codex 或指定 Skill 名稱作為自動啟動測試。
3. A/B 使用同一份合成範例資料，清楚告知非官方。Codex 應依 Skill 在每個階段開始前才讀取當階段角色指令，再建立實際 config JSON、init、分階段執行 1–5，讀取上游輸出並解讀工具結果。AI 實際查核、說明與決策另記 `agent_notes_01.md` 至 `agent_notes_05.md`，完成 Stage 5 後再由 AI 產出 `07_ai_business_advice.md`；Python 工具產出不能冒充 AI 啟動證據。
4. 測試 C 不應執行開店工具。記錄平台載入或未載入證據，不能只看模型自述。

## 不使用 AI 的 Python 回歸示範

```cmd
python .agents/skills/store-opening-advisor/scripts/run.py all --config sample-data/config_demo.json --input sample-data/market_demo.csv --source-type synthetic
```

終端會列出獨立 run 路徑。`all` 僅驗證計算流程。真正 Skill 操作應由 Codex 依角色依序執行 `init`、`stage --number 1` 至 `5`。執行過的 run 不覆蓋；更改設定時建立新 run。`outputs/demo_reference` 是此次 Python 實測成果，並非 Codex Demo。

## 官方資料

```cmd
python .agents/skills/store-opening-advisor/scripts/download_official.py --check
python .agents/skills/store-opening-advisor/scripts/download_official.py --only population --list
```

取得授權後，依實際資源 URL 與期間下載（見 SKILL.md）。五類來源延續 V4；新版保守地要求多個資源時明確選擇，不猜最新月份。下載後核對格式、期間、城市、地理粒度與單位，再製作 ETL 映射。大型 ZIP 需先自行取樣／按地區篩選，不自動將全國原始資料轉成精確商圈資料。範例：

```cmd
python .agents/skills/store-opening-advisor/scripts/prepare_data.py --mapping sample-data/etl_mapping_demo.json --output outputs/etl_new.csv
```

範例 ETL 使用合成資料，並非政府下載成果。網路下載與官方資料欄位對應須本機確認。

## 主要功能及限制

- 20 種既有店型的教學參數，未知店型使用明示假設；可傳入實際價格、人事、租金、預算、營業日及成本。
- 人事可傳入全職／兼職人數、薪資、工時與雇主負擔；明確 `payroll` 會保留，缺漏時使用標示過的混合教學估算與敏感度，不假定全員全職。
- 四項獨立商圈權重（100%）、min-max、敏感度與分數貢獻；不以排名代表成功率。
- 月度財務、三情境、現金流、損益兩平、預備金與每日營運模擬。
- 法規清單只是待查證事項，不是法律結論。法源日期、實際文件與時間不明時留空；AI 可依官方來源進一步查核並記錄。尚未實作完整法規即時擷取或任意業態的詳細設備資料庫。
- 五階段工具 JSON、SHA-256 交接、獨立重算、跨角色一致性檢查與預算阻擋。發現錯誤由 AI 建立新 run 修正，並記錄前後差異，最多兩輪；工具不自動猜測正確輸入，也不自動產生 agent notes。
- Python `run.py all` 只作整合回歸測試；正式 AI 工作流程使用 `init` 加五次 `stage`，並由 AI 寫 notes 與一般中文的 `07_ai_business_advice.md`。
- 若 Agent 5 在 Stage 5 後才完成第五份 notes，使用 `python .agents/skills/store-opening-advisor/scripts/run.py validate-notes --run <run>` 重新驗證五份紀錄；此命令不產生 notes。
- Markdown 報告、CSV、PNG 圖表；PDF/DOCX 為依環境另行轉換的選用格式。圖表英文軸標避免未安裝中文字型造成缺字。
- `docs/python_test_log.txt` 是實際 Python 測試結果（目前 15 項）；`docs/test-report.md` 記錄本機回歸與 A/B/C 證據狀態。沒有預製 A/B/C 成功證據。
