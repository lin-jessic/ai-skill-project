# OpenShop LIFE Studio v4

OpenShop LIFE v4 把 v2 的資料可靠性與三角色審查，和 v3 的 PWA 互動工作台整合在同一個可獨立啟動的專案。

## 快速啟動

Windows 使用者：

1. 進入 `ai-skill-project-v4/`。
2. 第一次執行 `CHECK_V4.cmd`。它會檢查專案檔案、PWA 資源並執行 pytest。
3. 執行 `START_V4.cmd`，瀏覽器開啟 <http://127.0.0.1:8502/>。

命令列方式：

```powershell
python -m pip install -r requirements_pwa.txt
python preflight_v4.py
python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502
```

## 網站操作方法

### A. 直接開啟網頁（離線展示）

適合快速查看版面、測試導覽與示範資料分析，不需要安裝 Python 套件。

1. 開啟 `web/index.html`。
2. 點選「建立我的店鋪」，填入店型、縣市、行政區、坪數與預算。
3. 進入「資料挑戰」，按「下載示範資料」或上傳自己的 `.csv`／`.json`。
4. 按「執行三角色完整分析」，瀏覽器會直接解析檔案並產生離線示範排行、法規提醒與審查摘要。
5. 透過底部導覽查看「商圈 PK」、「法規通關」、「每日營運」、「老闆財務」與「報告」。

離線模式的結果會標示為「離線示範」；它不會執行 Python 後端，也不代表官方法規核准或正式市場預測。

### B. 啟動完整分析服務（推薦）

完整模式會使用 FastAPI 與 Python 分析引擎，適合教授 Demo、CSV 品質檢查、三角色輸出與報告匯出。

Windows 可直接雙擊：

```text
START_V4.cmd
```

或使用命令列：

```powershell
cd "C:\Users\你的帳號\Downloads\week 11\ai-skill-project-v4"
python -m pip install -r requirements_pwa.txt
python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502
```

接著用瀏覽器開啟 <http://127.0.0.1:8502/>。在完整模式中，按「執行三角色完整分析」會將檔案送至本機服務，依序產生 Agent 1、Agent 2、Agent 3／審查結果。

### C. 上傳檔案格式

CSV 或 JSON 至少要能對應以下欄位：

| 用途 | 英文欄名 | 可接受的中文別名 |
|---|---|---|
| 地點 | `district` | 行政區、商圈、候選地點 |
| 人口 | `population` | 人口、人口數 |
| 競品 | `competitors` | 同業數、競爭店家數 |
| 人流 | `footfall` | 人流指標、交通量、旅運量 |
| 租金 | `rent` | 租金、月租金 |

數值欄不可有缺值或負數；檔案上限為 20 MB。範例檔案為 `examples/DEMO_商圈資料_情境假設_非官方.csv`，屬於合成教學資料，不是政府統計。

### D. 常見問題

- **顯示「無法連接本機分析伺服器」**：目前頁面是完整模式但後端尚未啟動。請執行 `START_V4.cmd`，或重新直接開啟 `web/index.html` 使用離線模式。
- **示範資料變成 `file:///C:/api/sample`**：請按 `Ctrl + F5` 強制重新整理；目前直接開檔會改用專案內的範例 CSV。
- **按鈕沒有反應**：確認已重新整理到最新版頁面；若仍無反應，請關閉舊分頁後重新開啟 `web/index.html`，不要開啟舊的快取頁面。
- **完整模式無法啟動**：先執行 `python -m pip install -r requirements_pwa.txt`，再確認 8502 埠沒有被其他程式占用。
- **法規結果不是核准證明**：網站只整理檢核路徑；土地使用、消防、建管、食品、稅務與勞動事項仍須向所在地主管機關確認。

## 三角色輸出

1. Agent 1：`01_market_report.json`，包含資料品質、候選地點相對排行、營收假設與開放問題。
2. Agent 2：`02_legal_checklist.json`，包含法規來源、風險、證照與主管機關確認事項。
3. Agent 3：`03_store_opening_plan.md`，包含流程、文件、天數、預算覆蓋與高風險對應。
4. 稽核：`04_audit.json`，包含預算檢查、法規對應、財務公式與 `actual_skill_auto_trigger_tested` 狀態。

## 官方資料下載

v4 採用 v2 的全自動下載器。它會從政府資料平台資源頁解析實際檔案連結，並記錄來源、期間、檔案大小、SHA-256 與錯誤。下載成功不代表欄位已完成整合，也不代表資料適合直接合併。

```powershell
python -m scripts.download_official --check
python -m scripts.download_official --only tax
python -m scripts.download_official --all-months
```

結果寫入 `data/raw/`，紀錄寫入 `data/official_download_manifest.json`。遇到政府網站拒絕、來源格式變更或沒有可解析連結時，程式會記錄失敗，不產生佔位資料。

## 教授檔案 Demo

範例檔 `examples/DEMO_商圈資料_情境假設_非官方.csv` 是合成教學資料，只用於驗證欄位與流程，不是政府統計。執行：

```powershell
python -m scripts.run_studio --input examples/DEMO_商圈資料_情境假設_非官方.csv --shop 手搖飲店 --city 桃園市 --output outputs/studio_cli
```

可用欄位與防呆規則見 `docs/上傳檔案欄位格式.md`。未知欄位、缺值、負數、錯誤編碼與超過 20 MB 的檔案會被拒絕，不會補造數字。

## v2 / v3 到 v4 的整合

詳細差異見 `docs/V4_整合說明.md`。v4 保留 v2 的官方自動下載與來源追溯，保留 v3 的 PWA、FastAPI、20 種店型、逐日模擬與測試，並新增獨立啟動入口與 preflight 檢查。

## 重要限制

- 商圈分數是依使用者輸入資料與權重的相對指標，不是實際成功率。
- 財務與每日經營數字是標記為模擬的假設，不是市場預測。
- 登記家數不等於實際營業家數；人口、人流與捷運運量也不等於來客數。
- 土地使用、建管、消防、食品、環保、稅務與勞動規則必須由所在地主管機關依地址、規模與業態確認。
- 網站流程不等於 AI Skill 自動觸發；A/B/C 啟動證據須在真正支援 Skill 的工具中另行留存。
