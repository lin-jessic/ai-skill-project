---
name: openshop-ai
version: "2.0"
description: 當使用者要求在台灣規劃開店、比較商圈、檢查餐飲法規、安排員工SOP或做開店預算模擬時啟動；三角色協作且附可驗證資料。
---
# OpenShop AI：台灣創業三角色協作 Skill

## 何時啟動
- 明確：幫我在桃園開手搖飲店，核對法規、選址和營收。
- 同義：我有八十萬想在中壢做咖啡廳，怎麼評估商圈、員工與財務？
- 不啟動：請解釋微積分；幫我寫一首詩。
- 不應只有「店」單字就觸發：如「這家書店推薦什麼書」。

## 輸入
`shop`、`city`、`candidate_areas`、`finance`（售價、租金、員工、預期訂單、費率等）。未提供時標記為假設或請求補充；不得把預設當成市場觀察。

## Agent 1：法遵與現場營運研究員
讀取 `agents/legal_operations.md`。依店型產出 `01_legal.json`、`01_operations.json`；逐項列官方查證入口。法律狀態預設「待核實」，禁止宣稱執照取得或確定合法。

## Agent 2：商圈／資料研究員
讀取 `agents/market_location.md`。僅使用 `data/raw` 實際存在、通過欄位核對的官方資料；產出 `02_market.json`。若缺資料，寫明「資料不足」，不得補出人口、外送訂單、商家或顧客偏好。

## Agent 3：財務策略與公式審查員
讀取 `agents/business_finance.md`。使用 Agent 1／2 產物與使用者參數；輸出 `03_finance.json`、`03_business_report.md` 和 `04_audit.json`。獨立比對收益公式，檢查來源與假設標籤。

## 固定交接流程
使用者條件 → A1 合規／SOP → A2 實證商圈資料 → A3 財務與驗算 → 報告。由 `python -m scripts.run_pipeline` 提供可重複 Python 執行結果。**Python CLI 能啟動流程，不等於 AI 環境的自動 Skill 觸發已驗證。**

## 資料原則
來源網址、下載日期、檔案雜湊和資料期間要記錄。2024–2026 分年比較須有一致口徑；稅籍登記不等於開門營業、捷運運量不等於來店人數；不能把外送平台涵蓋宣稱成實測訂單量。具體來源在 `references/data_sources.md`。

## 可重現操作
1. `python -m pip install -r requirements.txt`
2. `python -m scripts.download_official` 下載；官方連線失敗時於資料頁手動取得。
3. `python -m pytest -q` 驗證計算。
4. `python -m scripts.run_pipeline --config config_example.json` 產生可追溯結果。
5. `python -m streamlit run app.py` 展示使用者介面。

## A/B/C 觸發測試
A：「請啟動 OpenShop Skill，幫我在桃園開一間咖啡廳。」預期啟動。
B：「我想經營早餐店，幫我把法規、選址和獲利一起規劃。」預期啟動。
C：「幫我計算二元一次方程式。」預期不啟動。
需在真正支援 Skill 的執行環境留下自動載入證據，不得將命令列執行充作自動觸發證據。
