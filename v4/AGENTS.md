# OpenShop LIFE Agent Guide v4

v4 是 v2 的資料與流程嚴謹度，加上 v3 的 PWA 與互動體驗的整合版。

## 固定三角色順序

1. Agent 1 市場分析：資料品質、來源、候選地點排行與初估損益，輸出 `01_market_report.json`。
2. Agent 2 法規合規：依 Agent 1 的業態與地點定位，列出法源、證照與主管機關確認事項，輸出 `02_legal_checklist.json`。
3. Agent 3 程序及審查：產出流程、預算與風險稽核，輸出 `03_store_opening_plan.md` 與 `04_audit.json`。

## v4 的整合原則

- `web/` 是 v3 的 PWA 展示層；Python API 仍是本機分析引擎，不宣稱等同 AI Skill 自動觸發。
- `scripts/download_official.py` 採 v2 的官方資源頁解析與 SHA-256 manifest；下載失敗會記錄，不建立假資料。
- `scripts/studio_engine.py` 採 v3 的上傳檔案防護、相對排行、可重現模擬與四份審查輸出。
- 官方資料下載、資料清理、商圈整合、AI Skill A/B/C 觸發測試是四個不同驗證步驟。
- `examples/` 只包含明確標註的合成教學資料，不能冒充政府統計。

## 風險界線

市場分數是依輸入資料與權重計算的相對指標；財務和每日經營數字是模擬；土地使用、消防、建管、食品、稅務及勞動事項仍須由所在地主管機關按個案確認。
