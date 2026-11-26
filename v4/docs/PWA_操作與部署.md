# OpenShop LIFE PWA — 安裝、啟動與驗收

## 1. Windows VS Code 啟動

在 `v2/` 資料夾雙擊 `launch_pwa.cmd`；亦可使用 CMD：

```cmd
python -m pip install -r requirements_pwa.txt
python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502
```

用電腦瀏覽器前往 `http://127.0.0.1:8502/`。原本 `app.py` 是 Streamlit 舊版；新 PWA 專用入口為 `app_pwa.py`，前端為 `web/index.html`。

**不要直接雙擊 `web/index.html`**，因為網頁需要 Python API。`launch_pwa.cmd` 只含 ASCII，避免 Windows 中文指令碼編碼問題。

## 2. Windows/Android/iPhone 安裝 PWA

- 電腦版 Chrome 或 Edge：本機 `localhost` 或 `127.0.0.1` 是受信任的安全內容環境，瀏覽器符合安裝條件時可使用安裝 App 按鈕。
- Android：在 **HTTPS** 站點用 Chrome 的「安裝應用程式」或「加到主畫面」。
- iPhone：使用 Safari 開啟 **HTTPS** 站點，點分享選單 →「加入主畫面」。iOS 不一定會觸發 `beforeinstallprompt`，屬瀏覽器行為。
- 僅在電腦上以 `127.0.0.1` 啟動，手機無法直接連到電腦的 loopback；從手機測試需要把 FastAPI 部署至**有 HTTPS 網域**的主機，並檢查連線、CORS/反向代理、檔案與隱私安全。不能只把前端放 GitHub Pages，因為分析需要 Python 後端。

可使用 `Dockerfile.pwa` 部署到支援 Docker 的 HTTPS 託管服務（不是已經部署完成）。

## 3. 前端 PWA 檔案

```
v2/
├── app_pwa.py                  FastAPI 本機 API
├── launch_pwa.cmd              Windows 一鍵啟動
├── requirements_pwa.txt        後端套件
├── Dockerfile.pwa              可選擇的容器部署
├── web/
│   ├── index.html              HTML + iOS meta + manifest
│   ├── styles.css              手機底部導覽與安全留白
│   ├── app.js                  六大模組事件與 API
│   ├── manifest.webmanifest
│   ├── sw.js                   只快取網站殼層
│   └── icons/
│       ├── icon-192.png
│       └── icon-512.png
└── tests/test_pwa.py
```

## 4. 教授 Demo（檔案輸入、三角色、遊戲）

1. 開始頁 →「建立我的店鋪」，選擇店型／地區／預算，按儲存。
2. 「資料挑戰」→ 下載 `openshop_SAMPLE_ASSUMPTIONS.csv`（只用於課堂操作測試，不是官方資料），或使用教授提供且具備必要欄位的 CSV/JSON。
3. 上傳並按「執行三角色完整分析」，畫面顯示資料筆數、SHA-256 與審查狀態。
4. 「商圈 PK」用滑桿改權重，觀察五個候選地點排序變化。注意評分只是相對情境分數。
5. 「法規通關」展示每項法遵工作及人工確認標記，官方查核連結不得當成核准證明。
6. 「店面與通路」調整內用、外帶、外送；「老闆財務」重新試算。
7. 「每日營運」選擇社群廣告、增加人力等決策，結算數日並下載 *SIMULATION* CSV。
8. 「報告」下載三個 Agent 成果與審查 JSON。AI Skill 自動觸發 A/B/C 需另在 AI 工具中實際測試錄影。

## 5. 重要驗證限制

- `sw.js` 僅快取**首頁 HTML／CSS／JS／icon／manifest**，不快取上傳資料、API、財務紀錄。離線時可打開已快取的介面，但不能執行分析。
- 避免禁止頁面縮放：`viewport` 保留 `user-scalable=yes`，支援需要放大文字的使用者；同時設定 `viewport-fit=cover` 與 `safe-area-inset`。
- 手機 PWA 安裝條件受瀏覽器版本及 HTTPS 部署狀態影響；安裝按鈕未出現不代表程式壞掉。
- 模擬數據不能冒充政府真實資料；來源資料由上傳者提供，網站不會自動認證原始檔內容。
- 新版仍沿用既有 `scripts/studio_engine.py` 與 `SKILL.md` 三角色規則。網站流程執行 != 模型自動載入 Skill。

## 6. 測試

```cmd
python -m pytest -q
python -m uvicorn app_pwa:app --host 127.0.0.1 --port 8502
```

桌面版和手機版最終視覺與 PWA 安裝需要在使用者的 Windows、Android、iOS 真機驗收。
