# SafeRoad Studio v3｜新版 Dashboard

## 特色
- 以政府真實事故資料為唯一資料來源；沒有 `outputs/` 時拒絕顯示虛構數據。
- 全局總覽、事故空間分布、時間解碼、道路文字探索、地區比較、方法與驗證，共六個分析空間。
- 淡色編輯式視覺系統、收斂的色彩、精簡視覺階層、互動圖表與可下載篩選資料。
- 2024–2026 年皆可選擇，**前提**是 `outputs/01_normalized.csv` 真正包含這些年份。
- Agent 1/2/3 分工仍沿用原本的資料流程與審查記錄。

## 使用方式（Windows CMD）

1. 把 ZIP 解壓縮到新資料夾，或將 `app_v3.py`、`啟動新版Dashboard.cmd` 複製到原本的 `1118_ch` 根目錄。
2. **如果複製新版程式到舊專案，不要刪掉舊專案 `data/raw`、`outputs`**。原始官方檔可能很大，因此不會包含在此 ZIP。
3. 確保舊專案已執行 `python scripts\run_all.py`，並在 `outputs/` 產生報表。
4. 在 VS Code CMD 執行：`python -m streamlit run app_v3.py`，或雙擊 `啟動新版Dashboard.cmd`。
5. 若缺套件：`python -m pip install -r requirements.txt`。

## 資料誠實聲明
- 此版本**沒有**即時事故 API、送醫個案紀錄、全台任意路線安全導航、事故發生機率預測。
- 熱點及縣市排名是「來源資料列」統計，可能有同案多當事者。不要用來宣稱真實事故件數。
- 2026 若只有部分月份，不能與 2024、2025 全年直接比較年度增減。
- 本版本的外觀不再追求花俏 AI 風格，而是偏向資料新聞與研究儀表板。

## 記錄與影片
此 Dashboard 是 **AI Skill 的成果檢視介面**，不是 AI Skill 本身；教授要求的 A／B／C 啟動測試仍需在 Codex／支援 Skill 的平台錄影。三角色從本地 Python 程式依序執行，不能冒稱三個平行自主 Agent。
