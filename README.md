# Three-Agent Skill｜台灣道路事故資料分析

以臺灣政府開放資料為基礎的 **三角色 AI Skill** 課堂專案。將事故資料蒐整、歷史分布分析與品質審查串成可重現流程，並以 **SafeRoad Studio v3** 互動式 Dashboard 展示結果。

> 目前保存的第一個可展示版本位於 [`v1/`](v1/)。本專案分析**歷史來源資料紀錄**，不是即時路況、事故機率預測或救護派遣系統。

## 已完成

- **資料**：取得並處理 2024、2025 年官方 A1／A2 年度檔，及 2026 年 A1／A2 已公布資料；年份涵蓋不代表 2026 全年完整。
- **三角色**：資料檢查員 → 分析員 → 品質審查員；保留正規化、統計、稽核結果。
- **Dashboard v3**：全局總覽、事故地圖、時間解碼、道路探索、地區比較、方法與驗證；支援條件篩選與 CSV 匯出。
- **已保存的執行成果**：合併來源 **2,254,292 筆資料列**，有效地圖座標 **2,246,830 筆**，排除無效座標 **7,462 筆**；`03_audit.json` 為 `PASS`。這些是來源資料列數，不等於獨立事故件數；數據來自此版執行結果，重新下載或篩選後可能不同。

## Windows / VS Code 快速操作

1. Clone 儲存庫後，開啟根目錄，雙擊 **`SafeRoad_操作選單.cmd`**。
2. 選 **1**：啟動 `v1/app_v3.py`，查看**已存在的** `v1/outputs/` 分析結果。
3. 如果資料不存在，先依 [`v1/README.md`](v1/README.md) 將**官方真實資料**放進 `v1/data/raw/`，選 **2** 重新執行全部資料分析，再選 **1**。
4. 選 **3** 可執行 Python 單元測試；選 **4** 安裝依賴。

手動啟動（在根目錄的 CMD）：

```cmd
cd v1
python -m pip install -r requirements.txt
python scripts\run_all.py
python -m streamlit run app_v3.py
```

**資料與結果說明：** `data/raw/` 與 `outputs/` 可能因檔案較大而未上傳 GitHub。沒有真實來源資料就不會產出正式事故分析。使用步驟、資料來源及限制請見 [`v1/README.md`](v1/README.md)。

## 技術與限制

Python、pandas、Streamlit、Plotly、Folium、pytest；`SKILL.md` 與 `agents/` 定義三個角色的分工。Dashboard 是成果檢視介面，**不等同於 AI Skill 自動啟動的證明**。正式 A／B／C 觸發測試與課堂影片仍須另外實錄。

資料來源：[政府資料開放平臺 A1](https://data.gov.tw/dataset/57023) · [A2](https://data.gov.tw/dataset/57024) · [2024 年度](https://data.gov.tw/dataset/172969) · [2025 年度](https://data.gov.tw/dataset/177136)。
